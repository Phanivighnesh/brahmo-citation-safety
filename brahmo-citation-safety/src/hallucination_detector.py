"""
hallucination_detector.py
--------------------------
Applies 4 deterministic pre-filter rules to each extracted citation.
Zero AI — pure rule-based logic derived from SETUP_GUIDE.md.

Rules (source: SETUP_GUIDE.md § "HALLUCINATION DETECTION RULES"):
  RULE 1 — FUTURE YEAR:        year > 2026  → ❌ HALLUCINATED
  RULE 2 — IMPOSSIBLE VOLUME:  SCC/SCR vol > 25 → ❌ HALLUCINATED
  RULE 3 — IMPOSSIBLE PAGE:    page > 5000  → ⚠️ SUSPICIOUS (still sent to IK)
  RULE 4 — PRE-MODERN DATE:    year < 1900  → ⚠️ SUSPICIOUS (still sent to IK)
"""

from typing import List
from .types import (
    ExtractedCitation, HallucinationResult,
    HALT_FUTURE_YEAR, HALT_IMPOSSIBLE_VOLUME,
    HALT_IMPOSSIBLE_PAGE, HALT_PRE_MODERN,
)

# Current year ceiling per assessment spec
CURRENT_YEAR = 2026

# SCC/SCR publishes roughly 10-20 volumes per year; >25 is impossible
MAX_SCC_VOLUME = 25

# Page numbers rarely exceed 2000; >5000 is suspicious
MAX_PAGE_SUSPICIOUS = 5000

# Indian law reports start around 1900s
MIN_YEAR = 1900


def detect_hallucination(citation: ExtractedCitation) -> HallucinationResult:
    """
    Apply all 4 pre-filter rules to a single citation.

    Returns HallucinationResult where:
      is_flagged   = True  → REMOVED immediately, skip IK API call
      is_suspicious = True → still sent to IK, but flagged as risky
    """
    year   = citation.year
    volume = citation.volume
    page   = citation.page
    pname  = citation.pattern_name.upper()

    # RULE 1 — Future year → hard halt
    if year is not None and year > CURRENT_YEAR:
        return HallucinationResult(
            citation     = citation,
            is_flagged   = True,
            reason       = HALT_FUTURE_YEAR,
            is_suspicious = False,
        )

    # RULE 2 — Impossible SCC / SCR volume → hard halt
    if pname in ("SCC", "SCR") and volume is not None and volume > MAX_SCC_VOLUME:
        return HallucinationResult(
            citation     = citation,
            is_flagged   = True,
            reason       = HALT_IMPOSSIBLE_VOLUME,
            is_suspicious = False,
        )

    # RULE 3 — Impossible page number → suspicious (verify with IK)
    # SCC OnLine and MANU use document IDs (can be 6000+), not page numbers.
    # Only apply this rule to formats that actually use page numbers.
    PAGE_FORMATS = ("SCC", "SCR", "AIR", "CRI_LJ")
    if pname in PAGE_FORMATS and page is not None and page > MAX_PAGE_SUSPICIOUS:
        return HallucinationResult(
            citation      = citation,
            is_flagged    = False,
            reason        = HALT_IMPOSSIBLE_PAGE,
            is_suspicious = True,
        )

    # RULE 4 — Pre-modern date → suspicious (verify with IK)
    if year is not None and year < MIN_YEAR:
        return HallucinationResult(
            citation      = citation,
            is_flagged    = False,
            reason        = HALT_PRE_MODERN,
            is_suspicious = True,
        )

    # No rules fired — citation looks structurally valid, send to IK
    return HallucinationResult(
        citation      = citation,
        is_flagged    = False,
        reason        = None,
        is_suspicious = False,
    )


def run_prefilter(citations: List[ExtractedCitation]) -> List[HallucinationResult]:
    """Apply detect_hallucination to every citation in a list."""
    return [detect_hallucination(c) for c in citations]


# ── Quick self-test ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
    from src.types import ExtractedCitation

    cases = [
        ExtractedCitation("(2028) 3 SCC 45",  "SCC",  2028, 3,  45, None, 0, 16),  # future
        ExtractedCitation("(2024) 47 SCC 123", "SCC",  2024, 47, 123, None, 0, 18), # impossible vol
        ExtractedCitation("(2024) 5 SCC 9999", "SCC",  2024, 5,  9999, None, 0, 18),# suspicious page
        ExtractedCitation("(1856) 3 SCC 45",   "SCC",  1856, 3,  45, None, 0, 15),  # pre-modern
        ExtractedCitation("(2021) 10 SCC 1",   "SCC",  2021, 10, 1, None, 0, 15),   # clean
    ]

    for c in cases:
        r = detect_hallucination(c)
        flag = "❌ FLAGGED" if r.is_flagged else ("⚠️ SUSPICIOUS" if r.is_suspicious else "✅ OK")
        print(f"  {c.raw_text:<30} → {flag}  reason={r.reason}")
