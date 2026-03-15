"""
Standalone helper script.

Parses AAAI proceedings from ojs.aaai.org, creates list of
dictionaries that store information about each publication, and saves
the result as a pickle called pubs_aaai.
"""

import urllib.request
import re
from bs4 import BeautifulSoup
from repool_util import savePubs

BASE_URL = "https://ojs.aaai.org/index.php/AAAI"


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as f:
        return f.read().decode('utf-8')


# Step 1: collect all issue URLs from archive pages
print("collecting issue list from archive...")
issue_urls = {}  # year -> list of (url, title)

for page in range(1, 15):
    url = "%s/issue/archive/%d" % (BASE_URL, page)
    try:
        html = fetch(url)
    except:
        break

    soup = BeautifulSoup(html, 'html.parser')
    links = soup.find_all('a', class_='title')
    if not links:
        break

    for a in links:
        title = a.text.strip()
        href = a.get('href', '')
        m = re.search(r'AAAI-(\d+)', title)
        if not m:
            continue
        yr = int(m.group(1))
        year = yr + 2000 if yr < 100 else yr
        if year not in issue_urls:
            issue_urls[year] = []
        issue_urls[year].append((href, title))

print("found issues for years: %s" % sorted(issue_urls.keys()))

# Step 2: scrape papers from each issue
pubs = []
warnings = []

for year in sorted(issue_urls):
    issues = issue_urls[year]
    print("downloading AAAI %d (%d issues)..." % (year, len(issues)))

    venue = 'AAAI %d' % (year,)
    old_count = len(pubs)

    for issue_url, issue_title in issues:
        try:
            html = fetch(issue_url)
        except Exception as e:
            warnings.append("error fetching %s: %s" % (issue_url, e))
            continue

        soup = BeautifulSoup(html, 'html.parser')

        for article in soup.find_all('div', class_='obj_article_summary'):
            new_pub = {}

            title_tag = article.find('h3', class_='title')
            if not title_tag:
                continue
            a = title_tag.find('a')
            if not a:
                continue

            new_pub['title'] = a.text.strip()

            authors_div = article.find('div', class_='authors')
            if authors_div:
                authors_text = authors_div.text.strip()
                new_pub['authors'] = [x.strip() for x in authors_text.split(',')]

            pdf_link = article.find('a', class_='obj_galley_link pdf')
            if pdf_link:
                new_pub['pdf'] = pdf_link['href']

            new_pub['venue'] = venue
            new_pub['year'] = year
            pubs.append(new_pub)

    print("read in %d publications for AAAI %d." % (len(pubs) - old_count, year))

if len(warnings) > 0:
    print("%d warnings:" % (len(warnings),))
    for x in warnings:
        print(x)
else:
    print("No warnings generated.")

print("read in a total of %d publications." % (len(pubs),))
fname = "pubs_aaai"
print("saving pickle in %s" % (fname,))
savePubs(fname, pubs)
print("all done.")
