"""Scrape ACL proceedings from aclanthology.org into pubs_acl.

Only missing years (through the current year) are fetched - the shared
pipeline lives in scrape_common.scrapeAnthology.
"""

from scrape_common import scrapeAnthology

scrapeAnthology(slug="acl", name="ACL", first_year=2000)
