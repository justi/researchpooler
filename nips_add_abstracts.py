"""
Extract abstracts from NeurIPS HTML abstract pages.

NeurIPS papers have URLs like:
  https://proceedings.neurips.cc/paper_files/paper/2024/hash/HASH-Abstract-Conference.html

These pages contain <h2>Abstract</h2> followed by the full abstract text.
No PDF download needed — much faster than pdf_text extraction.

Usage:
    python nips_add_abstracts.py                  # all papers
    python nips_add_abstracts.py --limit 100      # first 100 without abstract
    python nips_add_abstracts.py --year 2024      # only 2024 papers
    python nips_add_abstracts.py --status          # show progress
"""

import os
import sys
import time
import argparse
import re
import urllib.request
import urllib.error
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from repool_util import loadPubs, savePubs

CHECKPOINT_EVERY = 500
REQUEST_DELAY = 0.5  # seconds between requests
USER_AGENT = "ResearchPooler/1.0 (academic research tool)"
MAX_ABSTRACT_LENGTH = 2000


class AbstractParser(HTMLParser):
    """Simple HTML parser to extract abstract text after <h2>Abstract</h2>."""

    def __init__(self):
        super().__init__()
        self.in_abstract = False
        self.found_h2_abstract = False
        self.abstract_parts = []
        self.current_tag = None
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        if tag == "h2":
            self.depth = 0
        if self.found_h2_abstract and tag in ("p", "div", "span"):
            self.in_abstract = True
            self.depth += 1

    def handle_endtag(self, tag):
        if self.in_abstract and tag in ("p", "div"):
            self.depth -= 1
            if self.depth <= 0:
                self.in_abstract = False

    def handle_data(self, data):
        if self.current_tag == "h2" and "abstract" in data.lower().strip().lower():
            self.found_h2_abstract = True
            return

        if self.in_abstract or (self.found_h2_abstract and self.current_tag == "p"):
            text = data.strip()
            if text and len(text) > 20:  # skip tiny fragments
                self.abstract_parts.append(text)

    def get_abstract(self):
        if not self.abstract_parts:
            return None
        abstract = " ".join(self.abstract_parts)
        # Clean up whitespace
        abstract = re.sub(r'\s+', ' ', abstract).strip()
        if len(abstract) < 50:  # too short to be a real abstract
            return None
        return abstract[:MAX_ABSTRACT_LENGTH]


def fetch_abstract(url):
    """Fetch HTML page and extract abstract text."""
    if not url or "Abstract" not in url:
        return None

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        return None

    parser = AbstractParser()
    try:
        parser.feed(html)
    except Exception:
        return None

    return parser.get_abstract()


def show_status(pubs):
    total = len(pubs)
    with_abstract = sum(1 for p in pubs if p.get("abstract"))
    with_url = sum(1 for p in pubs if p.get("pdf") and "Abstract" in p.get("pdf", ""))
    pct = (with_abstract / total * 100) if total > 0 else 0

    print("=== NeurIPS Abstract Status ===")
    print(f"Total papers:       {total}")
    print(f"With abstract URL:  {with_url}")
    print(f"Abstracts scraped:  {with_abstract} ({pct:.1f}%)")
    print(f"Remaining:          {with_url - with_abstract}")
    print("================================")


def main():
    parser = argparse.ArgumentParser(description="Extract NeurIPS abstracts from HTML")
    parser.add_argument("--limit", type=int, default=None, help="Max papers to process")
    parser.add_argument("--year", type=int, default=None, help="Only this year")
    parser.add_argument("--status", action="store_true", help="Show progress")
    args = parser.parse_args()

    print("Loading pubs_nips...")
    pubs = loadPubs("pubs_nips")
    print(f"Loaded {len(pubs)} papers")

    if args.status:
        show_status(pubs)
        return

    # Filter papers needing abstracts
    to_process = []
    for p in pubs:
        if p.get("abstract"):
            continue  # already has abstract
        if not p.get("pdf") or "Abstract" not in p.get("pdf", ""):
            continue  # no abstract URL
        if args.year and p.get("year") != args.year:
            continue
        to_process.append(p)

    if args.limit:
        to_process = to_process[:args.limit]

    total = len(to_process)
    if total == 0:
        print("No papers to process.")
        show_status(pubs)
        return

    print(f"Processing {total} papers...")
    extracted = 0
    failed = 0

    for i, p in enumerate(to_process):
        url = p["pdf"]
        abstract = fetch_abstract(url)

        if abstract:
            p["abstract"] = abstract
            extracted += 1
            if extracted % 50 == 0 or i < 5:
                print(f"  [{i+1}/{total}] ✓ {p['title'][:60]}... ({len(abstract)} chars)")
        else:
            failed += 1
            if failed <= 5:
                print(f"  [{i+1}/{total}] ✗ {p['title'][:60]}...")

        # Progress every 100
        if (i + 1) % 100 == 0:
            pct = (i + 1) / total * 100
            print(f"  --- {i+1}/{total} ({pct:.1f}%) — {extracted} extracted, {failed} failed ---")

        # Checkpoint
        if (i + 1) % CHECKPOINT_EVERY == 0:
            print(f"  [checkpoint] saving pubs_nips ({extracted} new abstracts)...")
            savePubs("pubs_nips", pubs)

        time.sleep(REQUEST_DELAY)

    # Final save
    savePubs("pubs_nips", pubs)

    print(f"\n=== Done ===")
    print(f"Extracted: {extracted}")
    print(f"Failed:    {failed}")
    print(f"Total with abstract: {sum(1 for p in pubs if p.get('abstract'))}/{len(pubs)}")


if __name__ == "__main__":
    main()
