"""Run from the project root with:  python -m unittest discover -v"""
import pickle
import tempfile
import unittest
from pathlib import Path

from my_tools.Corpus import Corpus
from my_tools.Document import Document
from my_tools.TextProcessor import TextProcessor as TP


def make_doc(filename, text):
    """A Document without running PDF extraction."""
    doc = Document.__new__(Document)
    doc.file_path = Path(filename)
    doc.filename = filename
    doc.metadata = {}
    doc.text = text
    doc.tokens = text.lower().split()
    doc.nr_tokens = len(doc.tokens)
    doc.char_number = len(text)
    return doc


def make_pdf_bytes(text):
    """Smallest possible one-page PDF with a text layer."""
    stream = b"BT /F1 12 Tf 72 720 Td (" + text.encode() + b") Tj ET"
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offsets = b"%PDF-1.4\n", []
    for i, obj in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + obj + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF" % (len(objs) + 1, xref)
    return out


class TextProcessorTests(unittest.TestCase):
    tokens = "the licence was relinquished and the licence area was returned".split()

    def test_concordance_single_word(self):
        hits = TP.concordance(self.tokens, "Licence", width=2)
        self.assertEqual(hits[0], ("the", "licence", "was relinquished"))
        self.assertEqual(len(hits), 2)

    def test_concordance_phrase(self):
        hits = TP.concordance(self.tokens, "licence area", width=1)
        self.assertEqual(hits, [("the", "licence area", "was")])

    def test_concordance_no_hit_and_empty(self):
        self.assertEqual(TP.concordance(self.tokens, "oil"), [])
        self.assertEqual(TP.concordance(self.tokens, "  "), [])

    def test_ngrams_positions(self):
        any_ = TP.ngrams(self.tokens, "returned", 2, "any")
        self.assertEqual(any_, [("was", "returned")])
        first = TP.ngrams(self.tokens, "was", 2, "first")
        self.assertEqual(first, [("was", "relinquished"), ("was", "returned")])
        last = TP.ngrams(self.tokens, "was", 2, "last")
        self.assertEqual(last, [("licence", "was"), ("area", "was")])
        self.assertEqual(len(TP.ngrams(self.tokens, None, 3)), len(self.tokens) - 2)
        self.assertEqual(TP.ngrams(["a"], None, 2), [])

    def test_ngram_counts(self):
        counts = TP.ngram_counts(self.tokens, "licence", 2, "first")
        self.assertEqual(counts[("licence", "was")], 1)
        self.assertEqual(sum(TP.ngram_counts(self.tokens, "was", 2, "last").values()), 2)

    def test_token_freq_and_clean(self):
        self.assertEqual(TP.token_freq(self.tokens, "the"), 2)
        self.assertEqual(TP.clean_tokens(["the", "well", "!"], True, True), ["well"])

    def test_collocates(self):
        docs = [("drilling of the well showed oil in the well " * 3).split(),
                "the well was dry".split()]
        rows = TP.collocates(docs, "well", window=2, min_freq=2, measure="freq", exclude_stopwords=True)
        words = [r["collocate"] for r in rows]
        self.assertNotIn("the", words)          # stopword removed
        self.assertNotIn("well", words)         # node itself excluded
        self.assertEqual(rows[0]["cooccurrence"], max(r["cooccurrence"] for r in rows))
        self.assertTrue(all(r["cooccurrence"] >= 2 for r in rows))
        self.assertEqual(TP.collocates(docs, "missing"), [])
        with self.assertRaises(ValueError):
            TP.collocates(docs, "well", measure="nope")

    def test_collocates_do_not_cross_documents(self):
        rows = TP.collocates([["alpha", "node"], ["beta", "gamma"]], "node", window=3,
                             min_freq=1, exclude_stopwords=False)
        self.assertEqual([r["collocate"] for r in rows], ["alpha"])


