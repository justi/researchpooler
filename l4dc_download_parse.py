"""Scrape L4DC proceedings from proceedings.mlr.press into pubs_l4dc.

Volumes are discovered at run time and only missing years are fetched -
the shared pipeline lives in scrape_common.scrapePmlr.
"""

from scrape_common import scrapePmlr

scrapePmlr("L4DC")
