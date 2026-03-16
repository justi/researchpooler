"""
Standalone helper script.

Parses ICLR (International Conference on Learning Representations) proceedings
from the OpenReview API, creates list of dictionaries that store information
about each publication, and saves the result as a pickle in the current
directory called pubs_iclr.

Uses two OpenReview API versions:
  - API v2 (api2.openreview.net) for 2024 onwards
  - API v1 (api.openreview.net)  for 2018-2023

For 2021-2023, accepted papers have a venue field that can be filtered on.
For 2018-2020, accepted papers must be identified through decision/meta-review
replies attached to each blind submission.
"""

import urllib.request
import urllib.parse
import json
import time
from repool_util import savePubs

OPENREVIEW_V1 = "https://api.openreview.net"
OPENREVIEW_V2 = "https://api2.openreview.net"
HEADERS = {'User-Agent': 'Mozilla/5.0'}
PAGE_SIZE = 1000


def fetch_json(url):
    """Fetch a URL and return parsed JSON."""
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as f:
        return json.loads(f.read())


# --------------------------------------------------------------------------
# API v2 fetcher (2024+)
# --------------------------------------------------------------------------

def fetch_iclr_v2(year):
    """
    Fetch accepted ICLR papers for a given year using the OpenReview API v2.
    Returns a list of pub dicts.
    """
    pubs = []
    offset = 0

    while True:
        url = (
            "%s/notes?content.venueid=ICLR.cc/%d/Conference"
            "&limit=%d&offset=%d"
            % (OPENREVIEW_V2, year, PAGE_SIZE, offset)
        )
        data = fetch_json(url)
        notes = data.get('notes', [])
        if not notes:
            break

        for note in notes:
            c = note.get('content', {})
            title_val = c.get('title', {}).get('value', '')
            authors_val = c.get('authors', {}).get('value', [])
            pdf_val = c.get('pdf', {}).get('value', '')

            if not title_val:
                continue

            new_pub = {
                'title': title_val,
                'authors': list(authors_val),
                'venue': 'ICLR %d' % year,
                'year': year,
            }
            if pdf_val:
                if pdf_val.startswith('/'):
                    pdf_val = 'https://openreview.net' + pdf_val
                new_pub['pdf'] = pdf_val

            pubs.append(new_pub)

        offset += len(notes)
        time.sleep(0.2)

    return pubs


# --------------------------------------------------------------------------
# API v1 fetcher with venue filter (2021-2023)
# --------------------------------------------------------------------------

# Accepted venue strings by year. Case and wording vary across years.
VENUE_FILTERS = {
    2021: ['ICLR 2021 Poster', 'ICLR 2021 Oral', 'ICLR 2021 Spotlight'],
    2022: ['ICLR 2022 Poster', 'ICLR 2022 Oral', 'ICLR 2022 Spotlight'],
    2023: ['ICLR 2023 poster', 'ICLR 2023 oral',
           'ICLR 2023 notable top 5%', 'ICLR 2023 notable top 25%'],
}


def fetch_iclr_v1_venue(year):
    """
    Fetch accepted ICLR papers for years where API v1 blind submissions
    contain a venue field (2021-2023). Returns a list of pub dicts.
    """
    pubs = []
    venue_strings = VENUE_FILTERS.get(year, [])
    invitation = "ICLR.cc/%d/Conference/-/Blind_Submission" % year

    for venue_str in venue_strings:
        offset = 0
        while True:
            encoded_venue = urllib.parse.quote(venue_str)
            url = (
                "%s/notes?invitation=%s"
                "&content.venue=%s"
                "&limit=%d&offset=%d"
                % (OPENREVIEW_V1, invitation, encoded_venue, PAGE_SIZE, offset)
            )
            data = fetch_json(url)
            notes = data.get('notes', [])
            if not notes:
                break

            for note in notes:
                c = note.get('content', {})
                title = c.get('title', '')
                authors = c.get('authors', [])
                pdf = c.get('pdf', '')

                if not title:
                    continue

                new_pub = {
                    'title': title,
                    'authors': list(authors),
                    'venue': 'ICLR %d' % year,
                    'year': year,
                }
                if pdf:
                    if pdf.startswith('/'):
                        pdf = 'https://openreview.net' + pdf
                    new_pub['pdf'] = pdf

                pubs.append(new_pub)

            offset += len(notes)
            time.sleep(0.2)

    return pubs


# --------------------------------------------------------------------------
# API v1 fetcher with decision lookup (2018-2020)
# --------------------------------------------------------------------------

def fetch_iclr_v1_decisions(year):
    """
    Fetch accepted ICLR papers for years where blind submissions lack a
    venue field (2018-2020). We fetch all submissions with their direct
    replies and check the decision/meta-review for acceptance.

    For 2018, the acceptance decision is stored in a reply with a 'decision'
    content field. For 2019, it is in a 'recommendation' field from the
    meta-review. For 2020, it is in a 'decision' field in a Decision reply.

    Returns a list of pub dicts.
    """
    pubs = []
    invitation = "ICLR.cc/%d/Conference/-/Blind_Submission" % year
    offset = 0
    total_checked = 0

    while True:
        url = (
            "%s/notes?invitation=%s"
            "&details=directReplies"
            "&limit=%d&offset=%d"
            % (OPENREVIEW_V1, invitation, PAGE_SIZE, offset)
        )
        data = fetch_json(url)
        notes = data.get('notes', [])
        if not notes:
            break

        for note in notes:
            total_checked += 1
            accepted = False
            replies = note.get('details', {}).get('directReplies', [])
            for reply in replies:
                rc = reply.get('content', {})
                decision = rc.get('decision', '') or rc.get('recommendation', '')
                if 'Accept' in decision and 'Workshop' not in decision:
                    accepted = True
                    break

            if not accepted:
                continue

            c = note.get('content', {})
            title = c.get('title', '')
            authors = c.get('authors', [])
            pdf = c.get('pdf', '')

            if not title:
                continue

            new_pub = {
                'title': title,
                'authors': list(authors),
                'venue': 'ICLR %d' % year,
                'year': year,
            }
            if pdf:
                if pdf.startswith('/'):
                    pdf = 'https://openreview.net' + pdf
                new_pub['pdf'] = pdf

            pubs.append(new_pub)

        offset += len(notes)
        time.sleep(0.3)

    return pubs


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

pubs = []
warnings = []

for year in range(2018, 2026):
    print("downloading proceedings from ICLR %d..." % year)

    try:
        if year >= 2024:
            year_pubs = fetch_iclr_v2(year)
        elif year >= 2021:
            year_pubs = fetch_iclr_v1_venue(year)
        else:
            year_pubs = fetch_iclr_v1_decisions(year)
    except Exception as e:
        warnings.append("error fetching ICLR %d: %s" % (year, e))
        print("  error: %s, skipping..." % e)
        continue

    if not year_pubs:
        warnings.append("no papers found for ICLR %d" % year)
        print("  no papers found, skipping...")
    else:
        print("  read in %d publications for ICLR %d." % (len(year_pubs), year))

    pubs.extend(year_pubs)

# show warnings, if any were generated
if len(warnings) > 0:
    print("%d warnings:" % len(warnings))
    for x in warnings:
        print(x)
else:
    print("No warnings generated.")

# finally, save pickle as output
print("read in a total of %d publications." % len(pubs))
fname = "pubs_iclr"
print("saving pickle in %s" % fname)
savePubs(fname, pubs)
print("all done.")
