"""AAAI abstract source.

Covers: aaai (~15k papers)

URL transform: strip last path segment (PDF galley ID) from ojs.aaai.org URLs
  e.g. .../view/3762/3640 -> .../view/3762
Abstract element: <section class="abstract">
"""

from .base import AbstractSource


class AaaiSource(AbstractSource):
    conferences = ["aaai"]

    def transform_url(self, pdf_url):
        if not pdf_url:
            return None
        # https://ojs.aaai.org/index.php/AAAI/article/view/3762/3640 -> .../view/3762
        # Strip the last path segment (PDF galley ID)
        if "ojs.aaai.org" in pdf_url and "/view/" in pdf_url:
            return pdf_url.rsplit("/", 1)[0]
        return None

    def extract_abstract(self, soup):
        section = soup.find("section", class_="abstract")
        if section:
            return section.get_text().strip()
        return None
