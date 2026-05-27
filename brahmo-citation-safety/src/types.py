"""
types.py — Shared dataclasses for the BRAHMO Citation Safety pipeline.
"""

from dataclasses import dataclass, field
from typing import Optional, List

STATUS_VERIFIED   = "VERIFIED"
STATUS_CORRECTED  = "CORRECTED"
STATUS_UNVERIFIED = "UNVERIFIED"
STATUS_REMOVED    = "REMOVED"

HALT_FUTURE_YEAR       = "FUTURE_YEAR"
HALT_IMPOSSIBLE_VOLUME = "IMPOSSIBLE_VOLUME"
HALT_IMPOSSIBLE_PAGE   = "IMPOSSIBLE_PAGE"
HALT_PRE_MODERN        = "PRE_MODERN_DATE"


@dataclass
class ExtractedCitation:
    raw_text:     str
    pattern_name: str
    year:         Optional[int]
    volume:       Optional[int]
    page:         Optional[int]
    court_code:   Optional[str]
    start_pos:    int
    end_pos:      int


@dataclass
class HallucinationResult:
    citation:     ExtractedCitation
    is_flagged:   bool
    reason:       Optional[str]
    is_suspicious: bool


@dataclass
class VerificationResult:
    citation_text: str
    status:        str
    ik_doc_id:     Optional[int]
    case_name:     Optional[str]
    from_cache:    bool
    ik_attempted:  bool    # True = a real IK API call was made (not mock, not cached)
    cost_inr:      float


@dataclass
class SectionAlert:
    old_section:  str
    new_section:  str
    old_act:      str
    new_act:      str
    occurrences:  int


@dataclass
class AnnotatedCitation:
    original_text:   str
    corrected_text:  Optional[str]
    status:          str
    pattern_name:    str
    halt_reason:     Optional[str]
    ik_doc_id:       Optional[int]
    case_name:       Optional[str]
    from_cache:      bool
    ik_attempted:    bool
    cost_inr:        float


@dataclass
class PipelineReport:
    total:            int
    verified:         int
    corrected:        int
    unverified:       int
    removed:          int
    prefilter_caught: int
    ik_calls:         int
    total_cost_inr:   float
    accuracy_pct:     float
    section_alerts:   List[SectionAlert] = field(default_factory=list)
    annotated:        List[AnnotatedCitation] = field(default_factory=list)
