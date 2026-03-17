"""ACL Anthology abstract source.

Covers: acl, emnlp, naacl, coling, eacl, aacl, ijcnlp, conll, semeval
URL transform: strip .pdf suffix -> HTML page with abstract
Abstract element: <span class="acl-abstract"> or <div class="card-body acl-abstract">
"""

from .base import AbstractSource


class AclAnthologySource(AbstractSource):
    conferences = ["acl", "emnlp", "naacl", "coling", "eacl", "aacl", "ijcnlp", "conll", "semeval"]

    def transform_url(self, pdf_url):
        if not pdf_url:
            return None
        # https://aclanthology.org/W00-1100.pdf -> https://aclanthology.org/W00-1100
        if pdf_url.endswith(".pdf"):
            return pdf_url[:-4]
        return pdf_url

    def extract_abstract(self, soup):
        # Try <span class="acl-abstract"> first (current ACL Anthology layout)
        el = soup.find("span", class_="acl-abstract")
        if el:
            return el.get_text()

        # Fallback: <div class="card-body acl-abstract">
        el = soup.find("div", class_="acl-abstract")
        if el:
            return el.get_text()

        # Fallback: <textarea id="paperAbstract">
        el = soup.find("textarea", id="paperAbstract")
        if el:
            return el.get_text()

        # Fallback: look for "Abstract" section
        for tag in soup.find_all(["h2", "h3", "h4", "h5"]):
            if "abstract" in tag.get_text().lower():
                sib = tag.find_next_sibling()
                if sib:
                    return sib.get_text()

        return None
