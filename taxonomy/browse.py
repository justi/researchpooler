"""
Interactive taxonomy browser.

Browse the classified papers by topic hierarchy and keywords.

Usage:
    python taxonomy/browse.py                    # interactive mode
    python taxonomy/browse.py --topic "Machine Learning"  # filter by topic
    python taxonomy/browse.py --keyword "transformer"     # filter by keyword
    python taxonomy/browse.py --tree              # show topic tree
    python taxonomy/browse.py --stats             # show statistics
"""

import os
import sys
import pickle
import argparse
from collections import defaultdict

TAXONOMY_DIR = os.path.dirname(os.path.abspath(__file__))


def load_all_taxonomies():
    """Load all taxonomy_* files."""
    all_data = {}
    for fname in os.listdir(TAXONOMY_DIR):
        if fname.startswith('taxonomy_'):
            conf = fname.replace('taxonomy_', '')
            path = os.path.join(TAXONOMY_DIR, fname)
            with open(path, 'rb') as f:
                all_data[conf] = pickle.load(f)
    return all_data


def build_tree(all_data):
    """Build a nested tree from topic paths."""
    tree = {}
    for conf, papers in all_data.items():
        for title, data in papers.items():
            for topic_path in data.get('topics', []):
                parts = [p.strip() for p in topic_path.split('>')]
                node = tree
                for part in parts:
                    if part not in node:
                        node[part] = {'_papers': [], '_children': {}, '_seen': set()}
                    if title not in node[part]['_seen']:
                        node[part]['_seen'].add(title)
                        node[part]['_papers'].append({
                            'title': title,
                            'conf': conf,
                            'year': data.get('year', 0),
                            'keywords': data.get('keywords', [])
                        })
                    node = node[part]['_children']
    return tree


def print_tree(tree, prefix="", max_depth=3, depth=0):
    """Print topic tree with paper counts."""
    if depth >= max_depth:
        return

    for name in sorted(tree.keys()):
        node = tree[name]
        count = len(node['_papers'])
        connector = "├── " if name != sorted(tree.keys())[-1] else "└── "
        print("%s%s%s (%d)" % (prefix, connector, name, count))

        child_prefix = prefix + ("│   " if name != sorted(tree.keys())[-1] else "    ")
        if node['_children']:
            print_tree(node['_children'], child_prefix, max_depth, depth + 1)


def search_topics(all_data, query):
    """Find papers matching a topic query."""
    query_lower = query.lower()
    results = []
    for conf, papers in all_data.items():
        for title, data in papers.items():
            for topic in data.get('topics', []):
                if query_lower in topic.lower():
                    results.append({
                        'title': title,
                        'topic': topic,
                        'conf': conf,
                        'year': data.get('year', 0),
                        'keywords': data.get('keywords', [])
                    })
                    break
    return sorted(results, key=lambda x: -x['year'])


def search_keywords(all_data, query):
    """Find papers matching a keyword."""
    query_lower = query.lower()
    results = []
    for conf, papers in all_data.items():
        for title, data in papers.items():
            matching_kw = [kw for kw in data.get('keywords', []) if query_lower in kw.lower()]
            if matching_kw:
                results.append({
                    'title': title,
                    'conf': conf,
                    'year': data.get('year', 0),
                    'keywords': data.get('keywords', []),
                    'topics': data.get('topics', []),
                    'matched': matching_kw
                })
    return sorted(results, key=lambda x: -x['year'])


def show_stats(all_data):
    """Show taxonomy statistics."""
    total_papers = 0
    all_topics = defaultdict(int)
    all_keywords = defaultdict(int)
    top_level = defaultdict(int)

    for conf, papers in all_data.items():
        total_papers += len(papers)
        for title, data in papers.items():
            for topic in data.get('topics', []):
                all_topics[topic] += 1
                top = topic.split('>')[0].strip()
                top_level[top] += 1
            for kw in data.get('keywords', []):
                all_keywords[kw.lower()] += 1

    print("=== Taxonomy Statistics ===")
    print()
    print("Classified papers: %d" % total_papers)
    print("Unique topic paths: %d" % len(all_topics))
    print("Unique keywords: %d" % len(all_keywords))
    print()

    print("Top-level domains:")
    for domain, count in sorted(top_level.items(), key=lambda x: -x[1]):
        print("  %-35s %d" % (domain, count))

    print()
    print("Top 20 keywords:")
    for kw, count in sorted(all_keywords.items(), key=lambda x: -x[1])[:20]:
        print("  %-35s %d" % (kw, count))

    print()
    print("Top 20 topic paths:")
    for topic, count in sorted(all_topics.items(), key=lambda x: -x[1])[:20]:
        print("  [%3d] %s" % (count, topic))


def main():
    parser = argparse.ArgumentParser(description='Browse paper taxonomy')
    parser.add_argument('--topic', type=str, help='Search by topic')
    parser.add_argument('--keyword', type=str, help='Search by keyword')
    parser.add_argument('--tree', action='store_true', help='Show topic tree')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--depth', type=int, default=3, help='Tree depth (default: 3)')
    args = parser.parse_args()

    all_data = load_all_taxonomies()
    if not all_data:
        print("No taxonomies found. Run classify.py first.")
        return

    total = sum(len(v) for v in all_data.values())
    print("Loaded %d classified papers from %d conferences." % (total, len(all_data)))
    print()

    if args.stats:
        show_stats(all_data)

    elif args.tree:
        tree = build_tree(all_data)
        print_tree(tree, max_depth=args.depth)

    elif args.topic:
        results = search_topics(all_data, args.topic)
        print("Found %d papers matching topic '%s':" % (len(results), args.topic))
        print()
        for r in results[:30]:
            print("[%d] [%s] %s" % (r['year'], r['conf'].upper(), r['title']))
            print("     Topic: %s" % r['topic'])
            print("     Keywords: %s" % ', '.join(r['keywords']))
            print()

    elif args.keyword:
        results = search_keywords(all_data, args.keyword)
        print("Found %d papers with keyword '%s':" % (len(results), args.keyword))
        print()
        for r in results[:30]:
            print("[%d] [%s] %s" % (r['year'], r['conf'].upper(), r['title']))
            print("     Topics: %s" % '; '.join(r['topics']))
            print("     Matched: %s" % ', '.join(r['matched']))
            print()

    else:
        # Interactive mode
        show_stats(all_data)
        print()
        print("Use --topic, --keyword, --tree, or --stats to explore.")


if __name__ == '__main__':
    main()
