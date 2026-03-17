"""AAAI abstract source — STUB, not yet implemented.

Covers: aaai (~15k papers)

Findings from investigation (2026-03-17):
  - PDF URLs look like: https://ojs.aaai.org/index.php/AAAI/article/view/3762/3640
  - The /3640 suffix is the PDF galley ID — stripping it gives the article view page
  - Article page URL: https://ojs.aaai.org/index.php/AAAI/article/view/3762
  - Abstract is in: <section class="abstract">
  - Previously reported as "403 Forbidden" but that was the PDF URL, not the article page
  - Article pages return 200 OK with full abstract text

URL transform: strip last path segment (PDF galley ID) from the URL
  e.g. .../view/3762/3640 -> .../view/3762

TODO: Implement transform_url() and extract_abstract()
"""

from .base import AbstractSource


class AaaiSource(AbstractSource):
    conferences = ["aaai"]

    def transform_url(self, pdf_url):
        # TODO: strip last path segment (galley ID) to get article view URL
        # https://ojs.aaai.org/index.php/AAAI/article/view/3762/3640 -> .../view/3762
        raise NotImplementedError("AAAI plugin not yet implemented")

    def extract_abstract(self, soup):
        # TODO: soup.find("section", class_="abstract")
        raise NotImplementedError("AAAI plugin not yet implemented")
