"""
Standalone helper script.

Parses IJCAI proceedings from ijcai.org, creates list of
dictionaries that store information about each publication, and saves
the result as a pickle called pubs_ijcai.

Two HTML formats are handled:
  - 2017+: structured divs with class="paper_wrapper"
  - 2013-2016: flat <p> tags with titles in <a> and authors in <i> or <em>

IJCAI was biennial before 2016 (odd years only: 2013, 2015), then
annual from 2016 onward.  Years that return 404 are silently skipped.
"""

import urllib.request
import re
from bs4 import BeautifulSoup
from repool_util import savePubs

BASE_URL = "https://www.ijcai.org"

YEARS = list(range(2013, 2026))


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as f:
        return f.read().decode('utf-8')


def parse_new_format(soup, year):
    """Parse proceedings pages from 2017 onward (div.paper_wrapper)."""
    papers = []
    for pw in soup.find_all('div', class_='paper_wrapper'):
        new_pub = {}

        title_div = pw.find('div', class_='title')
        if not title_div:
            continue
        new_pub['title'] = title_div.get_text(strip=True)

        authors_div = pw.find('div', class_='authors')
        if authors_div:
            authors_text = authors_div.get_text(strip=True)
            new_pub['authors'] = [a.strip() for a in authors_text.split(',')
                                  if a.strip()]

        details_div = pw.find('div', class_='details')
        if details_div:
            for a in details_div.find_all('a'):
                href = a.get('href', '')
                if href.endswith('.pdf'):
                    # Relative link like "0001.pdf"
                    new_pub['pdf'] = "%s/proceedings/%d/%s" % (
                        BASE_URL, year, href)
                    break

        new_pub['venue'] = 'IJCAI %d' % year
        new_pub['year'] = year
        papers.append(new_pub)
    return papers


def parse_old_format(soup, year):
    """Parse proceedings pages from 2013-2016 (flat <p> tags)."""
    papers = []
    # The short year code used in URLs (e.g. 13 for 2013)
    short_year = str(year % 100).zfill(2)

    for p_tag in soup.find_all('p'):
        # A paper <p> must contain a PDF link and an author tag
        pdf_link = None
        for a in p_tag.find_all('a'):
            href = a.get('href', '')
            if '.pdf' in href and 'Papers/' in href:
                pdf_link = href
                break

        if not pdf_link:
            continue

        # Authors are in <i> (2013, 2016) or <em> (2015)
        authors_tag = p_tag.find('i')
        if not authors_tag:
            authors_tag = p_tag.find('em')
        if not authors_tag:
            continue

        # Extract title.  Two layouts exist:
        #   2013: <a href="...pdf">Title</a> / page_num
        #   2015-2016: Title / page_num  (plain text, PDF <a> has no text
        #              or is at the end of the <p>)
        title_a = None
        for a in p_tag.find_all('a'):
            href = a.get('href', '')
            if '.pdf' in href and 'Papers/' in href:
                link_text = a.get_text(strip=True)
                # In 2013 the link text IS the title; in 2015/2016 it is
                # just the word "PDF"
                if link_text and link_text.lower() != 'pdf':
                    title_a = a
                break

        if title_a:
            title = title_a.get_text(strip=True)
        else:
            # Title is the plain text before the first <br> or " / "
            # Get the first text node of the <p>
            first_text = ''
            for child in p_tag.children:
                if isinstance(child, str):
                    first_text = child.strip()
                    if first_text:
                        break
                elif child.name == 'br':
                    break
                elif child.name == 'a':
                    # Could be the title link (2013 style)
                    first_text = child.get_text(strip=True)
                    break
            title = first_text

        if not title:
            continue

        # Skip front matter entries (preface, organization, committee, etc.)
        skip_keywords = ['Preface', 'Conference Organization',
                         'IJCAI Organization', 'Past IJCAI Conferences',
                         'Program Committee', 'Organizers and Sponsors',
                         'Awards and Distinguished', 'Contents',
                         'Author Index', 'Keyword Index',
                         'Conference Sponsors', 'Conference Organizers']
        if any(kw.lower() in title.lower() for kw in skip_keywords):
            continue

        # Remove trailing page number like " / 20" or " / xxxiii"
        title = re.sub(r'\s*/\s*[\dxlvicXLVIC]+\s*$', '', title).strip()

        new_pub = {}
        new_pub['title'] = title

        authors_text = authors_tag.get_text(strip=True)
        new_pub['authors'] = [a.strip() for a in authors_text.split(',')
                              if a.strip()]

        # Normalize the PDF link to a full URL
        if pdf_link.startswith('http'):
            new_pub['pdf'] = pdf_link
        else:
            new_pub['pdf'] = BASE_URL + pdf_link

        new_pub['venue'] = 'IJCAI %d' % year
        new_pub['year'] = year
        papers.append(new_pub)
    return papers


pubs = []
warnings = []

for year in YEARS:
    url = "%s/proceedings/%d" % (BASE_URL, year)
    print("downloading IJCAI %d..." % year)

    try:
        html = fetch(url)
    except Exception as e:
        if '404' in str(e) or 'Not Found' in str(e):
            print("  no proceedings found for %d, skipping." % year)
        else:
            warnings.append("error fetching %d: %s" % (year, e))
            print("  error: %s" % e)
        continue

    print("  done. Parsing...")
    soup = BeautifulSoup(html, 'html.parser')

    old_count = len(pubs)

    # Detect format: new (2017+) uses div.paper_wrapper
    if soup.find('div', class_='paper_wrapper'):
        papers = parse_new_format(soup, year)
    else:
        papers = parse_old_format(soup, year)

    pubs.extend(papers)
    print("  read in %d publications for IJCAI %d." % (
        len(pubs) - old_count, year))

if len(warnings) > 0:
    print("%d warnings:" % len(warnings))
    for x in warnings:
        print(x)
else:
    print("No warnings generated.")

print("read in a total of %d publications." % len(pubs))
fname = "pubs_ijcai"
print("saving pickle in %s" % fname)
savePubs(fname, pubs)
print("all done.")
