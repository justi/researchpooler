"""Scrape COLING proceedings from aclanthology.org into pubs_coling.

Only missing years (through the current year) are fetched - the shared
pipeline lives in scrape_common.scrapeAnthology.
"""

from scrape_common import scrapeAnthology

scrapeAnthology(slug="coling", name="COLING", first_year=2000)
