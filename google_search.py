"""
Functions for searching Google and retrieving urls to PDFs
"""

import urllib.request
import urllib.parse

def getPDFURL(pdf_title):
    """
    Search google for exact match of the title of this paper
    and return the url to the pdf file, or 'notfound' if no exact match was
    found.

    pdf_title: string, name of the paper.
    Returns url to the PDF, or 'notfound' if unsuccessful

    Note: The original Google AJAX Search API has been retired.
    This version uses a simple scraping approach which may be fragile.
    For production use, consider using the Google Custom Search JSON API.
    """

    query = urllib.parse.urlencode({'q': pdf_title + ' filetype:pdf'})
    url = 'https://www.google.com/search?%s' % (query,)

    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8')
    except Exception as e:
        print('Error searching Google: %s' % (e,))
        return 'notfound'

    # Try to extract first PDF link from results
    import re
    pdf_links = re.findall(r'(https?://[^\s"&]+\.pdf)', html)
    if pdf_links:
        return pdf_links[0]

    return 'notfound'
