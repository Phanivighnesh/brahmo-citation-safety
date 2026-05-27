"""
test_extractor.py
-----------------
Tests for the citation_extractor module.
Verifies all 6 Indian legal citation formats are correctly extracted.
"""

import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import unittest
from src.database import get_connection
from src.citation_extractor import extract_citations


class TestCitationExtractor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # get_connection() auto-bootstraps the DB on first call — no reset needed.
        # Avoids Windows file-lock errors when multiple test modules share the DB.
        cls.conn = get_connection()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    # ── Pattern 1: SCC ────────────────────────────────────────────────────────
    def test_scc_basic(self):
        text = "In Siddharth v. State of UP (2021) 10 SCC 1 the Court held X."
        found = extract_citations(text, self.conn)
        self.assertEqual(len(found), 1)
        c = found[0]
        self.assertEqual(c.pattern_name, "SCC")
        self.assertEqual(c.year, 2021)
        self.assertEqual(c.volume, 10)
        self.assertEqual(c.page, 1)

    def test_scc_multi(self):
        text = "(2014) 8 SCC 273 and (2022) 10 SCC 51 and (2020) 5 SCC 1"
        found = extract_citations(text, self.conn)
        self.assertEqual(len(found), 3)

    def test_scc_all_3_from_sample_output_1(self):
        text = """
        In Siddharth v. State of UP (2021) 10 SCC 1, guidelines laid down.
        In Satender Kumar Antil v. CBI (2022) 10 SCC 51, categories classified.
        In Arnesh Kumar v. State of Bihar (2014) 8 SCC 273, guidelines issued.
        In Sushila Aggarwal v. State (NCT of Delhi) (2020) 5 SCC 1, clarified.
        """
        found = extract_citations(text, self.conn)
        scc = [c for c in found if c.pattern_name == "SCC"]
        self.assertEqual(len(scc), 4)

    # ── Pattern 2: SCC_OnLine ─────────────────────────────────────────────────
    def test_scc_online_basic(self):
        text = "Delhi HC in 2024 SCC OnLine Del 3456 granted bail."
        found = extract_citations(text, self.conn)
        self.assertEqual(len(found), 1)
        c = found[0]
        self.assertEqual(c.pattern_name, "SCC_OnLine")
        self.assertEqual(c.year, 2024)
        self.assertEqual(c.court_code, "Del")
        self.assertEqual(c.page, 3456)

    def test_scc_online_sc(self):
        text = "2023 SCC OnLine SC 987 is relevant."
        found = extract_citations(text, self.conn)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].court_code, "SC")

    # ── Pattern 3: AIR ────────────────────────────────────────────────────────
    def test_air_basic(self):
        text = "AIR 2024 SC 567 is the leading case."
        found = extract_citations(text, self.conn)
        self.assertEqual(len(found), 1)
        c = found[0]
        self.assertEqual(c.pattern_name, "AIR")
        self.assertEqual(c.year, 2024)
        self.assertEqual(c.court_code, "SC")
        self.assertEqual(c.page, 567)

    def test_air_high_court(self):
        text = "AIR 2023 Del 100 and AIR 2022 Bom 999"
        found = extract_citations(text, self.conn)
        self.assertEqual(len(found), 2)

    # ── Pattern 4: Cri_LJ ────────────────────────────────────────────────────
    def test_cri_lj_basic(self):
        text = "See 2024 Cri LJ 789 for details."
        found = extract_citations(text, self.conn)
        self.assertEqual(len(found), 1)
        c = found[0]
        self.assertEqual(c.pattern_name, "Cri_LJ")
        self.assertEqual(c.year, 2024)
        self.assertEqual(c.page, 789)

    def test_cri_lj_with_parens(self):
        text = "(2023) Cri LJ 456 is also relevant."
        found = extract_citations(text, self.conn)
        self.assertEqual(len(found), 1)

    # ── Pattern 5: SCR ────────────────────────────────────────────────────────
    def test_scr_basic(self):
        text = "(2022) 3 SCR 100"
        found = extract_citations(text, self.conn)
        self.assertEqual(len(found), 1)
        c = found[0]
        self.assertEqual(c.pattern_name, "SCR")
        self.assertEqual(c.year, 2022)
        self.assertEqual(c.volume, 3)
        self.assertEqual(c.page, 100)

    # ── Pattern 6: MANU ───────────────────────────────────────────────────────
    def test_manu_basic(self):
        text = "MANU/SC/0456/2024 confirms the position."
        found = extract_citations(text, self.conn)
        self.assertEqual(len(found), 1)
        c = found[0]
        self.assertEqual(c.pattern_name, "MANU")
        self.assertEqual(c.court_code, "SC")
        self.assertEqual(c.year, 2024)

    def test_manu_high_court(self):
        text = "MANU/DE/0123/2023 from Delhi HC."
        found = extract_citations(text, self.conn)
        self.assertEqual(len(found), 1)

    # ── Multi-format ──────────────────────────────────────────────────────────
    def test_all_6_formats_in_one_text(self):
        text = """
        (2021) 10 SCC 1 held X.
        2024 SCC OnLine Del 456 said Y.
        AIR 2022 SC 300 ruled Z.
        2023 Cri LJ 789 discussed W.
        (2020) 4 SCR 50 confirmed V.
        MANU/SC/0100/2021 clarified U.
        """
        found = extract_citations(text, self.conn)
        names = {c.pattern_name for c in found}
        self.assertIn("SCC", names)
        self.assertIn("SCC_OnLine", names)
        self.assertIn("AIR", names)
        self.assertIn("Cri_LJ", names)
        self.assertIn("SCR", names)
        self.assertIn("MANU", names)

    # ── SETUP_GUIDE sample outputs ────────────────────────────────────────────
    def test_sample_output_1_finds_5_citations(self):
        text = """
        In Siddharth v. State of UP (2021) 10 SCC 1, guidelines laid down.
        In Satender Kumar Antil v. CBI (2022) 10 SCC 51, categories.
        In Arnesh Kumar v. State of Bihar (2014) 8 SCC 273, guidelines.
        In Sushila Aggarwal v. State (NCT of Delhi) (2020) 5 SCC 1, clarified.
        The Delhi High Court in 2024 SCC OnLine Del 3456 granted bail.
        """
        found = extract_citations(text, self.conn)
        self.assertEqual(len(found), 5)

    def test_sample_output_2_finds_7_citations(self):
        text = """
        In Rajesh Sharma v. State of UP (2023) 4 SCC 789 held X.
        In Siddharth v. State of UP (2021) 10 SCC 1 held Y.
        In Amit Kumar v. Union of India AIR 2024 SC 567 held Z.
        In Satender Kumar Antil v. CBI (2022) 10 SCC 51 classified.
        In Arnesh Kumar v. State of Bihar (2014) 8 SCC 273 issued.
        In Sushila Aggarwal v. State (2020) 5 SCC 12 confirmed.
        In Vikram Singh v. State (2024) 8 SCC 234 added.
        """
        found = extract_citations(text, self.conn)
        self.assertEqual(len(found), 7)

    def test_no_duplicate_extraction(self):
        text = "(2021) 10 SCC 1 is the same as (2021) 10 SCC 1."
        found = extract_citations(text, self.conn)
        self.assertEqual(len(found), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
