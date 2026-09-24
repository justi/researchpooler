"""Unit tests for abstract source plugins — URL transforms and HTML extraction."""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from abstract_sources.acl_anthology import AclAnthologySource
from abstract_sources.pmlr import PmlrSource
from abstract_sources.openreview import OpenReviewSource
from abstract_sources.ijcai import IjcaiSource
from abstract_sources.isca import IscaSource
from abstract_sources.jmlr import JmlrSource
from abstract_sources.usenix import UsenixSource
from abstract_sources.eccv import EccvSource
from abstract_sources.miccai import MiccaiSource


class TestAclAnthologyTransform(unittest.TestCase):
    def setUp(self):
        self.src = AclAnthologySource()

    def test_strip_pdf(self):
        self.assertEqual(
            self.src.transform_url("https://aclanthology.org/W00-1100.pdf"),
            "https://aclanthology.org/W00-1100"
        )

    def test_no_pdf_suffix(self):
        self.assertEqual(
            self.src.transform_url("https://aclanthology.org/W00-1100"),
            "https://aclanthology.org/W00-1100"
        )

    def test_none(self):
        self.assertIsNone(self.src.transform_url(None))


class TestAclAnthologyExtract(unittest.TestCase):
    def setUp(self):
        self.src = AclAnthologySource()

    def test_span_acl_abstract(self):
        from bs4 import BeautifulSoup
        html = '<html><body><span class="acl-abstract">This is a test abstract for a paper.</span></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        self.assertEqual(self.src.extract_abstract(soup), "This is a test abstract for a paper.")

    def test_div_acl_abstract(self):
        from bs4 import BeautifulSoup
        html = '<html><body><div class="acl-abstract">Another abstract text here.</div></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        self.assertEqual(self.src.extract_abstract(soup), "Another abstract text here.")


class TestPmlrTransform(unittest.TestCase):
    def setUp(self):
        self.src = PmlrSource()

    def test_nested_format(self):
        """New format: /v202/aamand23a/aamand23a.pdf -> /v202/aamand23a.html"""
        self.assertEqual(
            self.src.transform_url("https://proceedings.mlr.press/v202/aamand23a/aamand23a.pdf"),
            "https://proceedings.mlr.press/v202/aamand23a.html"
        )

    def test_flat_format(self):
        """Old format: /v28/sznitman13.pdf -> /v28/sznitman13.html"""
        self.assertEqual(
            self.src.transform_url("http://proceedings.mlr.press/v28/sznitman13.pdf"),
            "http://proceedings.mlr.press/v28/sznitman13.html"
        )

    def test_none(self):
        self.assertIsNone(self.src.transform_url(None))


class TestPmlrExtract(unittest.TestCase):
    def setUp(self):
        self.src = PmlrSource()

    def test_div_id_abstract(self):
        from bs4 import BeautifulSoup
        html = '<html><body><h4>Abstract</h4><div id="abstract">We study density estimation tradeoffs.</div></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        self.assertEqual(self.src.extract_abstract(soup), "We study density estimation tradeoffs.")


class TestJmlrTransform(unittest.TestCase):
    def setUp(self):
        self.src = JmlrSource()

    def test_volume_format(self):
        """volume24/18-080/18-080.pdf -> v24/18-080.html"""
        self.assertEqual(
            self.src.transform_url("https://jmlr.org/papers/volume24/18-080/18-080.pdf"),
            "https://jmlr.org/papers/v24/18-080.html"
        )

    def test_short_format(self):
        """v22/20-1234.pdf -> v22/20-1234.html"""
        self.assertEqual(
            self.src.transform_url("https://jmlr.org/papers/v22/20-1234.pdf"),
            "https://jmlr.org/papers/v22/20-1234.html"
        )


class TestIjcaiTransform(unittest.TestCase):
    def setUp(self):
        self.src = IjcaiSource()

    def test_strip_pdf(self):
        self.assertEqual(
            self.src.transform_url("https://www.ijcai.org/Proceedings/13/Papers/010.pdf"),
            "https://www.ijcai.org/Proceedings/13/Papers/010"
        )


class TestIscaTransform(unittest.TestCase):
    def setUp(self):
        self.src = IscaSource()

    def test_pdf_to_html(self):
        self.assertEqual(
            self.src.transform_url("https://www.isca-archive.org/interspeech_2016/foo.pdf"),
            "https://www.isca-archive.org/interspeech_2016/foo.html"
        )


class TestUsenixTransform(unittest.TestCase):
    def setUp(self):
        self.src = UsenixSource()

    def test_html_url_passthrough(self):
        url = "https://www.usenix.org/conference/osdi16/technical-sessions/presentation/sigurbjarnarson"
        self.assertEqual(self.src.transform_url(url), url)

    def test_pdf_returns_none(self):
        self.assertIsNone(self.src.transform_url("https://example.com/paper.pdf"))


class TestOpenReviewTransform(unittest.TestCase):
    def setUp(self):
        self.src = OpenReviewSource()

    def test_transform_returns_none(self):
        """OpenReview uses bulk API, not per-paper URL transform."""
        self.assertIsNone(self.src.transform_url("https://openreview.net/pdf/abc123.pdf"))


