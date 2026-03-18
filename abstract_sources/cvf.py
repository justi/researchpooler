"""CVF (Computer Vision Foundation) abstract source.

Covers: cvpr (~18.5k), iccv (~9.1k), wacv (~4.4k) — total ~32k papers

URL transform: replace /papers/ with /html/ in path, .pdf -> .html
  Works for both older (2013-2019) and newer (2020+) URL formats.
Abstract element: <div id="abstract">

Note: ECCV uses ecva.net (not thecvf.com) and has no HTML pages — not covered here.
"""

from .base import AbstractSource


class CvfSource(AbstractSource):
    conferences = ["cvpr", "iccv", "wacv"]

    def transform_url(self, pdf_url):
        if not pdf_url:
            return None
        # Replace /papers/ with /html/ and .pdf with .html
        # Works for both older (content_cvpr_2013) and newer (content/CVPR2023) formats
        if "thecvf.com" in pdf_url and "/papers/" in pdf_url:
            return pdf_url.replace("/papers/", "/html/").replace(".pdf", ".html")
        return None

    def extract_abstract(self, soup):
        div = soup.find("div", id="abstract")
        if div:
            return div.get_text().strip()
        return None
