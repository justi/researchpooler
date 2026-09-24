"""ECCV abstract source.

Covers: eccv

The paper page URL cannot be derived from the PDF URL, which is what the first
version of this source tried and why it stalled at 5%: ECCV 2024 serves
papers/00004.pdf beside html/4_ECCV_2024_paper.php - the same paper, with the
zero padding dropped - and every guessed URL came back 404. So the pairing is
read out of the proceedings index instead, which lists both links per entry.
The index is ~3.6 MB and is fetched once per run.

Abstract element: <div id="abstract">
"""

import re
import urllib.request

from .base import AbstractSource, USER_AGENT

INDEX_URL = "https://www.ecva.net/papers.php"
SITE = "https://www.ecva.net/"

# Both link forms appear unquoted, single-quoted and double-quoted in the same
# document, so the quote character cannot be relied on.
LINK_RE = re.compile(r"href=['\"]?(papers/eccv_\d{4}/[^'\"> ]+\.(?:php|pdf))")


class EccvSource(AbstractSource):
    conferences = ["eccv"]

    def __init__(self):
        self._pages = None

    def transform_url(self, pdf_url):
        if not pdf_url or not pdf_url.endswith(".pdf"):
            return None

        return self.index().get(self.relative(pdf_url))

    # The pickle holds absolute URLs and the index relative ones.
    @staticmethod
    def relative(url):
        return url.split(SITE, 1)[-1].lstrip("/")

    def index(self):
        """Map every PDF path in the proceedings index to its paper page."""
        if self._pages is None:
            self._pages = self.build_index(self.fetch_index())
        return self._pages

    def fetch_index(self):
        req = urllib.request.Request(INDEX_URL, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.read().decode("utf-8", errors="replace")

    @staticmethod
    def build_index(html):
        """Pair each PDF link with the paper page that precedes it.

        Only the FIRST pdf after a page is taken, and clearing `current` is what
        enforces that: an entry also lists a "-supp.pdf" supplement, and without
        the reset the supplement would overwrite the paper's own link.
        """
        pages = {}
        current = None
        for path in LINK_RE.findall(html):
            if path.endswith(".php"):
                current = SITE + path
            elif current:
                pages[path] = current
                current = None
        return pages

    def extract_abstract(self, soup):
        el = soup.find(id="abstract")
        if not el:
            return None

        text = el.get_text().strip().strip('"').strip("“").strip("”").strip()
        return text if len(text) > 50 else None