# The whole point of this source is that the paper page CANNOT be derived from
# the PDF name, so every test here works off an index fragment rather than a
# transform rule. The 2024 fragment is the case that broke the first version:
# 00004.pdf next to 4_ECCV_2024_paper.php.
ECCV_INDEX = """
<dt class="ptitle"><a href=papers/eccv_2024/papers_ECCV/html/4_ECCV_2024_paper.php>Title</a></dt>
<dd>[<a href='papers/eccv_2024/papers_ECCV/papers/00004.pdf'>pdf</a>]
<div class="link2">[<a href='papers/eccv_2024/papers_ECCV/papers/00004-supp.pdf'>supp</a>]</div></dd>
<dt class="ptitle"><a href="papers/eccv_2018/papers_ECCV/html/A_Author_Some_Paper_ECCV_2018_paper.php">T2</a></dt>
<dd>[<a href='papers/eccv_2018/papers_ECCV/papers/A_Author_Some_Paper_ECCV_2018_paper.pdf'>pdf</a>]</dd>
"""


class TestEccvIndex(unittest.TestCase):
    def setUp(self):
        self.src = EccvSource()
        self.index = EccvSource.build_index(ECCV_INDEX)

    def test_zero_padded_pdf_maps_to_unpadded_page(self):
        self.assertEqual(
            self.index["papers/eccv_2024/papers_ECCV/papers/00004.pdf"],
            "https://www.ecva.net/papers/eccv_2024/papers_ECCV/html/4_ECCV_2024_paper.php",
        )

    def test_supplement_is_not_indexed(self):
        self.assertNotIn("papers/eccv_2024/papers_ECCV/papers/00004-supp.pdf", self.index)

    def test_both_quoting_styles_are_read(self):
        """The index mixes bare, single- and double-quoted hrefs in one page."""
        self.assertEqual(len(self.index), 2)

    def test_a_supplement_does_not_steal_the_next_papers_page(self):
        pdf = "papers/eccv_2018/papers_ECCV/papers/A_Author_Some_Paper_ECCV_2018_paper.pdf"
        self.assertTrue(self.index[pdf].endswith("A_Author_Some_Paper_ECCV_2018_paper.php"))

    def test_absolute_pdf_url_is_matched_against_the_relative_index(self):
        self.src._pages = self.index
        self.assertEqual(
            self.src.transform_url("https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/00004.pdf"),
            "https://www.ecva.net/papers/eccv_2024/papers_ECCV/html/4_ECCV_2024_paper.php",
        )

    def test_unknown_pdf_yields_no_url(self):
        self.src._pages = self.index
        self.assertIsNone(self.src.transform_url("https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/99999.pdf"))

    def test_non_pdf_is_skipped_without_touching_the_index(self):
        self.assertIsNone(self.src.transform_url("https://www.ecva.net/papers.php"))


MICCAI_INDEX = """[
  {"title": "A", "url": "/miccai-2024/001-Paper1861.html",
   "pdflink": "https://papers.miccai.org/miccai-2024/paper/1861_paper.pdf"},
  {"title": "B", "url": "/miccai-2024/002-Paper1908.html",
   "pdflink": "https://papers.miccai.org/miccai-2024/paper/1908_paper.pdf"},
  {"title": "C", "url": "/miccai-2024/003-Paper1001.html"}
]"""


class TestMiccaiIndex(unittest.TestCase):
    def setUp(self):
        self.src = MiccaiSource()
        self.src._years["2024"] = MiccaiSource.build_index(MICCAI_INDEX)

    def test_pdf_maps_to_its_numbered_page(self):
        """The 001- prefix is a position in the proceedings, not derivable."""
        self.assertEqual(
            self.src.transform_url("https://papers.miccai.org/miccai-2024/paper/1861_paper.pdf"),
            "https://papers.miccai.org/miccai-2024/001-Paper1861.html",
        )

    def test_record_without_a_pdf_link_is_dropped(self):
        self.assertEqual(len(self.src._years["2024"]), 2)

    def test_unparseable_index_is_empty_rather_than_fatal(self):
        self.assertEqual(MiccaiSource.build_index("<html>not json</html>"), {})

    def test_a_year_with_no_index_yields_no_url(self):
        """A pickle can hold an edition the site has not published yet."""
        self.src._years["1999"] = {}
        self.assertIsNone(
            self.src.transform_url("https://papers.miccai.org/miccai-1999/paper/1_paper.pdf")
        )

    def test_url_without_a_year_is_skipped(self):
        self.assertIsNone(self.src.transform_url("https://papers.miccai.org/paper/1_paper.pdf"))


class TestMiccaiExtract(unittest.TestCase):
    def setUp(self):
        self.src = MiccaiSource()

    def paragraph_after(self, html):
        from bs4 import BeautifulSoup
        return self.src.extract_abstract(BeautifulSoup(html, "html.parser"))

    def test_paragraph_after_the_abstract_heading(self):
        text = "Scoliosis is currently assessed solely on 2D lateral deviations, which misses much."
        self.assertEqual(self.paragraph_after(f"<h1>Abstract</h1><p>{text}</p>"), text)

    def test_a_heading_that_merely_mentions_abstracts_is_not_it(self):
        text = "This paragraph is long enough to pass the fifty character floor set in base."
        self.assertIsNone(self.paragraph_after(f"<h1>Abstract submission</h1><p>{text}</p>"))

    def test_a_stub_paragraph_is_refused(self):
        self.assertIsNone(self.paragraph_after("<h1>Abstract</h1><p>Too short.</p>"))


if __name__ == "__main__":
    unittest.main()
