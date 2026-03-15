"""
Standalone helper script.

Parses NAACL proceedings from aclanthology.org, creates list of
dictionaries that store information about each publication, and saves
the result as a pickle called pubs_naacl.
"""

import urllib.request
from bs4 import BeautifulSoup
from repool_util import savePubs

BASE_URL = "https://aclanthology.org"

pubs = []
warnings = []

for year in range(2000, 2026):
    url = "%s/events/naacl-%d/" % (BASE_URL, year)
    print("downloading NAACL %d..." % (year,))

    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as f:
            s = f.read()
    except Exception as e:
        print("  skipping (no proceedings): %s" % str(e)[:60])
        continue

    print("done. Parsing...")
    soup = BeautifulSoup(s, 'html.parser')

    venue = 'NAACL %d' % (year,)
    old_count = len(pubs)

    for strong in soup.find_all('strong'):
        a = strong.find('a', class_='align-middle')
        if not a:
            continue

        title = a.text.strip()
        if not title:
            continue

        href = a.get('href', '')
        if href.endswith('.0/') or 'report' in href:
            continue

        new_pub = {'title': title}

        span = strong.parent
        if span:
            authors = []
            for author_a in span.find_all('a'):
                author_href = author_a.get('href', '')
                if '/people/' in author_href:
                    authors.append(author_a.text.strip())
            if authors:
                new_pub['authors'] = authors

            container = span.parent
            if container:
                pdf_a = container.find('a', {'title': 'Open PDF'})
                if pdf_a:
                    new_pub['pdf'] = pdf_a['href']

        new_pub['venue'] = venue
        new_pub['year'] = year
        pubs.append(new_pub)

    count = len(pubs) - old_count
    if count > 0:
        print("read in %d publications for NAACL %d." % (count, year))
    else:
        print("  no papers found.")

if len(warnings) > 0:
    print("%d warnings:" % (len(warnings),))
    for x in warnings:
        print(x)
else:
    print("No warnings generated.")

print("read in a total of %d publications." % (len(pubs),))
fname = "pubs_naacl"
print("saving pickle in %s" % (fname,))
savePubs(fname, pubs)
print("all done.")
