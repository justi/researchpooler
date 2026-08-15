"""Scrape EMNLP proceedings from aclanthology.org into pubs_emnlp.

Only missing years (through the current year) are fetched - the shared
pipeline lives in scrape_common.scrapeAnthology.
"""

from scrape_common import scrapeAnthology

scrapeAnthology(slug="emnlp", name="EMNLP", first_year=2000)
