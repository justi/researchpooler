"""
Family-level scrapers shared by the *_download_parse.py entry points.

Two source families cover 22 of the venue scrapers:
- scrapePmlr:      proceedings.mlr.press volumes (COLT, ICML, CLeaR, ...)
- scrapeAnthology: aclanthology.org event pages (ACL, CoNLL, SemEval, ...)

Both are incremental and idempotent: already-scraped years are skipped,
already-known papers (title|||venue) are deduped, and existing entries -
including abstracts added later - are never touched. A per-venue entry point
is just a docstring plus one call with the venue's name/slug/first year.
"""

import urllib.request
from bs4 import BeautifulSoup
from repool_util import (savePubs, loadPubsIncremental, addPub,
                         discoverPmlrVolumes, scrapeYears)


def _fetch(url):
    """GET a page with a browser User-Agent; returns bytes."""
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as f:
        return f.read()


def _finish(pubs, warnings, fname):
    if len(warnings) > 0:
        print("%d warnings:" % (len(warnings),))
        for x in warnings:
            print(x)
    else:
        print("No warnings generated.")

    print("read in a total of %d publications." % (len(pubs),))
    print("saving pickle in %s" % (fname,))
    savePubs(fname, pubs)
    print("all done.")


def scrapePmlr(name):
    """
    Scrape every missing year of a PMLR-hosted venue.
    name: string as it appears both on the PMLR index ("Proceedings of
          <name> <year>") and in the venue field (e.g. "COLT", "CLeaR")
    """
    fname = "pubs_%s" % name.lower()
    volumes = discoverPmlrVolumes(name)
    pubs, existing_keys, existing_years = loadPubsIncremental(fname)
    warnings = []

    for vol, year in sorted(volumes.items()):
        if year in existing_years:
            continue
        url = "https://proceedings.mlr.press/v%d/" % (vol,)
        print("downloading %s %d (vol %d)..." % (name, year, vol))

        try:
            s = _fetch(url)
        except Exception as e:
            print("error fetching vol %d: %s, skipping..." % (vol, e))
            continue

        print("done. Parsing...")
        soup = BeautifulSoup(s, 'html.parser')

        old_count = len(pubs)
        venue = '%s %d' % (name, year)

        for paper_div in soup.find_all('div', {'class': 'paper'}):
            new_pub = {}

            title_tag = paper_div.find('p', {'class': 'title'})
            if not title_tag:
                continue

            new_pub['title'] = title_tag.text.strip()

            authors_tag = paper_div.find('span', {'class': 'authors'})
            if authors_tag:
                authors_text = authors_tag.get_text()
                authors = [a.strip().rstrip(';').strip() for a in authors_text.split(',')]
                new_pub['authors'] = [a for a in authors if a]

            links_tag = paper_div.find('p', {'class': 'links'})
            if links_tag:
                for a in links_tag.find_all('a'):
                    if 'Download PDF' in a.text:
                        new_pub['pdf'] = a['href']
                        break

            new_pub['venue'] = venue
            new_pub['year'] = year
            addPub(pubs, existing_keys, new_pub)

        print("read in %d publications for %s %d." % (len(pubs) - old_count, name, year))

    _finish(pubs, warnings, fname)


def scrapeAnthology(slug, name, first_year):
    """
    Scrape every missing year of an ACL-Anthology-hosted venue.
    slug: event-page slug ("conll" -> /events/conll-2026/)
    name: display/venue name (e.g. "CoNLL")
    first_year: earliest edition available on aclanthology.org
    """
    fname = "pubs_%s" % slug
    pubs, existing_keys, existing_years = loadPubsIncremental(fname)
    warnings = []

    for year in scrapeYears(first_year):
        if year in existing_years:
            continue
        url = "https://aclanthology.org/events/%s-%d/" % (slug, year)
        print("downloading %s %d..." % (name, year))

        try:
            s = _fetch(url)
        except Exception as e:
            print("error fetching year %d: %s, skipping..." % (year, e))
            continue

        print("done. Parsing...")
        soup = BeautifulSoup(s, 'html.parser')

        venue = '%s %d' % (name, year)
        old_count = len(pubs)

        for strong in soup.find_all('strong'):
            a = strong.find('a', class_='align-middle')
            if not a:
                continue

            title = a.text.strip()
            if not title:
                continue

            # skip proceedings headers / reports
            href = a.get('href', '')
            if href.endswith('.0/') or 'report' in href:
                continue

            new_pub = {'title': title}

            # authors are <a href="/people/..."> in the parent <span>
            span = strong.parent
            if span:
                authors = []
                for author_a in span.find_all('a'):
                    author_href = author_a.get('href', '')
                    if '/people/' in author_href:
                        authors.append(author_a.text.strip())
                if authors:
                    new_pub['authors'] = authors

                # PDF link - look in the surrounding div
                container = span.parent
                if container:
                    pdf_a = container.find('a', {'title': 'Open PDF'})
                    if pdf_a:
                        new_pub['pdf'] = pdf_a['href']

            new_pub['venue'] = venue
            new_pub['year'] = year
            addPub(pubs, existing_keys, new_pub)

        print("read in %d publications for %s %d." % (len(pubs) - old_count, name, year))

    _finish(pubs, warnings, fname)
