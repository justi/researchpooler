"""PMLR abstract source.

Covers: icml, aistats, colt, corl, uai, acml, l4dc, midl, mlhc, pgm, clear, alt, automl
URL transform: .pdf -> .html
Abstract element: content after "Abstract" heading, or <div id="abstract">
"""

from .base import AbstractSource


class PmlrSource(AbstractSource):
    conferences = ["icml", "aistats", "colt", "corl", "uai", "acml", "l4dc", "midl", "mlhc", "pgm", "clear", "alt", "automl"]

    def transform_url(self, pdf_url):
        if not pdf_url:
            return None
        # New format: .../v202/aamand23a/aamand23a.pdf -> .../v202/aamand23a.html
        # Old format: .../v28/sznitman13.pdf -> .../v28/sznitman13.html
        if pdf_url.endswith(".pdf"):
            # Strip filename, check if parent dir has same name
            parent = pdf_url.rsplit("/", 1)[0]
            grandparent = parent.rsplit("/", 1)[0]
            dirname = parent.rsplit("/", 1)[-1]
            filename = pdf_url.rsplit("/", 1)[-1].replace(".pdf", "")
            if dirname == filename:
                # New nested format: go up one level
                return parent + ".html"
            else:
                # Old flat format: just swap extension
                return pdf_url[:-4] + ".html"
        return pdf_url

    def extract_abstract(self, soup):
        # Try <div id="abstract">
        el = soup.find("div", id="abstract")
        if el:
            return el.get_text()

        # Try content after "Abstract" heading
        for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
            text = tag.get_text().strip()
            if text.lower() in ("abstract", "#### abstract"):
                # Collect text from following siblings
                parts = []
                for sib in tag.next_siblings:
                    if hasattr(sib, 'name') and sib.name in ("h1", "h2", "h3", "h4", "hr"):
                        break
                    t = sib.get_text() if hasattr(sib, 'get_text') else str(sib)
                    t = t.strip()
                    if t:
                        parts.append(t)
                if parts:
                    return " ".join(parts)

        # Fallback: look for <p> after "Abstract" text node
        body = soup.get_text()
        if "Abstract" in body:
            import re
            m = re.search(r'Abstract\s*\n\s*(.+?)(?:\n\s*\n|\Z)', body, re.DOTALL)
            if m and len(m.group(1).strip()) > 50:
                return m.group(1).strip()

        return None
