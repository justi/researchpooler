"""IJCAI abstract source.

Covers: ijcai
URL transform: strip .pdf suffix -> proceedings HTML page
Abstract element: <div class="col-md-12"> abstract section
"""

from .base import AbstractSource


class IjcaiSource(AbstractSource):
    conferences = ["ijcai"]

    def transform_url(self, pdf_url):
        if not pdf_url:
            return None
        # https://www.ijcai.org/Proceedings/13/Papers/010.pdf -> strip .pdf
        if pdf_url.endswith(".pdf"):
            return pdf_url[:-4]
        return pdf_url

    def extract_abstract(self, soup):
        # IJCAI proceedings pages have abstract in various structures

        # Try <div class="col-md-12"> with abstract content
        for div in soup.find_all("div", class_="col-md-12"):
            text = div.get_text().strip()
            # Look for substantial text that looks like an abstract
            if 100 < len(text) < 3000 and not text.startswith("IJCAI"):
                return text

        # Fallback: look for paragraph after title
        # IJCAI pages often have: <h1>Title</h1> <p>abstract text</p>
        h1 = soup.find("h1")
        if h1:
            for sib in h1.next_siblings:
                if hasattr(sib, 'name') and sib.name == "p":
                    text = sib.get_text().strip()
                    if len(text) > 100:
                        return text

        # Fallback: meta description
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            content = meta["content"].strip()
            if len(content) > 100:
                return content

        return None
