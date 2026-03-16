"""
Standalone helper script.

Parses CVPR proceedings from openaccess.thecvf.com, creates list of
dictionaries that store information about each publication, and saves
the result as a pickle in current directory called pubs_cvpr.
"""

import urllib.request
from bs4 import BeautifulSoup
from repool_util import savePubs

BASE_URL = "https://openaccess.thecvf.com"


def fetch(url):
    """Fetch a URL and return the response body as bytes, or None on error.

    Note: returns bytes (not str). BeautifulSoup handles both bytes and str,
    so callers can pass the result directly to BeautifulSoup.
    """
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as f:
        return f.read()


def get_pages_for_year(year):
    """Return list of HTML pages to parse for a given CVPR year."""
    # determine base URL pattern
    if year <= 2020:
        base = "%s/CVPR%d.py" % (BASE_URL, year)
    else:
        base = "%s/CVPR%d" % (BASE_URL, year)

    # first try day=all
    try:
        html = fetch(base + "?day=all")
        soup = BeautifulSoup(html, 'html.parser')
        # check if it actually has papers (not a DB error)
        if soup.find('dt', {'class': 'ptitle'}):
            return [html]
    except Exception:
        pass

    # fall back to fetching the index page and finding day links
    try:
        html = fetch(base)
        soup = BeautifulSoup(html, 'html.parser')
        pages = []
        for a in soup.find_all('a'):
            href = a.get('href', '')
            if 'day=' in href and 'day=all' not in href:
                day_url = BASE_URL + '/' + href.lstrip('/')
                try:
                    pages.append(fetch(day_url))
                except Exception:
                    pass
        if pages:
            return pages
    except Exception:
        pass

    return []


def parse_papers(html, venue, year):
    """Parse papers from a single HTML page. Returns list of pub dicts."""
    soup = BeautifulSoup(html, 'html.parser')
    results = []

    for dt in soup.find_all('dt', {'class': 'ptitle'}):
        new_pub = {}

        title_tag = dt.find('a')
        if not title_tag:
            continue

        new_pub['title'] = title_tag.text.strip()

        # collect authors and PDF from sibling <dd> elements
        authors = []
        for dd in dt.find_next_siblings('dd'):
            if dd.find_previous_sibling('dt', {'class': 'ptitle'}) != dt:
                break

            for form in dd.find_all('form', {'class': 'authsearch'}):
                author_input = form.find('input', {'name': 'query_author'})
                if not author_input:
                    author_input = form.find('input', {'name': 'query'})
                if author_input:
                    authors.append(author_input['value'])

            for a in dd.find_all('a'):
                href = a.get('href', '')
                if href.endswith('.pdf') and 'supp' not in href.lower():
                    new_pub['pdf'] = BASE_URL + '/' + href.lstrip('/')
                    break

        if authors:
            new_pub['authors'] = authors

        new_pub['venue'] = venue
        new_pub['year'] = year
        results.append(new_pub)

    return results


pubs = []
warnings = []

for year in range(2013, 2026):
    print("downloading CVPR %d..." % (year,))

    try:
        pages = get_pages_for_year(year)
    except Exception as e:
        print("error fetching year %d: %s, skipping..." % (year, e))
        continue

    if not pages:
        warnings.append("no pages found for CVPR %d" % (year,))
        print("no data found, skipping...")
        continue

    venue = 'CVPR %d' % (year,)
    old_count = len(pubs)

    for page_html in pages:
        pubs.extend(parse_papers(page_html, venue, year))

    print("read in %d publications for CVPR %d." % (len(pubs) - old_count, year))

# show warnings
if len(warnings) > 0:
    print("%d warnings:" % (len(warnings),))
    for x in warnings:
        print(x)
else:
    print("No warnings generated.")

print("read in a total of %d publications." % (len(pubs),))
fname = "pubs_cvpr"
print("saving pickle in %s" % (fname,))
savePubs(fname, pubs)
print("all done.")
