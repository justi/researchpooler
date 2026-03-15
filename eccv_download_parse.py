"""
Standalone helper script.

Parses ECCV proceedings from ecva.net/papers.php, creates list of
dictionaries that store information about each publication, and saves
the result as a pickle in current directory called pubs_eccv.

ECCV occurs every 2 years (even years only).
"""

import urllib.request
import re
from bs4 import BeautifulSoup
from repool_util import savePubs

BASE_URL = "https://www.ecva.net"
PAPERS_URL = BASE_URL + "/papers.php"


def fetch(url):
    """Fetch a URL and return the HTML as bytes."""
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as f:
        return f.read()


def parse_authors(raw_text):
    """
    Parse author string into a list of author names.
    ECCV 2018 uses 'Last, First and Last, First' format.
    ECCV 2020+ uses 'First Last, First Last' format.
    """
    raw = raw_text.strip()
    if not raw:
        return []

    # Remove trailing/leading whitespace and asterisks (corresponding author markers)
    raw = raw.replace('*', '').strip()

    # 2018 format: "Ling, Yonggen and Bao, Linchao and Jie, Zequn"
    # Detect by checking if the string uses " and " as separator between
    # "Last, First" pairs
    if ' and ' in raw and ', ' in raw:
        parts = [p.strip() for p in raw.split(' and ')]
        authors = []
        for part in parts:
            # "Last, First" -> "First Last"
            if ', ' in part:
                pieces = part.split(', ', 1)
                authors.append(pieces[1].strip() + ' ' + pieces[0].strip())
            else:
                authors.append(part.strip())
        return [a for a in authors if a]

    # 2020+ format: "First Last, First Last, First Last"
    authors = [a.strip() for a in raw.split(',')]
    return [a for a in authors if a]


def parse_papers_from_section(section_html, year):
    """Parse papers from a single year section. Returns list of pub dicts."""
    soup = BeautifulSoup(section_html, 'html.parser')
    results = []
    venue = 'ECCV %d' % (year,)

    for dt in soup.find_all('dt', {'class': 'ptitle'}):
        new_pub = {}

        title_tag = dt.find('a')
        if not title_tag:
            continue

        new_pub['title'] = title_tag.text.strip()

        # Collect authors and PDF from sibling <dd> elements
        authors = []
        for dd in dt.find_next_siblings('dd'):
            # Stop if we hit another ptitle's dd
            if dd.find_previous_sibling('dt', {'class': 'ptitle'}) != dt:
                break

            # First dd typically contains authors as text
            if not authors:
                author_text = dd.get_text(separator=' ').strip()
                # Skip if this dd contains links (it's the PDF dd)
                if author_text and not dd.find('a'):
                    authors = parse_authors(author_text)

            # Look for PDF link
            for a in dd.find_all('a'):
                href = a.get('href', '')
                if href.endswith('.pdf') and 'supp' not in href.lower():
                    if href.startswith('http'):
                        new_pub['pdf'] = href
                    else:
                        new_pub['pdf'] = BASE_URL + '/' + href.lstrip('/')
                    break

        if authors:
            new_pub['authors'] = authors

        new_pub['venue'] = venue
        new_pub['year'] = year
        results.append(new_pub)

    return results


# Fetch the single page containing all years
print("downloading ecva.net papers page...")
try:
    html = fetch(PAPERS_URL).decode('utf-8')
except Exception as e:
    print("error fetching papers page: %s" % (e,))
    raise SystemExit(1)

pubs = []
warnings = []

for year in range(2018, 2026, 2):  # even years only
    print("parsing ECCV %d..." % (year,))

    # Find the accordion section for this year
    pattern = r'ECCV\s+%d\s+Papers\s*</button>\s*<div[^>]*>\s*<div[^>]*>\s*<dl>(.*?)</dl>' % (year,)
    match = re.search(pattern, html, re.DOTALL)

    if not match:
        # Try a looser pattern
        marker = 'ECCV %d Papers' % (year,)
        start_idx = html.find(marker)
        if start_idx == -1:
            warnings.append("no section found for ECCV %d" % (year,))
            print("no data found, skipping...")
            continue

        # Find the <dl> after this marker
        dl_start = html.find('<dl>', start_idx)
        dl_end = html.find('</dl>', dl_start)
        if dl_start == -1 or dl_end == -1:
            warnings.append("could not find <dl> block for ECCV %d" % (year,))
            print("no data found, skipping...")
            continue

        section_html = html[dl_start:dl_end + 5]
    else:
        section_html = '<dl>' + match.group(1) + '</dl>'

    old_count = len(pubs)
    pubs.extend(parse_papers_from_section(section_html, year))
    print("read in %d publications for ECCV %d." % (len(pubs) - old_count, year))

# Show warnings
if len(warnings) > 0:
    print("%d warnings:" % (len(warnings),))
    for x in warnings:
        print(x)
else:
    print("No warnings generated.")

print("read in a total of %d publications." % (len(pubs),))
fname = "pubs_eccv"
print("saving pickle in %s" % (fname,))
savePubs(fname, pubs)
print("all done.")
