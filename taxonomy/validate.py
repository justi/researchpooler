"""
Validation test harness for two-stage classification pipeline (RE-29).

Runs an A/B comparison between current full-tree pipeline (Run A) and
pruned-tree pipeline (Run B) on 50 representative papers.

Usage:
    python taxonomy/validate.py                    # run full A/B comparison
    python taxonomy/validate.py --select-only      # export 50-paper sample only
    python taxonomy/validate.py --compare-only     # compare existing run_a/run_b results
"""

import os
import sys
import json
import pickle
import random
import argparse
from datetime import datetime, timezone

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repool_util import loadPubs

TAXONOMY_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TAXONOMY_DIR)

# 5 conferences, 10 papers each = 50 total
VALIDATION_CONFS = ['nips', 'icml', 'acl', 'cvpr', 'ijcai']
PAPERS_PER_CONF = 10

# Conference name mapping for display
CONF_DISPLAY = {
    'nips': 'NeurIPS', 'icml': 'ICML', 'acl': 'ACL',
    'cvpr': 'CVPR', 'ijcai': 'IJCAI'
}


def select_validation_papers(seed=42):
    """Select 50 papers: 10 from each of 5 conferences, all with abstracts.

    Returns:
        list of dicts with 'title', 'abstract', 'conf', 'year', 'venue'
    """
    random.seed(seed)
    selected = []

    for conf in VALIDATION_CONFS:
        pubs_path = os.path.join(PROJECT_DIR, "pubs_%s" % conf)
        if not os.path.exists(pubs_path):
            print("WARNING: pubs_%s not found, skipping" % conf)
            continue

        pubs = loadPubs(pubs_path)
        # Filter to papers with abstracts
        with_abstracts = [p for p in pubs if p.get('abstract')]
        if len(with_abstracts) < PAPERS_PER_CONF:
            print("WARNING: %s has only %d papers with abstracts (need %d)" % (
                conf, len(with_abstracts), PAPERS_PER_CONF))
            sample = with_abstracts
        else:
            sample = random.sample(with_abstracts, PAPERS_PER_CONF)

        for p in sample:
            selected.append({
                'title': p['title'],
                'abstract': p.get('abstract', ''),
                'conf': conf,
                'year': p.get('year', 0),
                'venue': p.get('venue', ''),
                'authors': p.get('authors', [])
            })

    print("Selected %d validation papers from %d conferences" % (
        len(selected), len(VALIDATION_CONFS)))
    return selected


def run_classification(papers, allowed_topics, run_name, use_normalization=False):
    """Run classification on a set of papers with given topics.

    Args:
        papers: list of paper dicts
        allowed_topics: list of allowed topic paths (full or pruned)
        run_name: "A" or "B" for logging
        use_normalization: whether to apply keyword post-processing

    Returns:
        dict mapping paper title -> classification result
    """
    from taxonomy.classify import classify_batch
    from taxonomy.keyword_normalize import normalize_keywords

    results = {}
    existing_kw = set()

    for i, paper in enumerate(papers):
        print("  Run %s [%d/%d]: %s" % (run_name, i + 1, len(papers), paper['title'][:60]))

        paper_data = [{'title': paper['title'], 'abstract': paper['abstract']}]
        result = classify_batch(paper_data, allowed_topics)

        if result and 'papers' in result and result['papers']:
            item = result['papers'][0]
            raw_keywords = item.get('keywords', [])

            if use_normalization:
                keywords = normalize_keywords(raw_keywords, existing_kw)
                existing_kw.update(keywords)
            else:
                keywords = raw_keywords

            results[paper['title']] = {
                'topics': item.get('topics', []),
                'keywords': keywords,
                'keywords_raw': raw_keywords,
                'reasoning': item.get('reasoning', ''),
                'conf': paper['conf'],
                'year': paper['year']
            }
        else:
            print("    WARN: no result for paper")
            results[paper['title']] = {
                'topics': [],
                'keywords': [],
                'keywords_raw': [],
                'reasoning': '',
                'conf': paper['conf'],
                'year': paper['year']
            }

        import time
        time.sleep(1)

    return results


