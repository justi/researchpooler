"""
Standalone helper script.

Parses INTERSPEECH proceedings from isca-archive.org, creates list of
dictionaries that store information about each publication, and saves
the result as a pickle called pubs_interspeech.
"""

import urllib.request
from bs4 import BeautifulSoup
from repool_util import savePubs

BASE_URL = "https://www.isca-archive.org"

pubs = []
warnings = []

for year in range(2016, 2025):
    url = "%s/interspeech_%d/" % (BASE_URL, year)
    print("downloading INTERSPEECH %d..." % (year,))

    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as f:
            s = f.read()
    except Exception as e:
        print("error fetching year %d: %s, skipping..." % (year, e))
        continue

    print("done. Parsing...")
    soup = BeautifulSoup(s, 'html.parser')

    venue = 'INTERSPEECH %d' % (year,)
    old_count = len(pubs)

    # Each paper is an <a class="w3-text" href="slug_interspeech.html">
    # containing a <p> with the title text, a <br>, and a
    # <span class="w3-text w3-text-theme"> with the authors.
    for a_tag in soup.find_all('a', class_='w3-text'):
        href = a_tag.get('href', '')
        if '_interspeech.html' not in href:
            continue

        p_tag = a_tag.find('p')
        if not p_tag:
            continue

        # Extract authors from the span
        author_span = p_tag.find('span', class_='w3-text-theme')
        authors_text = ''
        if author_span:
            authors_text = author_span.get_text(strip=True)

        # Extract title: get all text from <p>, then remove authors portion
        # The <p> contains: Title <br> <span>Authors</span>
        # We can get the title by removing the span and getting remaining text
        span_clone = author_span.extract() if author_span else None
        title = p_tag.get_text(strip=True)

        if not title:
            if span_clone:
                p_tag.append(span_clone)
            continue

        new_pub = {'title': title}

        # Parse authors (comma-separated in the span)
        if authors_text:
            authors = [a.strip() for a in authors_text.split(',')]
            authors = [a for a in authors if a]
            new_pub['authors'] = authors

        # PDF URL: replace .html with .pdf in the href
        pdf_url = "%s/interspeech_%d/%s" % (BASE_URL, year, href.replace('.html', '.pdf'))
        new_pub['pdf'] = pdf_url

        new_pub['venue'] = venue
        new_pub['year'] = year
        pubs.append(new_pub)

        # Restore the span so we don't break parsing of subsequent elements
        if span_clone:
            p_tag.append(span_clone)

    print("read in %d publications for INTERSPEECH %d." % (len(pubs) - old_count, year))

# show warnings, if any were generated
if len(warnings) > 0:
    print("%d warnings:" % (len(warnings),))
    for x in warnings:
        print(x)
else:
    print("No warnings generated.")

# finally, save pickle as output
print("read in a total of %d publications." % (len(pubs),))
fname = "pubs_interspeech"
print("saving pickle in %s" % (fname,))
savePubs(fname, pubs)
print("all done.")
