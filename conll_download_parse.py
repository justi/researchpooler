"""Scrape CoNLL proceedings from aclanthology.org into pubs_conll.

Only missing years (through the current year) are fetched - the shared
pipeline lives in scrape_common.scrapeAnthology.
"""

from scrape_common import scrapeAnthology

scrapeAnthology(slug="conll", name="CoNLL", first_year=2000)
