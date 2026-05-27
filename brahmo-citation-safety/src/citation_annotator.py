"""
citation_annotator.py
----------------------
Injects status badges into AI output and builds the PipelineReport.
IK call count now tracked via ik_attempted flag (not cost_inr).
"""

from typing import List, Dict, Tuple
from .types import (
    ExtractedCitation, HallucinationResult, VerificationResult,
    AnnotatedCitation, PipelineReport, SectionAlert,
    STATUS_VERIFIED, STATUS_CORRECTED, STATUS_UNVERIFIED,
    HALT_FUTURE_YEAR, HALT_IMPOSSIBLE_VOLUME,
)

BADGE = {
    STATUS_VERIFIED:   "✅ VERIFIED",
    STATUS_CORRECTED:  "⚠️ CORRECTED",
    STATUS_UNVERIFIED: "⚠️ UNVERIFIED",
    "REMOVED":         "❌ REMOVED",
}


def annotate(
    original_text: str,
    hallucination_results: List[HallucinationResult],
    verification_results: List[VerificationResult],
    section_alerts: List[SectionAlert],
) -> Tuple[str, PipelineReport]:

    vr_map: Dict[str, VerificationResult] = {vr.citation_text: vr for vr in verification_results}
    hr_by_citation: Dict[str, HallucinationResult] = {hr.citation.raw_text: hr for hr in hallucination_results}

    annotated_list: List[AnnotatedCitation] = []
    splice_ops: List[Tuple[int, int, str, str]] = []

    for vr in verification_results:
        raw    = vr.citation_text
        hr     = hr_by_citation.get(raw)
        status = vr.status
        corrected_text = None

        badge_label = BADGE.get(status, "⚠️ UNVERIFIED")

        if status == STATUS_VERIFIED:
            case_info  = f" [{vr.case_name}]" if vr.case_name else ""
            badge_text = f" {badge_label}{case_info}"
        elif status == STATUS_CORRECTED:
            corrected_text = vr.case_name
            badge_text = f" {badge_label} — corrected to: {corrected_text}"
        elif status == STATUS_UNVERIFIED:
            badge_text = f" {badge_label} — not found in Indian Kanoon, may be real"
        else:
            reason = ""
            if hr and hr.reason == HALT_FUTURE_YEAR:
                reason = "future year — cannot exist"
            elif hr and hr.reason == HALT_IMPOSSIBLE_VOLUME:
                reason = "impossible SCC volume — hallucinated"
            else:
                reason = "not found in Indian Kanoon"
            badge_text = f" {badge_label} — {reason}"

        if hr:
            start, end = hr.citation.start_pos, hr.citation.end_pos
        else:
            idx   = original_text.find(raw)
            start = idx if idx != -1 else -1
            end   = start + len(raw) if start != -1 else -1

        if start != -1:
            splice_ops.append((start, end, raw, badge_text))

        annotated_list.append(AnnotatedCitation(
            original_text  = raw,
            corrected_text = corrected_text,
            status         = status,
            pattern_name   = hr.citation.pattern_name if hr else "unknown",
            halt_reason    = hr.reason if hr else None,
            ik_doc_id      = vr.ik_doc_id,
            case_name      = vr.case_name,
            from_cache     = vr.from_cache,
            ik_attempted   = vr.ik_attempted,
            cost_inr       = vr.cost_inr,
        ))

    # Splice badges backwards to preserve offsets
    splice_ops.sort(key=lambda x: x[0], reverse=True)
    annotated_text = original_text
    for start, end, raw, badge in splice_ops:
        if end > start and annotated_text[start:end] == raw:
            annotated_text = annotated_text[:end] + badge + annotated_text[end:]
        else:
            pos = annotated_text.find(raw)
            if pos != -1:
                annotated_text = annotated_text[:pos + len(raw)] + badge + annotated_text[pos + len(raw):]

    # ── Build report ───────────────────────────────────────────────────────────
    counts = {"VERIFIED": 0, "CORRECTED": 0, "UNVERIFIED": 0, "REMOVED": 0}
    total_cost   = 0.0
    ik_calls     = 0          # count actual API attempts, not cost
    prefilter_caught = 0

    for ac in annotated_list:
        counts[ac.status] = counts.get(ac.status, 0) + 1
        total_cost += ac.cost_inr
        if ac.ik_attempted:           # ← fixed: use flag, not cost
            ik_calls += 1
        if ac.halt_reason in (HALT_FUTURE_YEAR, HALT_IMPOSSIBLE_VOLUME):
            prefilter_caught += 1

    total    = len(annotated_list)
    good     = counts["VERIFIED"] + counts["CORRECTED"]
    accuracy = round(good / total * 100, 1) if total > 0 else 0.0

    report = PipelineReport(
        total            = total,
        verified         = counts["VERIFIED"],
        corrected        = counts["CORRECTED"],
        unverified       = counts["UNVERIFIED"],
        removed          = counts["REMOVED"],
        prefilter_caught = prefilter_caught,
        ik_calls         = ik_calls,
        total_cost_inr   = round(total_cost, 2),
        accuracy_pct     = accuracy,
        section_alerts   = section_alerts,
        annotated        = annotated_list,
    )
    return annotated_text, report


def render_report(report: PipelineReport, title: str = "CITATION VERIFICATION REPORT") -> str:
    lines = [
        "",
        f"{'─' * 60}",
        f"  📋 {title}",
        f"{'─' * 60}",
        f"  Total citations found : {report.total}",
        f"  ✅ Verified           : {report.verified}",
        f"  ⚠️  Corrected          : {report.corrected}",
        f"  ⚠️  Unverified         : {report.unverified}",
        f"  ❌ Removed            : {report.removed}",
        f"  🛡️  Pre-filter caught  : {report.prefilter_caught} (no IK call needed)",
        f"  🌐 IK API calls       : {report.ik_calls}",
        f"  💰 IK API cost        : ₹{report.total_cost_inr:.2f}",
        f"  🎯 Accuracy           : {report.accuracy_pct}%",
    ]
    if report.section_alerts:
        lines.append(f"{'─' * 60}")
        lines.append("  ⚠️  SECTION ALERTS (old law → new law):")
        for a in report.section_alerts:
            lines.append(f"    {a.old_section} → {a.new_section}  ({a.old_act} → {a.new_act}, ×{a.occurrences})")
    lines += [f"{'─' * 60}", ""]
    return "\n".join(lines)
