"""
Standalone helper script.

Parses WACV proceedings from openaccess.thecvf.com, creates list of
dictionaries that store information about each publication, and saves
the result as a pickle in current directory called pubs_wacv.
"""

import urllib.request
from bs4 import BeautifulSoup
from repool_util import savePubs

BASE_URL = "https://openaccess.thecvf.com"


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as f:
        return f.read()


def get_pages_for_year(year):
    if year <= 2020:
        base = "%s/WACV%d.py" % (BASE_URL, year)
    else:
        base = "%s/WACV%d" % (BASE_URL, year)

    try:
        html = fetch(base + "?day=all")
        soup = BeautifulSoup(html, 'html.parser')
        if soup.find('dt', {'class': 'ptitle'}):
            return [html]
    except Exception:
        pass

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
    soup = BeautifulSoup(html, 'html.parser')
    results = []

    for dt in soup.find_all('dt', {'class': 'ptitle'}):
        new_pub = {}

        title_tag = dt.find('a')
        if not title_tag:
            continue

        new_pub['title'] = title_tag.text.strip()

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

for year in range(2020, 2027):
    print("downloading WACV %d..." % (year,))

    try:
        pages = get_pages_for_year(year)
    except Exception as e:
        print("error fetching year %d: %s, skipping..." % (year, e))
        continue

    if not pages:
        warnings.append("no pages found for WACV %d" % (year,))
        print("no data found, skipping...")
        continue

    venue = 'WACV %d' % (year,)
    old_count = len(pubs)

    for page_html in pages:
        pubs.extend(parse_papers(page_html, venue, year))

    print("read in %d publications for WACV %d." % (len(pubs) - old_count, year))

if len(warnings) > 0:
    print("%d warnings:" % (len(warnings),))
    for x in warnings:
        print(x)
else:
    print("No warnings generated.")

print("read in a total of %d publications." % (len(pubs),))
fname = "pubs_wacv"
print("saving pickle in %s" % (fname,))
savePubs(fname, pubs)
print("all done.")
