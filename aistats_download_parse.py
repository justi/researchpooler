"""
Standalone helper script.

Parses AISTATS proceedings from proceedings.mlr.press, creates list of
dictionaries that store information about each publication, and saves
the result as a pickle in current directory called pubs_aistats.
"""

import urllib.request
from bs4 import BeautifulSoup
from repool_util import savePubs, loadPubsIncremental, addPub, discoverPmlrVolumes

AISTATS_VOLUMES = discoverPmlrVolumes("AISTATS")

pubs, existing_keys, existing_years = loadPubsIncremental("pubs_aistats")
warnings = []

for vol, year in sorted(AISTATS_VOLUMES.items()):
    url = "https://proceedings.mlr.press/v%d/" % (vol,)
    print("downloading AISTATS %d (vol %d)..." % (year, vol))

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
    venue = 'AISTATS %d' % (year,)

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

    print("read in %d publications for AISTATS %d." % (len(pubs) - old_count, year))

if len(warnings) > 0:
    print("%d warnings:" % (len(warnings),))
    for x in warnings:
        print(x)
else:
    print("No warnings generated.")

print("read in a total of %d publications." % (len(pubs),))
fname = "pubs_aistats"
print("saving pickle in %s" % (fname,))
savePubs(fname, pubs)
print("all done.")
