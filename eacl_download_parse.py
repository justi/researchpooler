"""Scrape EACL proceedings from aclanthology.org into pubs_eacl.

Only missing years (through the current year) are fetched - the shared
pipeline lives in scrape_common.scrapeAnthology.
"""

from scrape_common import scrapeAnthology

scrapeAnthology(slug="eacl", name="EACL", first_year=2000)
