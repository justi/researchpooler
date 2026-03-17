"""RSS (Robotics: Science and Systems) abstract source — STUB, not yet implemented.

Covers: rss (~1.5k papers)

Findings from investigation (2026-03-17):
  - PDF URLs: https://www.roboticsproceedings.org/rss01/p01.pdf
  - HTML URLs: same but .pdf -> .html
  - Works across all years (2005-2020 tested)
  - Abstract is in a <p> tag — the first substantial paragraph (>200 chars)
  - Some older papers prefix with "Abstract: " in the text
  - No <div id="abstract"> or class="abstract" — must find by content heuristic

URL transform: .pdf -> .html
Abstract extraction: find first <p> with len > 200 chars

TODO: Implement transform_url() and extract_abstract()
"""

from .base import AbstractSource


class RssSource(AbstractSource):
    conferences = ["rss"]

    def transform_url(self, pdf_url):
        # TODO: pdf_url[:-4] + ".html" if pdf_url.endswith(".pdf")
        raise NotImplementedError("RSS plugin not yet implemented")

    def extract_abstract(self, soup):
        # TODO: find first <p> with substantial text (>200 chars)
        # strip "Abstract: " prefix if present
        raise NotImplementedError("RSS plugin not yet implemented")
