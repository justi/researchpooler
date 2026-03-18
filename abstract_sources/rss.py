"""RSS (Robotics: Science and Systems) abstract source.

Covers: rss (~1.5k papers)

URL transform: .pdf -> .html
Abstract extraction: first <p> with >200 chars, strip "Abstract: " prefix if present.
"""

from .base import AbstractSource


class RssSource(AbstractSource):
    conferences = ["rss"]

    def transform_url(self, pdf_url):
        if not pdf_url:
            return None
        # https://www.roboticsproceedings.org/rss01/p01.pdf -> .../rss01/p01.html
        if pdf_url.endswith(".pdf"):
            return pdf_url[:-4] + ".html"
        return None

    def extract_abstract(self, soup):
        # Find first <p> with substantial text (>200 chars)
        for p in soup.find_all("p"):
            text = p.get_text().strip()
            if len(text) > 200:
                # Strip "Abstract: " prefix if present
                if text.startswith("Abstract: "):
                    text = text[len("Abstract: "):]
                elif text.startswith("Abstract:"):
                    text = text[len("Abstract:"):]
                return text.strip()
        return None
