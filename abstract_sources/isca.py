"""ISCA Archive abstract source.

Covers: interspeech
URL transform: .pdf -> .html
Abstract element: page content with abstract text
"""

from .base import AbstractSource


class IscaSource(AbstractSource):
    conferences = ["interspeech"]

    def transform_url(self, pdf_url):
        if not pdf_url:
            return None
        # https://www.isca-archive.org/interspeech_2016/makhoul16_interspeech.pdf -> .html
        if pdf_url.endswith(".pdf"):
            return pdf_url[:-4] + ".html"
        return pdf_url

    def extract_abstract(self, soup):
        # ISCA archive pages have abstract in various structures

        # Try <div class="abstract"> or similar
        for cls in ["abstract", "Abstract", "paper-abstract"]:
            el = soup.find("div", class_=cls)
            if el:
                return el.get_text()

        # Look for "Abstract" heading
        for tag in soup.find_all(["h2", "h3", "h4", "b", "strong"]):
            if "abstract" in tag.get_text().lower():
                parts = []
                for sib in tag.next_siblings:
                    if hasattr(sib, 'name') and sib.name in ("h2", "h3", "h4", "hr"):
                        break
                    t = sib.get_text() if hasattr(sib, 'get_text') else str(sib)
                    t = t.strip()
                    if t and len(t) > 20:
                        parts.append(t)
                if parts:
                    return " ".join(parts)

        # Fallback: look for <p> with substantial text
        for p in soup.find_all("p"):
            text = p.get_text().strip()
            if 200 < len(text) < 3000:
                return text

        return None
