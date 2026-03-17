"""JMLR abstract source.

Covers: jmlr
URL transform: .pdf -> .html (or extract abstract page URL)
Abstract element: page content
"""

import re
from .base import AbstractSource


class JmlrSource(AbstractSource):
    conferences = ["jmlr"]

    def transform_url(self, pdf_url):
        if not pdf_url:
            return None
        # JMLR PDFs: https://jmlr.org/papers/volume24/18-080/18-080.pdf
        # HTML pages: https://jmlr.org/papers/v24/18-080.html
        # Need to: extract volume number, paper id, build new URL
        import re
        m = re.search(r'jmlr\.org/papers/volume(\d+)/([^/]+)', pdf_url)
        if m:
            vol = m.group(1)
            paper_id = m.group(2)
            return f"https://jmlr.org/papers/v{vol}/{paper_id}.html"
        # Already short format
        if pdf_url.endswith(".pdf"):
            return pdf_url[:-4] + ".html"
        return pdf_url

    def extract_abstract(self, soup):
        # JMLR pages typically have <h3>Abstract</h3> followed by <p>

        # Try <div id="abstract">
        el = soup.find("div", id="abstract")
        if el:
            return el.get_text()

        # Look for "Abstract" heading
        for tag in soup.find_all(["h2", "h3", "h4"]):
            if "abstract" in tag.get_text().lower():
                parts = []
                for sib in tag.next_siblings:
                    if hasattr(sib, 'name') and sib.name in ("h2", "h3", "h4", "hr"):
                        break
                    t = sib.get_text() if hasattr(sib, 'get_text') else str(sib)
                    t = t.strip()
                    if t:
                        parts.append(t)
                if parts:
                    return " ".join(parts)

        # Fallback: meta description
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            content = meta["content"].strip()
            if len(content) > 100:
                return content

        return None
