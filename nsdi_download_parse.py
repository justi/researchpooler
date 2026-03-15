"""
Standalone helper script.

Parses NSDI (Networked Systems Design and Implementation) proceedings from
usenix.org, creates list of dictionaries that store information about each
publication, and saves the result as a pickle called pubs_nsdi.

NSDI is held annually. The USENIX site has parseable technical-sessions
pages from 2012 onward.
"""

import urllib.request
import re
import time
from bs4 import BeautifulSoup
from repool_util import savePubs

BASE_URL = "https://www.usenix.org"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120.0.0.0 Safari/537.36")

# NSDI years with parseable technical-sessions pages on usenix.org.
NSDI_YEARS = list(range(2012, 2026))

# Delay between HTTP requests (seconds) to avoid rate-limiting.
REQUEST_DELAY = 4

pubs = []
warnings = []


def parse_authors_from_field(field_div):
    """
    Extract author names from a paper-people-text or presented-by field div.
    Affiliations are wrapped in <em> tags, so we remove those first.
    Author groups are separated by semicolons; authors within a group
    are separated by commas and 'and'.
    """
    if field_div is None:
        return []

    field_item = field_div.find('div', class_='field-item')
    if field_item is None:
        field_item = field_div

    # Remove <em> tags (affiliations) from a copy
    import copy
    fi = copy.copy(field_item)
    for em in fi.find_all('em'):
        em.decompose()

    text = fi.get_text()
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = text.replace('\xa0', ' ')  # non-breaking spaces

    # Split by semicolons (group separator), then handle commas and 'and'
    groups = text.split(';')
    authors = []
    for group in groups:
        group = group.strip()
        if not group:
            continue
        group = group.replace(' and ', ', ')
        parts = [p.strip() for p in group.split(',')]
        for p in parts:
            p = p.strip()
            if p and len(p) > 1:
                authors.append(p)
    return authors


for year in NSDI_YEARS:
    slug = "nsdi%d" % (year % 100)
    url = "%s/conference/%s/technical-sessions" % (BASE_URL, slug)
    venue = "NSDI %d" % year
    print("downloading %s..." % venue)

    req = urllib.request.Request(url, headers={'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as f:
            s = f.read()
    except Exception as e:
        warnings.append("error fetching %s: %s" % (venue, e))
        print("error fetching %s: %s, skipping..." % (venue, e))
        time.sleep(REQUEST_DELAY)
        continue

    print("done. Parsing...")
    soup = BeautifulSoup(s, 'html.parser')

    old_count = len(pubs)

    # Papers are in elements (article or div) with class 'node-paper'.
    papers = soup.find_all(class_='node-paper')

    for paper in papers:
        # Title is in an h2 tag containing an <a> link
        h2 = paper.find('h2')
        if not h2:
            continue
        a = h2.find('a')
        if not a:
            continue

        href = a.get('href', '')
        title = a.get_text(strip=True)
        if not title:
            continue

        # Skip non-NSDI entries (e.g. joint keynotes)
        if '/conference/' in href and ('/%s/' % slug) not in href:
            continue

        # Skip keynotes, opening remarks, etc.
        if 'keynote' in href.lower() or 'opening-remarks' in href.lower():
            continue

        new_pub = {'title': title}

        # Authors: look for field-paper-people-text first, then field-presented-by
        author_div = paper.find(
            'div', class_=re.compile(r'field-name-field-paper-people-text'))
        if not author_div:
            author_div = paper.find(
                'div', class_=re.compile(r'field-name-field-presented-by'))

        authors = parse_authors_from_field(author_div)
        if authors:
            new_pub['authors'] = authors

        # PDF link from the media section
        pdf_span = paper.find('span', class_='pdf')
        if pdf_span:
            pdf_a = pdf_span.find('a')
            if pdf_a and pdf_a.get('href'):
                pdf_href = pdf_a['href']
                if not pdf_href.startswith('http'):
                    pdf_href = BASE_URL + pdf_href
                new_pub['pdf'] = pdf_href

        new_pub['venue'] = venue
        new_pub['year'] = year
        pubs.append(new_pub)

    print("read in %d publications for %s." % (len(pubs) - old_count, venue))
    time.sleep(REQUEST_DELAY)

# show warnings
if len(warnings) > 0:
    print("%d warnings:" % (len(warnings),))
    for x in warnings:
        print(x)
else:
    print("No warnings generated.")

print("read in a total of %d publications." % (len(pubs),))
fname = "pubs_nsdi"
print("saving pickle in %s" % (fname,))
savePubs(fname, pubs)
print("all done.")
