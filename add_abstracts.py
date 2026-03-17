"""
Generic abstract scraper with pluggable source extractors.

Extracts abstracts from HTML pages for 7 conference sources (~122k papers).
Each source has a plugin that handles URL transformation and HTML parsing.

Usage:
    python add_abstracts.py --source acl_anthology          # scrape ACL Anthology conferences
    python add_abstracts.py --source pmlr --limit 100       # first 100 papers
    python add_abstracts.py --source openreview --year 2023  # only 2023 papers
    python add_abstracts.py --status                         # show all sources progress
    python add_abstracts.py --source acl_anthology --status  # show one source progress
"""

import os
import sys
import time
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from repool_util import loadPubs, savePubs
from abstract_sources import SOURCES

CHECKPOINT_EVERY = 500
REQUEST_DELAY = 0.5


def show_status(source_name=None):
    """Show abstract extraction progress per source."""
    if source_name:
        sources = {source_name: SOURCES[source_name]}
    else:
        sources = SOURCES

    total_papers = 0
    total_with_abstract = 0

    print("=" * 65)
    print(f"{'Source':<18} {'Conf':<8} {'Total':>7} {'Abstracts':>10} {'%':>6}")
    print("-" * 65)

    for name, source_cls in sorted(sources.items()):
        source = source_cls()
        for conf in source.conferences:
            pickle_name = f"pubs_{conf}"
            try:
                pubs = loadPubs(pickle_name)
            except FileNotFoundError:
                print(f"  {name:<18} {conf:<8} {'(not found)':>7}")
                continue

            total = len(pubs)
            with_abs = sum(1 for p in pubs if p.get("abstract"))
            pct = (with_abs / total * 100) if total > 0 else 0
            total_papers += total
            total_with_abstract += with_abs

            print(f"  {name:<18} {conf:<8} {total:>7} {with_abs:>10} {pct:>5.1f}%")

    print("-" * 65)
    pct = (total_with_abstract / total_papers * 100) if total_papers > 0 else 0
    print(f"  {'TOTAL':<18} {'':<8} {total_papers:>7} {total_with_abstract:>10} {pct:>5.1f}%")
    print("=" * 65)


def scrape_source(source_name, limit=None, year=None):
    """Scrape abstracts for all conferences of a source."""
    source_cls = SOURCES[source_name]
    source = source_cls()

    print(f"Source: {source_name}")
    print(f"Conferences: {', '.join(source.conferences)}")
    print()

    # Special handling for bulk API sources (OpenReview)
    if hasattr(source, "bulk_fetch_abstracts"):
        for conf in source.conferences:
            pickle_name = f"pubs_{conf}"
            try:
                pubs = loadPubs(pickle_name)
            except FileNotFoundError:
                print(f"  [{conf}] pickle not found, skipping")
                continue

            existing = sum(1 for p in pubs if p.get("abstract"))
            print(f"  [{conf}] {len(pubs)} papers, {existing} already have abstracts")

            added = source.bulk_fetch_abstracts(pubs, year=year)
            if added > 0:
                savePubs(pickle_name, pubs)

            now_total = sum(1 for p in pubs if p.get("abstract"))
            print(f"  [{conf}] Done: +{added} abstracts, {now_total}/{len(pubs)} total")
            print()
        return

    for conf in source.conferences:
        pickle_name = f"pubs_{conf}"
        try:
            pubs = loadPubs(pickle_name)
        except FileNotFoundError:
            print(f"  [{conf}] pickle not found, skipping")
            continue

        # Filter papers needing abstracts
        to_process = []
        for p in pubs:
            if p.get("abstract"):
                continue
            if not p.get("pdf"):
                continue
            if year and p.get("year") != year:
                continue
            to_process.append(p)

        if limit:
            remaining = limit - sum(1 for _ in [])  # limit is per-source, applied per-conf
            to_process = to_process[:limit]

        total = len(to_process)
        existing = sum(1 for p in pubs if p.get("abstract"))

        if total == 0:
            print(f"  [{conf}] {len(pubs)} papers, {existing} already have abstracts — nothing to do")
            continue

        print(f"  [{conf}] Processing {total} papers ({existing} already have abstracts)...")
        extracted = 0
        failed = 0

        for i, p in enumerate(to_process):
            abstract = source.fetch_and_extract(p["pdf"])

            if abstract:
                p["abstract"] = abstract
                extracted += 1
                if extracted <= 3 or extracted % 50 == 0:
                    print(f"    [{i+1}/{total}] + {p['title'][:55]}... ({len(abstract)}ch)")
            else:
                failed += 1
                if failed <= 3:
                    print(f"    [{i+1}/{total}] x {p['title'][:55]}...")

            # Progress
            if (i + 1) % 100 == 0:
                pct = (i + 1) / total * 100
                print(f"    --- {i+1}/{total} ({pct:.1f}%) — {extracted} ok, {failed} fail ---")

            # Checkpoint
            if (i + 1) % CHECKPOINT_EVERY == 0:
                print(f"    [checkpoint] saving {pickle_name}...")
                savePubs(pickle_name, pubs)

            time.sleep(REQUEST_DELAY)

        # Final save
        if extracted > 0:
            savePubs(pickle_name, pubs)

        now_total = sum(1 for p in pubs if p.get("abstract"))
        print(f"  [{conf}] Done: +{extracted} extracted, {failed} failed, {now_total}/{len(pubs)} total")
        print()


def main():
    parser = argparse.ArgumentParser(description="Generic abstract scraper with source plugins")
    parser.add_argument("--source", choices=list(SOURCES.keys()),
                        help="Source plugin to use")
    parser.add_argument("--limit", type=int, default=None,
                        help="Max papers to process per conference")
    parser.add_argument("--year", type=int, default=None,
                        help="Only process papers from this year")
    parser.add_argument("--status", action="store_true",
                        help="Show abstract extraction progress")
    args = parser.parse_args()

    if args.status:
        show_status(args.source)
        return

    if not args.source:
        print("Available sources:")
        for name, cls in sorted(SOURCES.items()):
            src = cls()
            print(f"  {name:<18} -> {', '.join(src.conferences)}")
        print("\nUsage: python add_abstracts.py --source <name> [--limit N] [--year YYYY]")
        print("       python add_abstracts.py --status")
        return

    scrape_source(args.source, limit=args.limit, year=args.year)


if __name__ == "__main__":
    main()