def compute_jaccard(set_a, set_b):
    """Compute Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def compare_runs(run_a, run_b, allowed_topics):
    """Compare Run A and Run B results, computing quality metrics.

    Returns:
        dict with aggregate metrics and per-paper breakdown
    """
    allowed_set = set(allowed_topics) if allowed_topics else set()
    papers = set(run_a.keys()) | set(run_b.keys())

    per_paper = []
    total_topics_a = 0
    total_topics_b = 0
    off_list_a = 0
    off_list_b = 0
    topics_overlaps = []
    keyword_overlaps = []
    prompt_size_a = 0
    prompt_size_b = 0

    # Count plural duplicates
    all_kw_a = []
    all_kw_b = []

    for title in sorted(papers):
        a = run_a.get(title, {'topics': [], 'keywords': []})
        b = run_b.get(title, {'topics': [], 'keywords': []})

        topics_a = set(a.get('topics', []))
        topics_b = set(b.get('topics', []))
        kw_a = set(a.get('keywords', []))
        kw_b = set(b.get('keywords', []))

        # Off-list topics
        off_a = [t for t in topics_a if t not in allowed_set and not t.startswith('Other:')]
        off_b = [t for t in topics_b if t not in allowed_set and not t.startswith('Other:')]

        total_topics_a += len(topics_a)
        total_topics_b += len(topics_b)
        off_list_a += len(off_a)
        off_list_b += len(off_b)

        # Overlap
        topic_jaccard = compute_jaccard(topics_a, topics_b)
        kw_jaccard = compute_jaccard(kw_a, kw_b)
        topics_overlaps.append(topic_jaccard)
        keyword_overlaps.append(kw_jaccard)

        all_kw_a.extend(a.get('keywords', []))
        all_kw_b.extend(b.get('keywords', []))

        per_paper.append({
            'title': title,
            'conf': a.get('conf', b.get('conf', '')),
            'topics_a': list(topics_a),
            'topics_b': list(topics_b),
            'keywords_a': list(kw_a),
            'keywords_b': list(kw_b),
            'off_list_a': off_a,
            'off_list_b': off_b,
            'topic_overlap': round(topic_jaccard, 3),
            'keyword_overlap': round(kw_jaccard, 3)
        })

    # Compute plural duplicate rate
    def count_plural_dupes(keywords):
        import inflect
        engine = inflect.engine()
        kw_set = set(kw.lower() for kw in keywords)
        dupes = 0
        checked = set()
        for kw in kw_set:
            if kw in checked:
                continue
            singular = engine.singular_noun(kw.split()[-1]) if kw.split() else None
            if singular:
                candidate = " ".join(kw.split()[:-1] + [singular])
                if candidate != kw and candidate in kw_set:
                    dupes += 1
            checked.add(kw)
        return dupes, len(kw_set)

    plural_dupes_a, total_kw_a = count_plural_dupes(all_kw_a)
    plural_dupes_b, total_kw_b = count_plural_dupes(all_kw_b)

    report = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'paper_count': len(papers),
        'metrics': {
            'off_list_pct_a': round(100 * off_list_a / max(total_topics_a, 1), 1),
            'off_list_pct_b': round(100 * off_list_b / max(total_topics_b, 1), 1),
            'plural_pct_a': round(100 * plural_dupes_a / max(total_kw_a, 1), 1),
            'plural_pct_b': round(100 * plural_dupes_b / max(total_kw_b, 1), 1),
            'topics_overlap_avg': round(sum(topics_overlaps) / max(len(topics_overlaps), 1), 3),
            'keyword_overlap_avg': round(sum(keyword_overlaps) / max(len(keyword_overlaps), 1), 3),
            'total_topics_a': total_topics_a,
            'total_topics_b': total_topics_b,
            'total_unique_topics_a': len(set(t for p in per_paper for t in p['topics_a'])),
            'total_unique_topics_b': len(set(t for p in per_paper for t in p['topics_b'])),
            'total_unique_keywords_a': total_kw_a,
            'total_unique_keywords_b': total_kw_b,
            'plural_dupes_a': plural_dupes_a,
            'plural_dupes_b': plural_dupes_b,
        },
        'per_paper': per_paper
    }

    return report


def print_report(report):
    """Print a human-readable comparison report."""
    m = report['metrics']

    print("\n" + "=" * 70)
    print("VALIDATION COMPARISON REPORT (%d papers)" % report['paper_count'])
    print("=" * 70)

    print("\n%-35s %10s %10s" % ("Metric", "Run A", "Run B"))
    print("-" * 57)
    print("%-35s %9.1f%% %9.1f%%" % ("Off-list topics", m['off_list_pct_a'], m['off_list_pct_b']))
    print("%-35s %9.1f%% %9.1f%%" % ("Plural duplicates", m['plural_pct_a'], m['plural_pct_b']))
    print("%-35s %10d %10d" % ("Total topics assigned", m['total_topics_a'], m['total_topics_b']))
    print("%-35s %10d %10d" % ("Unique topics", m['total_unique_topics_a'], m['total_unique_topics_b']))
    print("%-35s %10d %10d" % ("Unique keywords", m['total_unique_keywords_a'], m['total_unique_keywords_b']))
    print("%-35s %10d %10d" % ("Plural dupes count", m['plural_dupes_a'], m['plural_dupes_b']))

    print("\n%-35s %10s" % ("Cross-run Metric", "Value"))
    print("-" * 47)
    print("%-35s %9.1f%%" % ("Topics overlap (avg Jaccard)", 100 * m['topics_overlap_avg']))
    print("%-35s %9.1f%%" % ("Keyword overlap (avg Jaccard)", 100 * m['keyword_overlap_avg']))

    # Flag significant divergences
    divergent = [p for p in report['per_paper'] if p['topic_overlap'] < 0.3]
    if divergent:
        print("\nDIVERGENT PAPERS (topic overlap < 30%):")
        for p in divergent:
            print("  [%s] %s (overlap: %.0f%%)" % (
                p['conf'], p['title'][:60], 100 * p['topic_overlap']))

    # Threshold check
    print("\nTHRESHOLD CHECKS:")
    checks = [
        ("Off-list topics Run B < 3%%", m['off_list_pct_b'] < 3),
        ("Plural dupes Run B < 1%%", m['plural_pct_b'] < 1),
        ("Topics overlap >= 70%%", 100 * m['topics_overlap_avg'] >= 70),
    ]
    for label, passed in checks:
        status = "PASS" if passed else "FAIL"
        print("  [%s] %s" % (status, label))

    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description='Validation test harness for two-stage classification')
    parser.add_argument('--select-only', action='store_true',
                        help='Export 50-paper sample without running classification')
    parser.add_argument('--compare-only', action='store_true',
                        help='Compare existing run_a and run_b results')
    parser.add_argument('--pre-domains-file', type=str,
                        help='JSON file with pre-domains for Run B pruning')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for paper selection')
    args = parser.parse_args()

    if args.compare_only:
        run_a_path = os.path.join(TAXONOMY_DIR, "validation_run_a.json")
        run_b_path = os.path.join(TAXONOMY_DIR, "validation_run_b.json")
        if not os.path.exists(run_a_path) or not os.path.exists(run_b_path):
            print("ERROR: Need both validation_run_a.json and validation_run_b.json")
            sys.exit(1)
        with open(run_a_path) as f:
            run_a = json.load(f)
        with open(run_b_path) as f:
            run_b = json.load(f)

        from taxonomy.classify import load_taxonomy_config
        allowed_topics = load_taxonomy_config() or []

        report = compare_runs(run_a, run_b, allowed_topics)
        report_path = os.path.join(TAXONOMY_DIR, "validation_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print("Report saved to %s" % report_path)
        print_report(report)
        return

    # Select papers
    papers = select_validation_papers(seed=args.seed)

    if args.select_only:
        output_path = os.path.join(TAXONOMY_DIR, "validation_sample.json")
        with open(output_path, 'w') as f:
            json.dump(papers, f, indent=2, ensure_ascii=False)
        print("Sample exported to %s" % output_path)
        return

    # Load taxonomy
    from taxonomy.classify import load_taxonomy_config
    from taxonomy.pruned_taxonomy import build_pruned_taxonomy, load_taxonomy_config_raw

    full_topics = load_taxonomy_config()
    if not full_topics:
        print("ERROR: No config.yaml found")
        sys.exit(1)

    # Load pre-domains if provided
    pre_domains_map = {}
    if args.pre_domains_file:
        with open(args.pre_domains_file) as f:
            pre_domains_map = json.load(f)
        print("Loaded pre-domains for %d papers" % len(pre_domains_map))

    # Run A: Full taxonomy
    print("\n--- Run A: Full taxonomy (%d topics) ---" % len(full_topics))
    run_a = run_classification(papers, full_topics, "A", use_normalization=False)
    run_a_path = os.path.join(TAXONOMY_DIR, "validation_run_a.json")
    with open(run_a_path, 'w') as f:
        json.dump(run_a, f, indent=2, ensure_ascii=False)
    print("Run A saved (%d results)" % len(run_a))

    # Run B: Pruned taxonomy + normalization
    print("\n--- Run B: Pruned taxonomy + normalization ---")
    taxonomy_config = load_taxonomy_config_raw()
    run_b = {}

    for i, paper in enumerate(papers):
        title = paper['title']
        pre_domains = pre_domains_map.get(title, [])
        if pre_domains:
            pruned_topics = build_pruned_taxonomy(pre_domains, taxonomy_config)
        else:
            pruned_topics = full_topics

        print("  Run B [%d/%d]: %s (%d topics)" % (
            i + 1, len(papers), title[:50], len(pruned_topics)))

        result = run_classification([paper], pruned_topics, "B", use_normalization=True)
        run_b.update(result)

        import time
        time.sleep(1)

    run_b_path = os.path.join(TAXONOMY_DIR, "validation_run_b.json")
    with open(run_b_path, 'w') as f:
        json.dump(run_b, f, indent=2, ensure_ascii=False)
    print("Run B saved (%d results)" % len(run_b))

    # Compare
    report = compare_runs(run_a, run_b, full_topics)
    report_path = os.path.join(TAXONOMY_DIR, "validation_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print("Report saved to %s" % report_path)
    print_report(report)


if __name__ == '__main__':
    main()
