"""
Build a representative sample of 1000 papers from all conferences and years,
proportional to conference size, then classify them.
"""

import os
import sys
import random
import pickle
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repool_util import loadPubs

TAXONOMY_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TAXONOMY_DIR)
TARGET_SAMPLE = 1000
BATCH_SIZE = 20

ALL_CONFS = [
    'nips', 'acl', 'emnlp', 'cvpr', 'aaai', 'icml', 'iclr', 'ijcai', 'iccv',
    'naacl', 'interspeech', 'coling', 'eccv', 'ijcnlp', 'aistats', 'wacv',
    'jmlr', 'semeval', 'eacl', 'miccai', 'colt', 'conll', 'corl', 'rss',
    'uai', 'aacl', 'acml', 'nsdi', 'l4dc', 'midl', 'osdi', 'alt', 'mlhc',
    'pgm', 'clear', 'automl'
]


def build_sample():
    """Build proportional stratified sample across conferences and years."""
    # Load all papers grouped by (conf, year)
    all_papers = {}  # conf -> list of papers
    total = 0
    for conf in ALL_CONFS:
        pubs_path = os.path.join(PROJECT_DIR, "pubs_%s" % conf)
        if not os.path.exists(pubs_path):
            continue
        pubs = loadPubs(pubs_path)
        all_papers[conf] = pubs
        total += len(pubs)

    print("Total papers: %d across %d conferences" % (total, len(all_papers)))

    if total == 0:
        print("No pubs files found. Nothing to sample.")
        return []

    # Calculate proportional allocation per conference
    allocation = {}
    for conf, pubs in all_papers.items():
        allocation[conf] = max(1, round(TARGET_SAMPLE * len(pubs) / total))

    # Adjust to hit exactly TARGET_SAMPLE
    current = sum(allocation.values())
    while current > TARGET_SAMPLE:
        biggest = max(allocation, key=allocation.get)
        allocation[biggest] -= 1
        current -= 1
    while current < TARGET_SAMPLE:
        biggest = max(allocation, key=lambda c: len(all_papers[c]) / max(allocation[c], 1))
        allocation[biggest] += 1
        current += 1

    print("\nAllocation per conference:")
    for conf in sorted(allocation, key=lambda c: -allocation[c]):
        print("  %-12s %4d / %6d (%.1f%%)" % (
            conf, allocation[conf], len(all_papers[conf]),
            100.0 * allocation[conf] / len(all_papers[conf])
        ))

    # Sample: stratify by year within each conference
    sample = []
    for conf, n_sample in allocation.items():
        pubs = all_papers[conf]

        # Group by year
        by_year = defaultdict(list)
        for p in pubs:
            by_year[p.get('year', 0)].append(p)

        # Proportional per year
        years = sorted(by_year.keys())
        year_alloc = {}
        for y in years:
            year_alloc[y] = max(1, round(n_sample * len(by_year[y]) / len(pubs)))

        # Adjust
        curr = sum(year_alloc.values())
        while curr > n_sample:
            biggest_y = max(year_alloc, key=year_alloc.get)
            year_alloc[biggest_y] -= 1
            curr -= 1
        while curr < n_sample:
            biggest_y = max(year_alloc, key=lambda y: len(by_year[y]) / max(year_alloc[y], 1))
            year_alloc[biggest_y] += 1
            curr += 1

        for y in years:
            n = min(year_alloc.get(y, 0), len(by_year[y]))
            if n > 0:
                picked = random.sample(by_year[y], n)
                for p in picked:
                    p['_conf'] = conf
                sample.extend(picked)

    random.shuffle(sample)
    print("\nSample size: %d papers" % len(sample))

    # Show year distribution
    year_dist = defaultdict(int)
    for p in sample:
        year_dist[p.get('year', 0)] += 1
    print("\nYear distribution:")
    for y in sorted(year_dist):
        print("  %d: %d" % (y, year_dist[y]))

    return sample


def classify_batch(titles, allowed_topics=None):
    """Send a batch of titles to OpenCode for classification.
    Uses classify.py's classify_batch to avoid duplication."""
    # Import from classify.py to use the same logic (config + keyword rules)
    from classify import classify_batch as _classify
    return _classify(titles, allowed_topics)


def classify_sample(sample):
    """Classify all papers in the sample, saving progress after every batch."""
    from classify import load_taxonomy_config
    allowed_topics = load_taxonomy_config()
    if allowed_topics:
        print("Using config.yaml (%d allowed topics)" % len(allowed_topics))
    else:
        print("No config.yaml, using free-form classification")

    results = {}  # conf -> {title: {topics, keywords, year, venue, authors}}
    total_done = 0
    total_batches = (len(sample) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_start in range(0, len(sample), BATCH_SIZE):
        batch = sample[batch_start:batch_start + BATCH_SIZE]
        titles = [p['title'] for p in batch]

        batch_num = batch_start // BATCH_SIZE + 1
        sys.stdout.write("  batch %d/%d (%d done)..." % (batch_num, total_batches, total_done))
        sys.stdout.flush()

        result = classify_batch(titles, allowed_topics)

        batch_ok = 0
        if result and 'papers' in result:
            for item in result['papers']:
                idx = item.get('idx', 0) - 1
                if 0 <= idx < len(batch):
                    pub = batch[idx]
                    conf = pub['_conf']
                    if conf not in results:
                        results[conf] = {}
                    key = "%s|||%s" % (pub['title'], pub.get('venue', ''))
                    results[conf][key] = {
                        'topics': item.get('topics', []),
                        'keywords': item.get('keywords', []),
                        'year': pub.get('year', 0),
                        'venue': pub.get('venue', ''),
                        'authors': pub.get('authors', []),
                        'title': pub['title']
                    }
                    total_done += 1
                    batch_ok += 1

        print(" +%d (total: %d)" % (batch_ok, total_done))

        # Save after every batch
        for conf, classified in results.items():
            path = os.path.join(TAXONOMY_DIR, "taxonomy_%s" % conf)
            with open(path, 'wb') as f:
                pickle.dump(classified, f)

        time.sleep(1)

    return results


def main():
    random.seed(42)  # reproducible

    print("=== Building representative sample ===\n")
    sample = build_sample()

    print("\n=== Classifying %d papers ===\n" % len(sample))
    results = classify_sample(sample)

    # Save per-conference taxonomy files
    for conf, classified in results.items():
        path = os.path.join(TAXONOMY_DIR, "taxonomy_%s" % conf)
        with open(path, 'wb') as f:
            pickle.dump(classified, f)
        print("  saved taxonomy_%s (%d papers)" % (conf, len(classified)))

    total = sum(len(v) for v in results.values())
    print("\nDone! Classified %d papers across %d conferences." % (total, len(results)))


if __name__ == '__main__':
    main()
