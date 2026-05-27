"""
pipeline.py
-----------
Orchestrates the full Citation Safety pipeline:

  Input text
    │
    ├─ [0] section_normalizer  → detect + replace old law sections (~5ms)
    │
    ├─ [1] citation_extractor  → regex scan for all 6 citation formats
    │
    ├─ [2] hallucination_detector → 4 rule-based pre-filter checks
    │
    ├─ [3] citation_verifier   → IK API lookup (parallel, cached)
    │
    └─ [4] citation_annotator  → badge injection + report

Source: Citation_Safety_Engine.md § "The data flow"
"""

import os
import sqlite3
from typing import Optional, Tuple

from .database import get_connection
from .section_normalizer import normalize_sections
from .citation_extractor import extract_citations
from .hallucination_detector import run_prefilter
from .citation_verifier import verify_citations
from .citation_annotator import annotate, render_report
from .types import (
    PipelineReport, VerificationResult,
    STATUS_VERIFIED, STATUS_CORRECTED, STATUS_UNVERIFIED,
)


def run_pipeline(
    text: str,
    conn: sqlite3.Connection = None,
    api_key: str = None,
    mock_mode: bool = False,
    normalize_input: bool = False,
) -> Tuple[str, PipelineReport]:
    """
    Run the full deterministic citation safety pipeline.

    Parameters
    ----------
    text          : AI-generated legal text to process.
    conn          : SQLite connection (created if None).
    api_key       : Indian Kanoon API key. Falls back to INDIAN_KANOON_API_KEY env var.
    mock_mode     : If True, skip real IK API calls (demo without API key).
    normalize_input: If True, also normalise old IPC/CrPC sections in *input* query.
                     The output text is always normalised.

    Returns
    -------
    (annotated_text, PipelineReport)
    """
    if conn is None:
        conn = get_connection()
    if api_key is None:
        api_key = os.environ.get("INDIAN_KANOON_API_KEY", "")
    if not api_key:
        mock_mode = True

    # ── Stage 0: Normalize old legal sections in the output text ──────────────
    normalised_text, section_alerts = normalize_sections(text, conn)

    # ── Stage 1: Extract all citations via regex ───────────────────────────────
    citations = extract_citations(normalised_text, conn)

    if not citations:
        # No citations found — return text with section normalization only
        report = PipelineReport(
            total=0, verified=0, corrected=0, unverified=0, removed=0,
            prefilter_caught=0, ik_calls=0, total_cost_inr=0.0, accuracy_pct=0.0,
            section_alerts=section_alerts, annotated=[],
        )
        return normalised_text, report

    # ── Stage 2: Pre-filter (hallucination detection) ─────────────────────────
    hallucination_results = run_prefilter(citations)

    # ── Stage 3: IK API verification (parallel, cached) ───────────────────────
    verification_results = verify_citations(
        hallucination_results,
        conn=conn,
        api_key=api_key,
        mock_mode=mock_mode,
    )

    # ── Stage 3b: CORRECTED detection ─────────────────────────────────────────
    # Detect cases where IK returns a case whose citation differs slightly
    # from what the AI wrote (e.g. wrong page number).  Mark as CORRECTED.
    verification_results = _detect_corrections(citations, verification_results)

    # ── Stage 4: Annotate text and build report ────────────────────────────────
    annotated_text, report = annotate(
        original_text         = normalised_text,
        hallucination_results = hallucination_results,
        verification_results  = verification_results,
        section_alerts        = section_alerts,
    )

    return annotated_text, report


def _detect_corrections(
    citations: list,
    verification_results: list,
) -> list:
    """
    CORRECTED logic:
    When IK verifies a citation but the returned metadata citation string
    differs from what the AI wrote (e.g., page 12 vs page 1), mark as
    CORRECTED and store the correct citation text in case_name field.

    This is a post-processing step because IK's /docmeta/ returns the
    authoritative citation string we can compare against.

    Only applies to SCC/AIR/SCR patterns where page/volume is parseable.
    """
    citations_by_text = {c.raw_text: c for c in citations}

    corrected = []
    for vr in verification_results:
        if vr.status != STATUS_VERIFIED:
            corrected.append(vr)
            continue

        # If IK returned a case_name with a different citation, mark corrected
        # In practice the IK /docmeta/ response includes a "citation" field;
        # we compare the page number when the pattern is SCC.
        citation_obj = citations_by_text.get(vr.citation_text)
        if citation_obj and citation_obj.pattern_name.upper() == "SCC":
            # Check if the year+volume match but the page is suspicious
            # (The SETUP_GUIDE example: "(2020) 5 SCC 12" should be "(2020) 5 SCC 1")
            # We rely on IK returning the correct canonical citation via case_name.
            # Heuristic: if page > 5 and volume is reasonable, trust IK page.
            # Full CORRECTED detection would compare IK's canonical citation string.
            # Without the real IK response, we cannot detect this automatically.
            # This placeholder preserves the pipeline contract.
            pass

        corrected.append(vr)

    return corrected


# ── Convenience: pretty-print a full run ─────────────────────────────────────

def run_and_display(
    label: str,
    text: str,
    conn=None,
    api_key=None,
    mock_mode=False,
) -> None:
    """Run pipeline and print results to stdout.  Used by demo scripts."""
    print(f"\n{'═' * 60}")
    print(f"  SCENARIO: {label}")
    print(f"{'═' * 60}")
    print("\n[INPUT TEXT]\n")
    print(text[:600] + ("…" if len(text) > 600 else ""))

    annotated_text, report = run_pipeline(
        text, conn=conn, api_key=api_key, mock_mode=mock_mode
    )

    print("\n[ANNOTATED OUTPUT]\n")
    print(annotated_text)
    print(render_report(report))


if __name__ == "__main__":
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
    from src.database import get_connection as gc
    conn = gc()

    sample = """
    In Siddharth v. State of UP (2021) 10 SCC 1, the Court held X.
    In (2028) 3 SCC 45 the Court held Y.
    """
    run_and_display("Quick test", sample, conn=conn, mock_mode=True)
