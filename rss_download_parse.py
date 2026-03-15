"""
Standalone helper script.

Parses RSS (Robotics: Science and Systems) proceedings from
roboticsproceedings.org, creates list of dictionaries that store
information about each publication, and saves the result as a pickle
in current directory called pubs_rss.
"""

import urllib.request
from bs4 import BeautifulSoup
from repool_util import savePubs

BASE_URL = "https://www.roboticsproceedings.org"

# RSS I (2005) through RSS XXI (2025)
RSS_EDITIONS = {}
for n in range(1, 22):
    year = 2004 + n
    key = "rss%02d" % n
    RSS_EDITIONS[key] = year

pubs = []
warnings = []

for edition, year in sorted(RSS_EDITIONS.items(), key=lambda x: x[1]):
    url = "%s/%s/index.html" % (BASE_URL, edition)
    print("downloading RSS %d (%s)..." % (year, edition))

    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as f:
            s = f.read()
    except Exception as e:
        print("error fetching %s: %s, skipping..." % (edition, e))
        continue

    print("done. Parsing...")
    soup = BeautifulSoup(s, 'html.parser')

    old_count = len(pubs)
    venue = "RSS %d" % year

    content_div = soup.find('div', {'class': 'content'})
    if not content_div:
        warnings.append("no content div found for %s" % edition)
        continue

    table = content_div.find('table')
    if not table:
        warnings.append("no table found for %s" % edition)
        continue

    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        if not tds:
            continue

        first_td = tds[0]

        # skip spacer rows
        text = first_td.get_text(strip=True)
        if not text or text == '\xa0' or text == '&nbsp':
            continue

        title_tag = first_td.find('a')
        if not title_tag:
            continue

        new_pub = {}
        new_pub['title'] = title_tag.get_text(strip=True)

        authors_tag = first_td.find('i')
        if authors_tag:
            authors_text = authors_tag.get_text()
            authors = [a.strip() for a in authors_text.split(',')]
            new_pub['authors'] = [a for a in authors if a]

        # PDF link is in the second td
        if len(tds) > 1:
            pdf_tag = tds[1].find('a')
            if pdf_tag and pdf_tag.get('href'):
                pdf_href = pdf_tag['href']
                if not pdf_href.startswith('http'):
                    pdf_href = "%s/%s/%s" % (BASE_URL, edition, pdf_href)
                new_pub['pdf'] = pdf_href

        new_pub['venue'] = venue
        new_pub['year'] = year
        pubs.append(new_pub)

    print("read in %d publications for RSS %d." % (len(pubs) - old_count, year))

if len(warnings) > 0:
    print("%d warnings:" % (len(warnings),))
    for x in warnings:
        print(x)
else:
    print("No warnings generated.")

print("read in a total of %d publications." % (len(pubs),))
fname = "pubs_rss"
print("saving pickle in %s" % (fname,))
savePubs(fname, pubs)
print("all done.")
