"""
test_normalizer.py
------------------
Tests for the section_normalizer module.
Verifies all 30 IPC→BNS / CrPC→BNSS / IEA→BSA mappings.
"""

import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import unittest
from src.database import get_connection
from src.section_normalizer import normalize_sections


class TestSectionNormalizer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # get_connection() auto-bootstraps if DB doesn't exist yet.
        # Do NOT call reset_database() here — on Windows the DB file may still
        # be locked by the extractor test's open connection, causing WinError 32.
        cls.conn = get_connection()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def _normalize(self, text):
        result, alerts = normalize_sections(text, self.conn)
        return result, alerts

    # ── IPC → BNS (21 mappings) ───────────────────────────────────────────────
    def test_302_ipc_to_bns(self):
        result, alerts = self._normalize("Section 302 IPC (murder)")
        self.assertIn("Section 101 BNS", result)
        self.assertEqual(len(alerts), 1)

    def test_304_ipc_to_bns(self):
        result, _ = self._normalize("Section 304 IPC")
        self.assertIn("Section 105 BNS", result)

    def test_304a_ipc_to_bns(self):
        result, _ = self._normalize("Section 304A IPC")
        self.assertIn("Section 106 BNS", result)

    def test_304b_ipc_to_bns(self):
        result, _ = self._normalize("Section 304B IPC")
        self.assertIn("Section 80 BNS", result)

    def test_306_ipc_to_bns(self):
        result, _ = self._normalize("Section 306 IPC")
        self.assertIn("Section 108 BNS", result)

    def test_307_ipc_to_bns(self):
        result, _ = self._normalize("Section 307 IPC")
        self.assertIn("Section 109 BNS", result)

    def test_323_ipc_to_bns(self):
        result, _ = self._normalize("Section 323 IPC")
        self.assertIn("Section 115 BNS", result)

    def test_326_ipc_to_bns(self):
        result, _ = self._normalize("Section 326 IPC")
        self.assertIn("Section 119 BNS", result)

    def test_354_ipc_to_bns(self):
        result, _ = self._normalize("Section 354 IPC")
        self.assertIn("Section 74 BNS", result)

    def test_376_ipc_to_bns(self):
        result, _ = self._normalize("Section 376 IPC")
        self.assertIn("Section 63 BNS", result)

    def test_379_ipc_to_bns(self):
        result, _ = self._normalize("Section 379 IPC")
        self.assertIn("Section 303 BNS", result)

    def test_384_ipc_to_bns(self):
        result, _ = self._normalize("Section 384 IPC")
        self.assertIn("Section 308 BNS", result)

    def test_392_ipc_to_bns(self):
        result, _ = self._normalize("Section 392 IPC")
        self.assertIn("Section 309 BNS", result)

    def test_406_ipc_to_bns(self):
        result, _ = self._normalize("Section 406 IPC")
        self.assertIn("Section 316 BNS", result)

    def test_420_ipc_to_bns(self):
        result, _ = self._normalize("Section 420 IPC")
        self.assertIn("Section 318 BNS", result)

    def test_467_ipc_to_bns(self):
        result, _ = self._normalize("Section 467 IPC")
        self.assertIn("Section 336 BNS", result)

    def test_498a_ipc_to_bns(self):
        result, _ = self._normalize("Section 498A IPC")
        self.assertIn("Section 85 BNS", result)

    def test_499_ipc_to_bns(self):
        result, _ = self._normalize("Section 499 IPC")
        self.assertIn("Section 356 BNS", result)

    def test_506_ipc_to_bns(self):
        result, _ = self._normalize("Section 506 IPC")
        self.assertIn("Section 351 BNS", result)

    def test_34_ipc_to_bns(self):
        result, _ = self._normalize("Section 34 IPC")
        self.assertIn("Section 3(5) BNS", result)

    def test_120b_ipc_to_bns(self):
        result, _ = self._normalize("Section 120B IPC")
        self.assertIn("Section 61 BNS", result)

    # ── CrPC → BNSS (8 mappings) ──────────────────────────────────────────────
    def test_125_crpc_to_bnss(self):
        result, _ = self._normalize("Section 125 CrPC")
        self.assertIn("Section 144 BNSS", result)

    def test_154_crpc_to_bnss(self):
        result, _ = self._normalize("Section 154 CrPC")
        self.assertIn("Section 173 BNSS", result)

    def test_156_3_crpc_to_bnss(self):
        result, _ = self._normalize("Section 156(3) CrPC")
        self.assertIn("Section 175(3) BNSS", result)

    def test_167_crpc_to_bnss(self):
        result, _ = self._normalize("Section 167 CrPC")
        self.assertIn("Section 187 BNSS", result)

    def test_437_crpc_to_bnss(self):
        result, _ = self._normalize("Section 437 CrPC")
        self.assertIn("Section 480 BNSS", result)

    def test_438_crpc_to_bnss(self):
        result, _ = self._normalize("Section 438 CrPC")
        self.assertIn("Section 482 BNSS", result)

    def test_439_crpc_to_bnss(self):
        result, _ = self._normalize("Section 439 CrPC")
        self.assertIn("Section 483 BNSS", result)

    def test_482_crpc_to_bnss(self):
        result, _ = self._normalize("Section 482 CrPC")
        self.assertIn("Section 528 BNSS", result)

    # ── IEA → BSA (1 mapping) ─────────────────────────────────────────────────
    def test_65b_iea_to_bsa(self):
        result, _ = self._normalize("Section 65B IEA")
        self.assertIn("Section 63 BSA", result)

    # ── Scenario 2 full test ───────────────────────────────────────────────────
    def test_scenario_2_all_4_converted(self):
        text = (
            "Section 420 IPC and Section 406 IPC, "
            "read with Section 120B IPC and Section 34 IPC"
        )
        result, alerts = self._normalize(text)
        self.assertIn("Section 318 BNS", result)
        self.assertIn("Section 316 BNS", result)
        self.assertIn("Section 61 BNS", result)
        self.assertIn("Section 3(5) BNS", result)
        self.assertEqual(len(alerts), 4)

    # ── Edge cases ────────────────────────────────────────────────────────────
    def test_case_insensitive(self):
        result, alerts = self._normalize("section 420 ipc")
        self.assertIn("Section 318 BNS", result)
        self.assertEqual(len(alerts), 1)

    def test_multiple_occurrences_counted(self):
        text = "Section 420 IPC and again Section 420 IPC"
        result, alerts = self._normalize(text)
        self.assertEqual(alerts[0].occurrences, 2)

    def test_no_old_sections_unchanged(self):
        text = "This text has no old IPC sections."
        result, alerts = self._normalize(text)
        self.assertEqual(result, text)
        self.assertEqual(len(alerts), 0)

    def test_304a_not_confused_with_304(self):
        text = "Section 304A IPC causes negligent death."
        result, _ = self._normalize(text)
        self.assertIn("Section 106 BNS", result)
        self.assertNotIn("Section 105 BNS", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
