"""NeurIPS abstract source.

Covers: nips
URL: uses the 'url' field from pickle (proceedings.neurips.cc abstract pages)
Abstract element: <h2 class="section-label">Abstract</h2> followed by <p>
"""

from .base import AbstractSource


class NeuripsSource(AbstractSource):
    conferences = ["nips"]

    def transform_url(self, pdf_url):
        # NeurIPS papers have 'url' pointing to abstract page already
        # But pdf_url might be the PDF link — convert back to abstract page
        if not pdf_url:
            return None
        # If it's already an abstract page, use it
        if "-Abstract" in pdf_url:
            return pdf_url
        # Convert PDF URL to abstract page
        # /file/hash-Paper-Conference.pdf -> /hash/hash-Abstract-Conference.html
        if "/file/" in pdf_url and pdf_url.endswith(".pdf"):
            return pdf_url.replace("/file/", "/hash/").replace("-Paper-Conference.pdf", "-Abstract-Conference.html").replace("-Paper-Datasets_and_Benchmarks.pdf", "-Abstract-Datasets_and_Benchmarks.html").replace("-Paper.pdf", "-Abstract.html")
        return pdf_url

    def extract_abstract(self, soup):
        import re
        # Find <h2>Abstract</h2> or similar heading
        for el in soup.find_all(string=re.compile(r'^Abstract$')):
            parent = el.parent
            if parent and parent.name in ("h1", "h2", "h3", "h4"):
                nxt = parent.find_next_sibling("p")
                if nxt:
                    return nxt.get_text()
        return None
