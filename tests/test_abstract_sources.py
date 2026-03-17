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


if __name__ == "__main__":
    unittest.main()
