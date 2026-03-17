"""Base class for abstract source plugins."""

import urllib.request
import urllib.error
from bs4 import BeautifulSoup

USER_AGENT = "ResearchPooler/1.0 (academic research tool)"
MAX_ABSTRACT_LENGTH = 2000


class AbstractSource:
    """Base class for abstract extraction plugins.

    Subclasses must implement:
        conferences: list of conference keys (pickle names without 'pubs_')
        transform_url(pdf_url): convert PDF URL to HTML abstract page URL
        extract_abstract(soup): extract abstract text from BeautifulSoup object
    """

    conferences = []

    def transform_url(self, pdf_url):
        """Transform PDF URL to HTML abstract page URL. Return None to skip."""
        raise NotImplementedError

    def extract_abstract(self, soup):
        """Extract abstract text from parsed HTML. Return None if not found."""
        raise NotImplementedError

    def fetch_and_extract(self, pdf_url):
        """Fetch HTML page and extract abstract. Returns str or None."""
        url = self.transform_url(pdf_url)
        if not url:
            return None

        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                html = resp.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
            return None

        try:
            soup = BeautifulSoup(html, "html.parser")
            abstract = self.extract_abstract(soup)
        except Exception:
            return None

        if not abstract:
            return None

        import re
        abstract = re.sub(r'\s+', ' ', abstract).strip()
        if len(abstract) < 50:
            return None
        return abstract[:MAX_ABSTRACT_LENGTH]
