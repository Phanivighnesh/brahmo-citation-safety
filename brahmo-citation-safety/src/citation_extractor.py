"""
citation_extractor.py
----------------------
Extracts Indian legal citations from text using ONLY regex patterns.
Patterns are loaded from the citation_patterns table (database-driven).
Zero AI — 100% deterministic.

Source: SETUP_GUIDE.md § "SEED DATA — 6 CITATION REGEX PATTERNS"
"""

import re
import sqlite3
from typing import List, Dict
from .database import get_connection
from .types import ExtractedCitation


# ── Pattern loader ─────────────────────────────────────────────────────────────

def load_patterns(conn: sqlite3.Connection) -> List[Dict]:
    """
    Load all 6 citation patterns from the DB.
    Returns list of dicts: {pattern_name, regex, example, jurisdiction}
    Adding a new format = INSERT one row.  No code change required.
    """
    cur = conn.execute(
        "SELECT pattern_name, regex, format_template, example, jurisdiction "
        "FROM citation_patterns ORDER BY id"
    )
    return [dict(r) for r in cur.fetchall()]


# ── Core extractor ─────────────────────────────────────────────────────────────

def extract_citations(text: str, conn: sqlite3.Connection = None) -> List[ExtractedCitation]:
    """
    Scan *text* for all Indian legal citations using all 6 patterns.

    Strategy:
      1. Load patterns from DB (cached per-connection in practice).
      2. For each pattern, run re.finditer over the full text.
      3. Parse year / volume / page / court from named/positional groups.
      4. Deduplicate by (raw_text, start_pos) — a citation can only match once
         even if multiple patterns overlap (shouldn't happen, but be safe).

    Returns list of ExtractedCitation, ordered by position in text.
    """
    if conn is None:
        conn = get_connection()

    patterns = load_patterns(conn)
    results: List[ExtractedCitation] = []
    seen_spans: set = set()

    for pat in patterns:
        name  = pat["pattern_name"]
        regex = pat["regex"]

        compiled = re.compile(regex, re.IGNORECASE)

        for m in compiled.finditer(text):
            span = (m.start(), m.end())
            if span in seen_spans:
                continue
            seen_spans.add(span)

            citation = _parse_match(m, name, text)
            results.append(citation)

    # Sort by position in source text
    results.sort(key=lambda c: c.start_pos)
    return results


def _parse_match(m: re.Match, pattern_name: str, text: str) -> ExtractedCitation:
    """
    Extract year / volume / page / court_code from a regex match.
    Each pattern has a different group layout — handled by pattern_name.

    Group layouts (from SETUP_GUIDE seed data):
      SCC:        group(1)=year  group(2)=volume  group(3)=page
      SCC_OnLine: group(1)=year  group(2)=court   group(3)=num
      AIR:        group(1)=year  group(2)=court   group(3)=page
      Cri_LJ:     group(1)=year  group(2)=page
      SCR:        group(1)=year  group(2)=volume  group(3)=page
      MANU:       group(1)=court  (year & num embedded in full string)
    """
    raw = m.group(0)
    groups = m.groups()

    year       = None
    volume     = None
    page       = None
    court_code = None

    pn = pattern_name.upper()

    if pn == "SCC":
        year   = _to_int(groups[0])
        volume = _to_int(groups[1])
        page   = _to_int(groups[2])

    elif pn == "SCC_ONLINE":
        year       = _to_int(groups[0])
        court_code = groups[1]
        page       = _to_int(groups[2])     # "num" in format template

    elif pn == "AIR":
        year       = _to_int(groups[0])
        court_code = groups[1]
        page       = _to_int(groups[2])

    elif pn == "CRI_LJ":
        year = _to_int(groups[0])
        page = _to_int(groups[1])

    elif pn == "SCR":
        year   = _to_int(groups[0])
        volume = _to_int(groups[1])
        page   = _to_int(groups[2])

    elif pn == "MANU":
        court_code = groups[0]
        # Parse year from MANU/SC/NNNN/YYYY format (last segment)
        parts = raw.split("/")
        if len(parts) == 4:
            year = _to_int(parts[3])

    return ExtractedCitation(
        raw_text     = raw,
        pattern_name = pattern_name,
        year         = year,
        volume       = volume,
        page         = page,
        court_code   = court_code,
        start_pos    = m.start(),
        end_pos      = m.end(),
    )


def _to_int(s) -> int | None:
    try:
        return int(s)
    except (TypeError, ValueError):
        return None


# ── Quick self-test ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

    SAMPLE = """
    In Siddharth v. State of UP (2021) 10 SCC 1, the Court laid down guidelines.
    In Arnesh Kumar v. State of Bihar (2014) 8 SCC 273, the Court issued guidelines.
    The Delhi High Court in 2024 SCC OnLine Del 3456 granted bail.
    AIR 2024 SC 567 is also relevant.
    See also 2023 Cri LJ 456 and (2022) 3 SCR 100.
    MANU/SC/0456/2024 confirms the position.
    """

    conn = get_connection()
    found = extract_citations(SAMPLE, conn)
    print(f"Found {len(found)} citations:")
    for c in found:
        print(f"  [{c.pattern_name}] '{c.raw_text}' year={c.year} vol={c.volume} page={c.page}")
