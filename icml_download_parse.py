"""
Standalone helper script.

Parses ICML proceedings from proceedings.mlr.press, creates list of
dictionaries that store information about each publication, and saves
the result as a pickle in current directory called pubs_icml.
"""

import urllib.request
from bs4 import BeautifulSoup
from repool_util import savePubs

# ICML volume numbers mapped to years
ICML_VOLUMES = {
    28: 2013,
    32: 2014,
    37: 2015,
    48: 2016,
    70: 2017,
    80: 2018,
    97: 2019,
    119: 2020,
    139: 2021,
    162: 2022,
    202: 2023,
    235: 2024,
    267: 2025,
}

pubs = []
warnings = []

for vol, year in sorted(ICML_VOLUMES.items()):
    url = "https://proceedings.mlr.press/v%d/" % (vol,)
    print("downloading ICML %d (vol %d)..." % (year, vol))

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
    venue = 'ICML %d' % (year,)

    for paper_div in soup.find_all('div', {'class': 'paper'}):
        new_pub = {}

        title_tag = paper_div.find('p', {'class': 'title'})
        if not title_tag:
            continue

        new_pub['title'] = title_tag.text.strip()

        authors_tag = paper_div.find('span', {'class': 'authors'})
        if authors_tag:
            # authors separated by &nbsp; in HTML, but .text gives us the text
            authors_text = authors_tag.get_text()
            authors = [a.strip() for a in authors_text.split(',')]
            # clean up trailing semicolons
            authors = [a.rstrip(';').strip() for a in authors if a.strip()]
            new_pub['authors'] = authors

        # find PDF link
        links_tag = paper_div.find('p', {'class': 'links'})
        if links_tag:
            for a in links_tag.find_all('a'):
                if 'Download PDF' in a.text:
                    new_pub['pdf'] = a['href']
                    break

        new_pub['venue'] = venue
        new_pub['year'] = year
        pubs.append(new_pub)

    print("read in %d publications for ICML %d." % (len(pubs) - old_count, year))

# show warnings, if any were generated
if len(warnings) > 0:
    print("%d warnings:" % (len(warnings),))
    for x in warnings:
        print(x)
else:
    print("No warnings generated.")

# finally, save pickle as output
print("read in a total of %d publications." % (len(pubs),))
fname = "pubs_icml"
print("saving pickle in %s" % (fname,))
savePubs(fname, pubs)
print("all done.")
