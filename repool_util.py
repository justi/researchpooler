""" Functions: useful general utils """

import pickle
import re
import webbrowser

def savePubs(filename, pubs_to_save):
    """
    save a list of publications into a file using Python's pickle
    filename: string
    pubs_to_save: List of Publication objects

    returns nothing
    """

    with open(filename, 'wb') as f:
        pickle.dump(pubs_to_save, f)

def loadPubs(filename):
    """
    retrieve a saved list of publications
    filename: string
    returns list of dictionaries, each representing a Publication
    """

    with open(filename, 'rb') as f:
        pubs = pickle.load(f)
    return pubs

def openPDFs(pdf_lst):
    """
    uses webbrowser to open a list of pdfs
    pdf_lst: list of strings: paths (or urls) of pdfs to open
    """
    if len(pdf_lst)>10:
        print("more than 10? that can't be right. Request denied.")
        return

    for x in pdf_lst:
        webbrowser.open(x)
        
def stringToWordDictionary(str):
    """
    Takes a string and returns dictionary that stores frequency of every word.
    Some stop words are removed.
    
    str: string
    returns dictionary of word counts for each word. Example: d['hello'] -> 5
    """
    str = str.lower() #convert to lower case
    m = re.findall(r'[a-zA-Z\-]+', str)
    m = [x for x in m if len(x) > 2] #filter out small words
    
    # count number of occurences of each word in dict and return it
    d = {}
    for i in m: d[i] = d.get(i,0) + 1
    
    # remove stopwords
    stopwords = ['the', 'and', 'for', 'that', 'can', 'this', 'which', \
                 'where', 'are', 'from', 'our', 'not', 'with', 'use', \
                 'then', 'than', 'but', 'have', 'was', 'were', 'these', \
                 'each', 'used', 'set', 'such', 'using', 'when', 'those',
                 'may', 'also']
    
    #cid is some kind of artifact from the pdf conversion that occurs very often
    stopwords.extend(['cid'])
    
    for k in stopwords:
        d.pop(k, None)
    
    return d


# ---------------------------------------------------------------------------
# Incremental-scrape helpers (shared by every *_download_parse.py)
# ---------------------------------------------------------------------------

def pubKey(pub):
    """Stable identity of a publication: title|||venue."""
    return "%s|||%s" % (pub.get("title", ""), pub.get("venue", ""))

def loadPubsIncremental(filename):
    """
    Load an existing pubs pickle for an incremental re-scrape.
    filename: string
    returns (pubs, keys, years): the list plus lookup sets used to skip
    already-scraped papers (keys, per title|||venue) or whole years (years).
    """
    try:
        pubs = loadPubs(filename)
        print("loaded %d existing publications." % (len(pubs),))
    except Exception:
        pubs = []
    return pubs, {pubKey(p) for p in pubs}, {p.get("year") for p in pubs}

def addPub(pubs, keys, new_pub):
    """Append new_pub unless its title|||venue is already present."""
    key = pubKey(new_pub)
    if key in keys:
        return False
    keys.add(key)
    pubs.append(new_pub)
    return True

def discoverPmlrVolumes(abbr):
    """
    {volume_number: year} for a venue on the proceedings.mlr.press index,
    so scrapers never hardcode a volume/year map.
    abbr: string as it appears in "Proceedings of <abbr> <year>" (e.g. "COLT")
    """
    import urllib.request
    line = re.compile(
        r'<li>\s*<a href="(v\d+|r\d+)"[^>]*><b>Volume [^<]+</b></a>'
        r'\s*Proceedings of\s+(\S+)\s+(\d{4})')
    req = urllib.request.Request("https://proceedings.mlr.press/",
                                 headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as f:
        body = f.read().decode("utf-8", "replace")
    vols = {int(v[1:]): int(y) for v, a, y in line.findall(body) if a == abbr}
    print("discovered %s volumes on PMLR: %s" % (abbr, sorted(vols.items())))
    return vols

def scrapeYears(first_year, step=1):
    """
    Years to scrape: from a conference's first available edition through the
    CURRENT year, computed at run time - never a hardcoded maximum.
    first_year: int; step: int (2 for biennial venues)
    returns range
    """
    from datetime import date
    return range(first_year, date.today().year + 1, step)
