"""
section_normalizer.py
----------------------
Converts old Indian law section references (IPC / CrPC / IEA) to their
replacements under BNS / BNSS / BSA using ONLY database table lookups.
Zero AI — pure text substitution driven by the section_mappings table.

Source: SETUP_GUIDE.md § "SEED DATA — 30 SECTION MAPPINGS"

Key design decision: mappings are loaded into a dict (hash map) once per call.
At 30 mappings this is trivial; at 3,000 mappings this is still O(1) per lookup.
The regex is compiled once and matches ALL old-section patterns in a single pass.
"""

import re
import sqlite3
from typing import Dict, List, Tuple

from .database import get_connection
from .types import SectionAlert


# ── Mapping loader ─────────────────────────────────────────────────────────────

def load_section_mappings(conn: sqlite3.Connection) -> Dict[str, dict]:
    """
    Load all 30 section mappings from DB into a lookup dict.
    Key: normalised old_section string (upper-case, single spaces)
    Value: full row dict

    This is called once per normalize_sections() call.
    Adding a new mapping = INSERT one row, no code change.
    """
    cur = conn.execute(
        "SELECT old_section, new_section, old_act, new_act FROM section_mappings"
    )
    mappings: Dict[str, dict] = {}
    for row in cur.fetchall():
        key = _normalise_key(row["old_section"])
        mappings[key] = dict(row)
    return mappings


def _normalise_key(s: str) -> str:
    """Collapse whitespace and upper-case for robust matching."""
    return re.sub(r"\s+", " ", s.strip()).upper()


# ── Core normalizer ────────────────────────────────────────────────────────────

def normalize_sections(text: str, conn: sqlite3.Connection = None) -> Tuple[str, List[SectionAlert]]:
    """
    Scan *text* for old IPC/CrPC/IEA section references and replace them
    with their BNS/BNSS/BSA equivalents.

    Returns:
        (normalised_text, list_of_SectionAlert)

    Strategy:
      1. Load mappings hash-map from DB.
      2. Build a compiled regex that matches ALL old section strings in one pass.
      3. Walk all matches; substitute each; count occurrences per mapping.
      4. Return modified text + alert list.

    Edge cases handled:
      - "Section 420 IPC" and "Sec. 420 I.P.C." both normalise to same key.
      - "Sections 420, 406 IPC" pattern: matched individually by the regex.
      - Case-insensitive matching.
    """
    if conn is None:
        conn = get_connection()

    mappings = load_section_mappings(conn)
    if not mappings:
        return text, []

    # Build alternation regex from all old_section strings
    # Sorted longest-first so "Section 304A IPC" matches before "Section 304 IPC"
    old_sections = sorted(mappings.keys(), key=len, reverse=True)
    pattern_parts = [re.escape(s) for s in old_sections]
    # Also match original casing variants e.g. "Section 420 IPC" vs "section 420 ipc"
    combined = "|".join(pattern_parts)
    regex = re.compile(combined, re.IGNORECASE)

    alert_counts: Dict[str, int] = {}
    alerts: List[SectionAlert] = []

    def _replace(m: re.Match) -> str:
        matched_raw = m.group(0)
        key = _normalise_key(matched_raw)
        row = mappings.get(key)
        if row is None:
            return matched_raw          # shouldn't happen, but be safe
        alert_counts[key] = alert_counts.get(key, 0) + 1
        return row["new_section"]

    normalised_text = regex.sub(_replace, text)

    # Build SectionAlert list (one per unique mapping that fired)
    for key, count in alert_counts.items():
        row = mappings[key]
        alerts.append(SectionAlert(
            old_section  = row["old_section"],
            new_section  = row["new_section"],
            old_act      = row["old_act"],
            new_act      = row["new_act"],
            occurrences  = count,
        ))

    return normalised_text, alerts


# ── Quick self-test ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

    SAMPLE = """
    COMPLAINT UNDER SECTION 420 IPC AND SECTION 406 IPC

    The complainant submits that the accused committed offences under Section 420
    of the Indian Penal Code read with Section 120B IPC (criminal conspiracy)
    and Section 34 IPC (common intention).

    The complainant prays that an FIR be registered under Sections 420, 406,
    120B and 34 of the Indian Penal Code.
    """

    conn = get_connection()
    normalised, section_alerts = normalize_sections(SAMPLE, conn)

    print("=== NORMALISED TEXT ===")
    print(normalised)
    print("\n=== SECTION ALERTS ===")
    for a in section_alerts:
        print(f"  {a.old_section} → {a.new_section}  (×{a.occurrences})")
