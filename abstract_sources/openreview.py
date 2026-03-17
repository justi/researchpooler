"""OpenReview abstract source.

Covers: iclr
Uses OpenReview API (not HTML scraping — forum pages return 403).
Fetches abstracts in bulk per year via API v1/v2, matches to existing papers by title.
"""

import json
import re
import time
import urllib.request
import urllib.error
import urllib.parse

from .base import AbstractSource, USER_AGENT, MAX_ABSTRACT_LENGTH

OPENREVIEW_V1 = "https://api.openreview.net"
OPENREVIEW_V2 = "https://api2.openreview.net"
PAGE_SIZE = 1000

VENUE_FILTERS = {
    2021: ['ICLR 2021 Poster', 'ICLR 2021 Oral', 'ICLR 2021 Spotlight'],
    2022: ['ICLR 2022 Poster', 'ICLR 2022 Oral', 'ICLR 2022 Spotlight'],
    2023: ['ICLR 2023 poster', 'ICLR 2023 oral',
           'ICLR 2023 notable top 5%', 'ICLR 2023 notable top 25%'],
}


def _fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as f:
        return json.loads(f.read())


class OpenReviewSource(AbstractSource):
    conferences = ["iclr"]

    def transform_url(self, pdf_url):
        return None  # Not used — we use bulk API instead

    def extract_abstract(self, soup):
        return None  # Not used

    def fetch_and_extract(self, pdf_url):
        return None  # Not used — bulk_fetch handles everything

    def bulk_fetch_abstracts(self, pubs, year=None):
        """Fetch abstracts via OpenReview API and match to pubs by title.
        Returns count of abstracts added."""
        # Group pubs needing abstracts by year
        by_year = {}
        for p in pubs:
            if p.get("abstract"):
                continue
            y = p.get("year")
            if year and y != year:
                continue
            if y:
                by_year.setdefault(y, []).append(p)

        total_added = 0

        for y in sorted(by_year.keys()):
            papers = by_year[y]
            # Build title lookup (lowercase for matching)
            title_map = {}
            for p in papers:
                key = p["title"].strip().lower()
                title_map[key] = p

            print(f"    [API] Fetching ICLR {y} abstracts from OpenReview...")

            try:
                if y >= 2024:
                    abstracts = self._fetch_v2(y)
                elif y >= 2021:
                    abstracts = self._fetch_v1_venue(y)
                else:
                    abstracts = self._fetch_v1_decisions(y)
            except Exception as e:
                print(f"    [API] Error fetching ICLR {y}: {e}")
                continue

            matched = 0
            for title, abstract in abstracts.items():
                key = title.strip().lower()
                if key in title_map:
                    p = title_map[key]
                    if not p.get("abstract"):
                        abstract = re.sub(r'\s+', ' ', abstract).strip()
                        if len(abstract) >= 50:
                            p["abstract"] = abstract[:MAX_ABSTRACT_LENGTH]
                            matched += 1

            print(f"    [API] ICLR {y}: {matched} abstracts matched out of {len(abstracts)} fetched")
            total_added += matched
            time.sleep(0.5)

        return total_added

    def _fetch_v2(self, year):
        """Fetch title->abstract mapping via API v2 (2024+)."""
        result = {}
        offset = 0
        while True:
            url = (f"{OPENREVIEW_V2}/notes?content.venueid=ICLR.cc/{year}/Conference"
                   f"&limit={PAGE_SIZE}&offset={offset}")
            data = _fetch_json(url)
            notes = data.get("notes", [])
            if not notes:
                break
            for note in notes:
                c = note.get("content", {})
                title = c.get("title", {}).get("value", "")
                abstract = c.get("abstract", {}).get("value", "")
                if title and abstract:
                    result[title] = abstract
            offset += len(notes)
            time.sleep(0.2)
        return result

    def _fetch_v1_venue(self, year):
        """Fetch title->abstract via API v1 with venue filter (2021-2023)."""
        result = {}
        venue_strings = VENUE_FILTERS.get(year, [])
        invitation = f"ICLR.cc/{year}/Conference/-/Blind_Submission"

        for venue_str in venue_strings:
            offset = 0
            while True:
                encoded = urllib.parse.quote(venue_str)
                url = (f"{OPENREVIEW_V1}/notes?invitation={invitation}"
                       f"&content.venue={encoded}&limit={PAGE_SIZE}&offset={offset}")
                data = _fetch_json(url)
                notes = data.get("notes", [])
                if not notes:
                    break
                for note in notes:
                    c = note.get("content", {})
                    title = c.get("title", "")
                    abstract = c.get("abstract", "")
                    if title and abstract:
                        result[title] = abstract
                offset += len(notes)
                time.sleep(0.2)
        return result

    def _fetch_v1_decisions(self, year):
        """Fetch title->abstract via API v1 with decision lookup (2018-2020)."""
        result = {}
        invitation = f"ICLR.cc/{year}/Conference/-/Blind_Submission"
        offset = 0
        while True:
            url = (f"{OPENREVIEW_V1}/notes?invitation={invitation}"
                   f"&details=directReplies&limit={PAGE_SIZE}&offset={offset}")
            data = _fetch_json(url)
            notes = data.get("notes", [])
            if not notes:
                break
            for note in notes:
                # Check acceptance
                accepted = False
                replies = note.get("details", {}).get("directReplies", [])
                for reply in replies:
                    rc = reply.get("content", {})
                    decision = rc.get("decision", "") or rc.get("recommendation", "")
                    if "Accept" in decision and "Workshop" not in decision:
                        accepted = True
                        break
                if not accepted:
                    continue

                c = note.get("content", {})
                title = c.get("title", "")
                abstract = c.get("abstract", "")
                if title and abstract:
                    result[title] = abstract
            offset += len(notes)
            time.sleep(0.3)
        return result
