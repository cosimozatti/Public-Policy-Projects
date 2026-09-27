"""Run with: python3 -m unittest discover -s .claude/skills/verified-research/tests"""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import verify_citations as vc  # noqa: E402

FX = HERE / "fixtures"


class VerifyDraft(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        lib = vc.load_library([FX / "library.bib", FX / "library.json"])
        corpus = vc.Corpus(FX / "notes", None, None)
        cls.rep, cls.cited = vc.verify_draft(FX / "draft.md", lib, corpus, online=False)
        cls.lib = lib

    def msgs(self, level):
        return [f"{w} {m}" for lv, w, m in self.rep.rows if lv == level]

    def has(self, level, *needles):
        return any(all(n in m for n in needles) for m in self.msgs(level))

    def test_verbatim_quote_found_in_note(self):
        self.assertTrue(self.has("OK", "L4", "testauthor2020alpha.md"))

    def test_quote_attributed_to_wrong_source(self):
        self.assertTrue(self.has("ERROR", "L6", "other-note.md", "check attribution"))

    def test_misquote_rejected(self):
        self.assertTrue(self.has("ERROR", "L8", "NOT found verbatim"))

    def test_unknown_keys(self):
        self.assertTrue(self.has("ERROR", "@ghostkey2024"))
        self.assertTrue(self.has("ERROR", "@alsoghost"))

    def test_locator_outside_page_range(self):
        self.assertTrue(self.has("ERROR", "p. 300", "101–125"))

    def test_incomplete_entry(self):
        self.assertTrue(self.has("ERROR", "@incomplete2021", "volume, pages"))

    def test_uncited_quote(self):
        self.assertTrue(self.has("ERROR", "L20", "quotation without citation"))

    def test_figures(self):
        self.assertTrue(self.has("WARN", "L10", "without a page/section locator"))
        self.assertTrue(self.has("WARN", "L12", "no citation"))
        self.assertFalse(any("L14" in m for m in self.msgs("WARN")))  # [SOURCE?] marker accepted

    def test_email_is_not_a_citation(self):
        self.assertFalse(any("example" in m for m in self.msgs("ERROR")))

    def test_mla(self):
        ref = vc.mla(self.lib["testauthor2020alpha"])
        self.assertEqual(ref, 'Testauthor, Alpha, and Beta Second. "A Fictional Article on Teacher Training." '
                              '*Journal of Test Fixtures*, vol. 12, no. 3, 2020, pp. 101–125, '
                              'https://doi.org/10.0000/fixture.2020.001.')
        self.assertIn("[MISSING: pages]", vc.mla(self.lib["incomplete2021"]))

    def test_csl_json_loaded(self):
        self.assertIn("cslfixture2022", self.cited)
        self.assertEqual(self.lib["cslfixture2022"].page_range(), (1, 20))


class Figures(unittest.TestCase):
    def figs(self, text):
        return vc.FIGURE_RE.search(vc.STAT_LEVEL_RE.sub(" ", text))

    def test_statistical_levels_are_not_figures(self):
        self.assertIsNone(self.figs("The 95% upper bounds are 0.187 and 0.122."))
        self.assertIsNone(self.figs("None is significant at 5%, and none at the 10% level."))

    def test_data_percentages_still_flagged(self):
        self.assertIsNotNone(self.figs("Attendance was 60% for math."))
        self.assertIsNotNone(self.figs("The 95% interval excludes it, but 59% of teachers cite materials."))


class Parsing(unittest.TestCase):
    def test_latex_and_pandoc(self):
        c = vc.extract_citations(1, r"See [see @a, pp. 3-4; @b, sec. 2] and \textcite[cf.][7]{c,d} and @e [p. 9].")
        self.assertEqual([(x.key, x.locator) for x in c],
                         [("a", "pp. 3-4"), ("b", "sec. 2"), ("e", "p. 9"), ("c", "7"), ("d", "7")])

    def test_abbreviated_page_range(self):
        e = vc.Entry(key="x", type="article", raw_type="article", pages="123-45")
        self.assertEqual(e.page_range(), (123, 145))


if __name__ == "__main__":
    unittest.main()
