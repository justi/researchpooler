"""
Standalone helper script.

Parses COLT (Conference on Learning Theory) proceedings from
proceedings.mlr.press, creates list of dictionaries that store
information about each publication, and saves the result as a pickle
called pubs_colt.
"""

import urllib.request
from bs4 import BeautifulSoup
from repool_util import savePubs

COLT_VOLUMES = {
    19: 2011,
    23: 2012,
    30: 2013,
    35: 2014,
    40: 2015,
    49: 2016,
    65: 2017,
    75: 2018,
    99: 2019,
    125: 2020,
    134: 2021,
    178: 2022,
    195: 2023,
    247: 2024,
    291: 2025,
}

pubs = []
warnings = []

for vol, year in sorted(COLT_VOLUMES.items()):
    url = "https://proceedings.mlr.press/v%d/" % (vol,)
    print("downloading COLT %d (vol %d)..." % (year, vol))

    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as f:
            s = f.read()
    except Exception as e:
        print("error fetching vol %d: %s, skipping..." % (vol, e))
        continue

    print("done. Parsing...")
    soup = BeautifulSoup(s, 'html.parser')

    old_count = len(pubs)
    venue = 'COLT %d' % (year,)

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
        pubs.append(new_pub)

    print("read in %d publications for COLT %d." % (len(pubs) - old_count, year))

if len(warnings) > 0:
    print("%d warnings:" % (len(warnings),))
    for x in warnings:
        print(x)
else:
    print("No warnings generated.")

print("read in a total of %d publications." % (len(pubs),))
fname = "pubs_colt"
print("saving pickle in %s" % (fname,))
savePubs(fname, pubs)
print("all done.")
