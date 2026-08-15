"""
Standalone helper script.

Parses CLeaR (Causal Learning and Reasoning) proceedings from
proceedings.mlr.press, creates list of dictionaries that store information
about each publication, and saves the result as a pickle in current directory
called pubs_clear.

Volumes are DISCOVERED at runtime from the PMLR index (the same
"Volume NNN ... Proceedings of CLeaR YYYY" listing the research-explorer
freshness probe parses) - no hardcoded volume/year map, so a new year is picked
up as soon as PMLR lists it. Incremental: loads the existing pubs_clear and
only fetches years not present yet, so re-runs never drop earlier years.
"""

import urllib.request
from bs4 import BeautifulSoup
from repool_util import savePubs, loadPubsIncremental, discoverPmlrVolumes

CLEAR_VOLUMES = discoverPmlrVolumes("CLeaR")

pubs, existing_keys, existing_years = loadPubsIncremental("pubs_clear")
warnings = []

for vol, year in sorted(CLEAR_VOLUMES.items()):
    if year in existing_years:
        continue
    url = "https://proceedings.mlr.press/v%d/" % (vol,)
    print("downloading CLeaR %d (vol %d)..." % (year, vol))

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
    venue = 'CLeaR %d' % (year,)

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

    print("read in %d publications for CLeaR %d." % (len(pubs) - old_count, year))

if len(warnings) > 0:
    print("%d warnings:" % (len(warnings),))
    for x in warnings:
        print(x)
else:
    print("No warnings generated.")

print("read in a total of %d publications." % (len(pubs),))
fname = "pubs_clear"
print("saving pickle in %s" % (fname,))
savePubs(fname, pubs)
print("all done.")
