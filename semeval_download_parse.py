"""Scrape SemEval proceedings from aclanthology.org into pubs_semeval.

Only missing years (through the current year) are fetched - the shared
pipeline lives in scrape_common.scrapeAnthology.
"""

from scrape_common import scrapeAnthology

scrapeAnthology(slug="semeval", name="SemEval", first_year=2007)
