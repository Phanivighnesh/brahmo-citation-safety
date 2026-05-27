"""
test_detector.py
----------------
Tests for the hallucination_detector module.
Covers all 4 rules from SETUP_GUIDE.md § "HALLUCINATION DETECTION RULES".
"""

import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import unittest
from src.types import ExtractedCitation
from src.hallucination_detector import detect_hallucination
from src.types import (
    HALT_FUTURE_YEAR, HALT_IMPOSSIBLE_VOLUME,
    HALT_IMPOSSIBLE_PAGE, HALT_PRE_MODERN,
)


def _scc(raw, year, vol, page):
    return ExtractedCitation(raw, "SCC", year, vol, page, None, 0, len(raw))

def _air(raw, year, page, court="SC"):
    return ExtractedCitation(raw, "AIR", year, None, page, court, 0, len(raw))

def _manu(raw, year, court="SC"):
    return ExtractedCitation(raw, "MANU", year, None, None, court, 0, len(raw))


class TestHallucinationDetector(unittest.TestCase):

    # ── RULE 1: Future year ───────────────────────────────────────────────────
    def test_future_year_flagged(self):
        c = _scc("(2028) 3 SCC 45", 2028, 3, 45)
        r = detect_hallucination(c)
        self.assertTrue(r.is_flagged)
        self.assertEqual(r.reason, HALT_FUTURE_YEAR)

    def test_current_year_ok(self):
        c = _scc("(2026) 3 SCC 45", 2026, 3, 45)
        r = detect_hallucination(c)
        self.assertFalse(r.is_flagged)

    def test_past_year_ok(self):
        c = _scc("(2021) 10 SCC 1", 2021, 10, 1)
        r = detect_hallucination(c)
        self.assertFalse(r.is_flagged)

    # ── RULE 2: Impossible SCC volume ─────────────────────────────────────────
    def test_impossible_volume_flagged(self):
        c = _scc("(2024) 47 SCC 123", 2024, 47, 123)
        r = detect_hallucination(c)
        self.assertTrue(r.is_flagged)
        self.assertEqual(r.reason, HALT_IMPOSSIBLE_VOLUME)

    def test_volume_exactly_25_ok(self):
        c = _scc("(2024) 25 SCC 1", 2024, 25, 1)
        r = detect_hallucination(c)
        self.assertFalse(r.is_flagged)

    def test_volume_26_flagged(self):
        c = _scc("(2024) 26 SCC 1", 2024, 26, 1)
        r = detect_hallucination(c)
        self.assertTrue(r.is_flagged)

    def test_volume_rule_only_for_scc_scr(self):
        # AIR has no volume — volume rule should not fire for AIR
        c = _air("AIR 2024 SC 567", 2024, 567)
        r = detect_hallucination(c)
        self.assertFalse(r.is_flagged)

    # ── RULE 3: Impossible page ───────────────────────────────────────────────
    def test_impossible_page_suspicious_not_flagged(self):
        c = _scc("(2024) 5 SCC 9999", 2024, 5, 9999)
        r = detect_hallucination(c)
        self.assertFalse(r.is_flagged)       # not hard-halted
        self.assertTrue(r.is_suspicious)
        self.assertEqual(r.reason, HALT_IMPOSSIBLE_PAGE)

    def test_page_5000_suspicious(self):
        c = _scc("(2024) 5 SCC 5001", 2024, 5, 5001)
        r = detect_hallucination(c)
        self.assertTrue(r.is_suspicious)

    def test_page_5000_not_suspicious(self):
        c = _scc("(2024) 5 SCC 5000", 2024, 5, 5000)
        r = detect_hallucination(c)
        self.assertFalse(r.is_suspicious)

    # ── RULE 4: Pre-modern date ────────────────────────────────────────────────
    def test_pre_1900_suspicious_not_flagged(self):
        c = _scc("(1856) 3 SCC 45", 1856, 3, 45)
        r = detect_hallucination(c)
        self.assertFalse(r.is_flagged)       # suspicious, not hard-halted
        self.assertTrue(r.is_suspicious)
        self.assertEqual(r.reason, HALT_PRE_MODERN)

    def test_1900_boundary_ok(self):
        c = _scc("(1900) 1 SCC 1", 1900, 1, 1)
        r = detect_hallucination(c)
        self.assertFalse(r.is_suspicious)

    def test_1899_suspicious(self):
        c = _scc("(1899) 1 SCC 1", 1899, 1, 1)
        r = detect_hallucination(c)
        self.assertTrue(r.is_suspicious)

    # ── Rule priority: future year trumps impossible volume ───────────────────
    def test_future_year_takes_priority(self):
        c = _scc("(2030) 47 SCC 9999", 2030, 47, 9999)
        r = detect_hallucination(c)
        self.assertTrue(r.is_flagged)
        self.assertEqual(r.reason, HALT_FUTURE_YEAR)  # first rule wins

    # ── Clean citation ────────────────────────────────────────────────────────
    def test_clean_citation_passes(self):
        c = _scc("(2021) 10 SCC 1", 2021, 10, 1)
        r = detect_hallucination(c)
        self.assertFalse(r.is_flagged)
        self.assertFalse(r.is_suspicious)
        self.assertIsNone(r.reason)

    # ── MANU — no year/volume rules apply ────────────────────────────────────
    def test_manu_no_volume_rule(self):
        c = _manu("MANU/SC/0456/2024", 2024)
        r = detect_hallucination(c)
        self.assertFalse(r.is_flagged)

    def test_manu_future_year_flagged(self):
        c = _manu("MANU/SC/0456/2028", 2028)
        r = detect_hallucination(c)
        self.assertTrue(r.is_flagged)
        self.assertEqual(r.reason, HALT_FUTURE_YEAR)


if __name__ == "__main__":
    unittest.main(verbosity=2)
