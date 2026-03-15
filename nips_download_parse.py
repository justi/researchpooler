"""
Standalone helper script.

Parses NeurIPS proceedings, creates list of dictionaries
that store information about each publication, and saves the result as a
pickle in current directory called pubs_nips.
"""

import urllib.request
from bs4 import BeautifulSoup
from repool_util import savePubs

pubs = []
warnings = []

for year in range(2006, 2024):
    url = "https://proceedings.neurips.cc/paper_files/paper/%d" % (year,)
    print("downloading proceedings from NeurIPS year %d..." % (year,))

    try:
        with urllib.request.urlopen(url) as f:
            s = f.read()
    except Exception as e:
        print("error fetching year %d: %s, skipping..." % (year, e))
        continue

    print("done. Parsing...")
    soup = BeautifulSoup(s, 'html.parser')

    publication_section = soup.find('div', {'class': 'container-fluid'})
    if not publication_section:
        warnings.append("no publication section found for year %d" % (year,))
        continue

    venue = 'NeurIPS %d' % (year,)
    old_count = len(pubs)

    for entry in publication_section.find_all('li', {'class': 'none'}):
        new_pub = {}

        title_tag = entry.find('a', {'title': 'paper title'})
        if title_tag:
            new_pub['title'] = title_tag.text.strip()

        authors_tag = entry.find('i')
        if authors_tag:
            authors = authors_tag.text.strip().split(',')
            new_pub['authors'] = [author.strip() for author in authors]

        if new_pub:
            new_pub['venue'] = venue
            new_pub['year'] = year
            pubs.append(new_pub)

    print("read in %d publications for year %d." % (len(pubs) - old_count, year))

# show warnings, if any were generated
if len(warnings) > 0:
    print("%d warnings:" % (len(warnings),))
    for x in warnings:
        print(x)
else:
    print("No warnings generated.")

# finally, save pickle as output
print("read in a total of %d publications." % (len(pubs),))
fname = "pubs_nips"
print("saving pickle in %s" % (fname,))
savePubs(fname, pubs)
print("all done.")
