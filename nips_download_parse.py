"""
Standalone helper script.

Parses NeurIPS proceedings, creates list of dictionaries
that store information about each publication, and saves the result as a
pickle in current directory called pubs_nips.
"""

import urllib.request
from datetime import datetime
from bs4 import BeautifulSoup
from repool_util import savePubs

pubs = []
warnings = []

for year in range(2006, datetime.now().year + 1):
    url = "https://proceedings.neurips.cc/paper_files/paper/%d" % (year,)
    print("downloading proceedings from NeurIPS year %d..." % (year,))

    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=30) as f:
            s = f.read()
    except Exception as e:
        print("error fetching year %d: %s, skipping..." % (year, e))
        continue

    print("done. Parsing...")
    soup = BeautifulSoup(s, 'html.parser')

    paper_list = soup.find('ul', {'class': 'paper-list'})
    if not paper_list:
        warnings.append("no paper-list found for year %d" % (year,))
        continue

    venue = 'NeurIPS %d' % (year,)
    old_count = len(pubs)

    for entry in paper_list.find_all('li'):
        new_pub = {}

        title_tag = entry.find('a', {'title': 'paper title'})
        if not title_tag:
            continue

        new_pub['title'] = title_tag.text.strip()
        page_url = 'https://proceedings.neurips.cc' + title_tag['href']
        new_pub['url'] = page_url
        # Convert abstract page URL to direct PDF URL (handles multiple formats)
        pdf_url = page_url
        for abstract_suffix, paper_suffix in [
            ('-Abstract-Conference.html', '-Paper-Conference.pdf'),
            ('-Abstract-Datasets_and_Benchmarks.html', '-Paper-Datasets_and_Benchmarks.pdf'),
            ('-Abstract.html', '-Paper.pdf'),
        ]:
            if abstract_suffix in pdf_url:
                pdf_url = pdf_url.replace(abstract_suffix, paper_suffix).replace('/hash/', '/file/')
                break
        new_pub['pdf'] = pdf_url

        authors_tag = entry.find('span', {'class': 'paper-authors'})
        if authors_tag:
            authors = authors_tag.text.strip().split(',')
            new_pub['authors'] = [author.strip() for author in authors]

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
