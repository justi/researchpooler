"""
Standalone helper script.

Parses JMLR (Journal of Machine Learning Research) papers from
jmlr.org, creates list of dictionaries that store information about
each publication, and saves the result as a pickle called pubs_jmlr.
"""

import re
import urllib.request
from bs4 import BeautifulSoup, NavigableString
from repool_util import savePubs

BASE_URL = "https://jmlr.org"

# Volumes 1-26 cover years 2000-2025.
# The year is extracted from each paper's metadata rather than hardcoded,
# since the volume-to-year mapping is not perfectly regular (e.g. volumes
# 4 and 5 both correspond to 2003).
VOLUMES = list(range(1, 27))

pubs = []
warnings = []

for vol in VOLUMES:
    url = "%s/papers/v%d/" % (BASE_URL, vol)
    print("downloading JMLR volume %d..." % vol)

    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as f:
            s = f.read()
    except Exception as e:
        print("error fetching volume %d: %s, skipping..." % (vol, e))
        continue

    print("done. Parsing...")
    soup = BeautifulSoup(s, 'html.parser')

    old_count = len(pubs)

    for dl in soup.find_all('dl'):
        dt = dl.find('dt')
        dd = dl.find('dd')
        if not dt or not dd:
            continue

        # In older volumes, <dt> is not properly closed before <dd>,
        # so BeautifulSoup nests <dd> inside <dt>.  Extract only the
        # direct NavigableString children of <dt> to get the title.
        title = ''.join(
            s for s in dt.children if isinstance(s, NavigableString)
        ).strip()
        if not title:
            continue

        new_pub = {}
        new_pub['title'] = title

        # Parse authors from the bold/italic text inside dd.
        # The dd typically starts with <b><i>Author1, Author2</i></b>; ...
        dd_text = dd.get_text()

        # Authors appear before the semicolon
        author_part = dd_text.split(';')[0].strip() if ';' in dd_text else ''
        if author_part:
            authors = [a.strip() for a in author_part.split(',')]
            new_pub['authors'] = [a for a in authors if a]

        # Extract year from the metadata text after the semicolon.
        # The year appears at the end: ", 2024." -- match that to avoid
        # false positives from issue numbers like (2026) or paper IDs.
        year_match = re.search(r',\s*(20\d{2})\s*\.', dd_text)
        if year_match:
            new_pub['year'] = int(year_match.group(1))
        else:
            new_pub['year'] = 1999 + vol  # fallback estimate

        # Find PDF link
        for a in dd.find_all('a'):
            link_text = a.get_text(strip=True).lower()
            href = a.get('href', '')
            if 'pdf' in link_text or 'pdf' in href.lower():
                # Normalize the URL
                if href.startswith('http'):
                    new_pub['pdf'] = href
                elif href.startswith('/'):
                    new_pub['pdf'] = BASE_URL + href
                else:
                    new_pub['pdf'] = BASE_URL + '/papers/v%d/' % vol + href
                break

        new_pub['venue'] = 'JMLR %d' % new_pub['year']
        pubs.append(new_pub)

    added = len(pubs) - old_count
    print("read in %d publications for JMLR volume %d." % (added, vol))

    if added == 0:
        warnings.append("No papers found for volume %d" % vol)

if len(warnings) > 0:
    print("%d warnings:" % len(warnings))
    for x in warnings:
        print(x)
else:
    print("No warnings generated.")

print("read in a total of %d publications." % len(pubs))
fname = "pubs_jmlr"
print("saving pickle in %s" % fname)
savePubs(fname, pubs)
print("all done.")