class DocumentTests(unittest.TestCase):
    def test_pdf_text_extraction_and_cleaning(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "1_Relinquishment_report_PL_506S_506BS.pdf"
            path.write_bytes(make_pdf_bytes("The licence was relinquished (Figure 1.1) in 2015."))
            doc = Document(path, character_threshold=0)  # 0 = never fall back to OCR
        self.assertIn("licence", doc.tokens)
        self.assertIn("2015", doc.tokens)
        self.assertNotIn("figure", doc.tokens)
        self.assertEqual(doc.nr_tokens, len(doc.tokens))

    def test_filename_metadata(self):
        meta = make_doc("20108101_Relinquishment_report_PL_506S_506BS_506CS.pdf", "x").filename_metadata()
        self.assertEqual(meta, {"file_id": "20108101", "licences": ["506S", "506BS", "506CS"]})
        self.assertEqual(make_doc("20757_Relinquishment_report_PL_091F.PDF", "x").filename_metadata()["licences"], ["091F"])
        self.assertEqual(make_doc("odd.pdf", "x").filename_metadata()["licences"], [])

    def test_old_pickle_without_metadata_still_loads(self):
        doc = make_doc("a.pdf", "some text")
        del doc.__dict__["metadata"]
        loaded = pickle.loads(pickle.dumps(doc))
        self.assertEqual(loaded.metadata, {})

    def test_cid_garbage_removed_from_old_pickles(self):
        doc = make_doc("a.pdf", "oil cid 32 cid 82 field cid")
        doc.tokens = doc.text.split()
        loaded = pickle.loads(pickle.dumps(doc))
        self.assertEqual(loaded.tokens, ["oil", "field", "cid"])  # a lone 'cid' with no number is a real word
        self.assertEqual(loaded.nr_tokens, 3)
        self.assertNotIn("32", loaded.text)

    def test_extract_metadata_with_ai_uses_client(self):
        class FakeClient:
            def extract_metadata(self, text):
                return {"title": "T", "seen": text[:4]}
        doc = make_doc("a.pdf", "some text")
        self.assertEqual(doc.extract_metadata_with_ai(FakeClient())["seen"], "some")
        self.assertIn("ai_extracted", doc.metadata)


class CorpusTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_from_cache_and_lookup(self):
        cache = self.tmp / "cache"
        cache.mkdir()
        for name, text in [("a.pdf", "one two"), ("b.pdf", "three"), ("c.pdf", "one two")]:
            with open(cache / (name + ".pkl"), "wb") as f:
                pickle.dump(make_doc(name, text), f)
        (cache / "broken.pdf.pkl").write_bytes(b"not a pickle")

        corpus = Corpus.from_cache(cache)
        self.assertEqual(len(corpus), 3)
        self.assertEqual(len(corpus.failed), 1)
        # the original bug: get_document returned None for everything but the first document
        self.assertEqual(corpus.get_document("b.pdf").text, "three")
        self.assertIsNone(corpus.get_document("zzz.pdf"))
        self.assertEqual(corpus.get_all_tokens(), ["one", "two", "three", "one", "two"])
        self.assertEqual(corpus.duplicate_groups(), [["a.pdf", "c.pdf"]])
        self.assertEqual([d.filename for d in corpus.unique_documents()], ["a.pdf", "b.pdf"])

    def test_pdf_folder_creates_and_reuses_cache(self):
        pdfs, cache = self.tmp / "pdfs", self.tmp / "cache"   # cache dir does not exist yet
        pdfs.mkdir()
        (pdfs / "good.PDF").write_bytes(make_pdf_bytes("Production licence relinquished " * 40))
        (pdfs / "bad.pdf").write_bytes(b"this is not a pdf")
        (pdfs / "notes.txt").write_text("ignored")

        corpus = Corpus(str(pdfs), cache_dir=cache)
        self.assertEqual([d.filename for d in corpus], ["good.PDF"])
        self.assertEqual([name for name, _ in corpus.failed], ["bad.pdf"])
        self.assertTrue((cache / "good.PDF.pkl").exists())

        mtime = (cache / "good.PDF.pkl").stat().st_mtime_ns
        again = Corpus(str(pdfs), cache_dir=cache)
        self.assertEqual(len(again), 1)
        self.assertEqual((cache / "good.PDF.pkl").stat().st_mtime_ns, mtime)  # not rewritten

    def test_missing_folder(self):
        with self.assertRaises(FileNotFoundError):
            Corpus(str(self.tmp / "nope"), cache_dir=self.tmp)
        with self.assertRaises(FileNotFoundError):
            Corpus.from_cache(self.tmp / "nope")


if __name__ == "__main__":
    unittest.main()
