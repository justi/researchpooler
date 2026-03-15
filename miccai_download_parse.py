"""
Standalone helper script.

Parses MICCAI (Medical Image Computing and Computer Assisted Intervention)
proceedings from papers.miccai.org, creates list of dictionaries that store
information about each publication, and saves the result as a pickle in the
current directory called pubs_miccai.

As of writing, only MICCAI 2024 and 2025 are available on the site.
"""

import urllib.request
from bs4 import BeautifulSoup
from repool_util import savePubs

BASE_URL = "https://papers.miccai.org"


def fetch(url):
    """Fetch a URL and return the HTML as bytes."""
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as f:
        return f.read()


def parse_papers(html, year):
    """
    Parse papers from a MICCAI year page.

    Each paper entry is a <div class="posts-list-item"> containing:
      - A <b> tag with the paper title
      - Author <a> tags linking to /miccai-YYYY/tags#AuthorName
      - A PDF <a> tag linking to the paper PDF
    """
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    venue = 'MICCAI %d' % (year,)

    for div in soup.find_all('div', {'class': 'posts-list-item'}):
        new_pub = {}

        # Title is in the <b> tag
        title_tag = div.find('b')
        if not title_tag:
            continue
        new_pub['title'] = title_tag.get_text().strip()

        # Authors are <a> tags whose href contains /tags#
        authors = []
        for a in div.find_all('a'):
            href = a.get('href', '')
            if '/tags#' in href:
                # The link text is "Last, First" -- convert to "First Last"
                raw = a.get_text().strip()
                if ', ' in raw:
                    parts = raw.split(', ', 1)
                    authors.append(parts[1].strip() + ' ' + parts[0].strip())
                else:
                    authors.append(raw)

        if authors:
            new_pub['authors'] = authors

        # PDF link
        for a in div.find_all('a'):
            href = a.get('href', '')
            if href.endswith('.pdf'):
                if href.startswith('http'):
                    new_pub['pdf'] = href
                else:
                    new_pub['pdf'] = BASE_URL + '/' + href.lstrip('/')
                break

        new_pub['venue'] = venue
        new_pub['year'] = year
        results.append(new_pub)

    return results


pubs = []
warnings = []

for year in range(2024, 2027):
    url = "%s/miccai-%d/" % (BASE_URL, year)
    print("downloading MICCAI %d from %s ..." % (year, url))

    try:
        html = fetch(url).decode('utf-8')
    except Exception as e:
        warnings.append("could not fetch MICCAI %d: %s" % (year, e))
        print("error fetching, skipping...")
        continue

    # Check if the page actually has paper entries
    if 'posts-list-item' not in html:
        warnings.append("no papers found on page for MICCAI %d" % (year,))
        print("no papers found, skipping...")
        continue

    old_count = len(pubs)
    pubs.extend(parse_papers(html, year))
    print("read in %d publications for MICCAI %d." % (len(pubs) - old_count, year))

if len(warnings) > 0:
    print("%d warnings:" % (len(warnings),))
    for x in warnings:
        print(x)
else:
    print("No warnings generated.")

print("read in a total of %d publications." % (len(pubs),))
fname = "pubs_miccai"
print("saving pickle in %s" % (fname,))
savePubs(fname, pubs)
print("all done.")
