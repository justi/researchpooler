"""MICCAI abstract source.

Covers: miccai

Like ECCV, the paper page cannot be derived from the PDF name - the site serves
paper/1861_paper.pdf beside 001-Paper1861.html, where the prefix is a position
in the proceedings, not a property of the paper. The site's own search index
(search.json, one small file per year) already pairs the two, so it is read
instead of crawling the 1.5 MB listing page.

Abstract element: the <p> after an "Abstract" heading.
"""

import json
import re
import urllib.request

from .base import AbstractSource, USER_AGENT

SITE = "https://papers.miccai.org"
INDEX_URL = SITE + "/miccai-{year}/js/search.json"
YEAR_RE = re.compile(r"/miccai-(\d{4})/")


class MiccaiSource(AbstractSource):
    conferences = ["miccai"]

    def __init__(self):
        self._years = {}

    def transform_url(self, pdf_url):
        if not pdf_url or not pdf_url.endswith(".pdf"):
            return None

        year = YEAR_RE.search(pdf_url)
        return self.index(year.group(1)).get(pdf_url) if year else None

    def index(self, year):
        """Map every PDF link in one year's search index to its paper page."""
        if year not in self._years:
            self._years[year] = self.build_index(self.fetch_index(year))
        return self._years[year]

    def fetch_index(self, year):
        req = urllib.request.Request(INDEX_URL.format(year=year), headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception:
            # A year with no index is a year with no abstracts, not a crash -
            # the pickle can hold an edition the site has not published yet.
            return "[]"

    @staticmethod
    def build_index(payload):
        try:
            records = json.loads(payload)
        except ValueError:
            return {}

        pages = {}
        for record in records:
            pdf, url = record.get("pdflink"), record.get("url")
            if pdf and url:
                pages[pdf] = SITE + url
        return pages

    def extract_abstract(self, soup):
        for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
            if tag.get_text().strip().lower() != "abstract":
                continue

            paragraph = tag.find_next("p")
            text = paragraph.get_text().strip() if paragraph else ""
            return text if len(text) > 50 else None

        return None
