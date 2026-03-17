"""USENIX abstract source.

Covers: nsdi, osdi
URL transform: URL is already HTML (no .pdf to strip)
Abstract element: page content from proceedings page
"""

from .base import AbstractSource


class UsenixSource(AbstractSource):
    conferences = ["nsdi", "osdi"]

    def transform_url(self, pdf_url):
        # USENIX URLs are already HTML pages:
        # https://www.usenix.org/conference/osdi16/technical-sessions/presentation/sigurbjarnarson
        if not pdf_url:
            return None
        # If it happens to be a PDF URL, try to find the presentation page
        if pdf_url.endswith(".pdf"):
            return None  # Can't reliably transform USENIX PDF URLs
        return pdf_url

    def extract_abstract(self, soup):
        # USENIX presentation pages have abstract in various structures

        # Try <div class="field-name-field-paper-description"> (common USENIX layout)
        el = soup.find("div", class_="field-name-field-paper-description")
        if el:
            return el.get_text()

        # Try <div class="field--name-field-paper-description">
        el = soup.find("div", class_="field--name-field-paper-description")
        if el:
            return el.get_text()

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
                    if t and len(t) > 20:
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
