"""CVF (Computer Vision Foundation) abstract source — STUB, not yet implemented.

Covers: cvpr (~18.5k), iccv (~9.1k), wacv (~4.4k) — total ~32k papers

Findings from investigation (2026-03-17):
  - PDF URLs: https://openaccess.thecvf.com/content_cvpr_2013/papers/Kim_Deformable_..._paper.pdf
  - HTML URLs: same path but /papers/ -> /html/ and .pdf -> .html
  - Works for 2013-2023 across cvpr, iccv, wacv (tested)
  - Abstract is in: <div id="abstract">
  - Also has <b>Abstract</b> heading before the div
  - Older format (2013-2019): /content_cvpr_2013/papers/ -> /content_cvpr_2013/html/
  - Newer format (2020+): /content/CVPR2023/papers/ -> /content/CVPR2023/html/
  - Both formats confirmed working

URL transform: replace /papers/ with /html/ in path, .pdf -> .html
Abstract element: <div id="abstract">

ECCV note: ECCV uses ecva.net, NOT thecvf.com. ECCV has no HTML pages (PDF only).
  ECCV is NOT covered by this plugin.

TODO: Implement transform_url() and extract_abstract()
"""

from .base import AbstractSource


class CvfSource(AbstractSource):
    conferences = ["cvpr", "iccv", "wacv"]

    def transform_url(self, pdf_url):
        # TODO: pdf_url.replace("/papers/", "/html/").replace(".pdf", ".html")
        raise NotImplementedError("CVF plugin not yet implemented")

    def extract_abstract(self, soup):
        # TODO: soup.find("div", id="abstract")
        raise NotImplementedError("CVF plugin not yet implemented")
