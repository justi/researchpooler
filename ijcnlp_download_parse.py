"""Scrape IJCNLP proceedings from aclanthology.org into pubs_ijcnlp.

Only missing years (through the current year) are fetched - the shared
pipeline lives in scrape_common.scrapeAnthology.
"""

from scrape_common import scrapeAnthology

scrapeAnthology(slug="ijcnlp", name="IJCNLP", first_year=2005)
