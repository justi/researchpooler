"""
Paper taxonomy classifier using OpenCode CLI.

Classifies papers from pubs_* pickle files into a hierarchical topic taxonomy.
Uses OpenCode's default model to extract topics and keywords from paper titles.
Processes papers in batches to be efficient with API calls.

Usage:
    python taxonomy/classify.py                    # classify all conferences
    python taxonomy/classify.py --conf nips        # classify one conference
    python taxonomy/classify.py --conf nips --limit 100  # first 100 papers
    python taxonomy/classify.py --resume           # resume from last checkpoint
"""

import os
import sys
import json
import pickle
import subprocess
import argparse
import time
import yaml

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repool_util import loadPubs

TAXONOMY_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TAXONOMY_DIR)
CONFIG_PATH = os.path.join(TAXONOMY_DIR, "config.yaml")
BATCH_SIZE = 20  # papers per API call
CHECKPOINT_EVERY = 5  # save after every N batches


def load_taxonomy_config():
    """Load taxonomy config.yaml and flatten to list of allowed topic paths."""
    if not os.path.exists(CONFIG_PATH):
        return None

    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    paths = []

    def walk(node, prefix=""):
        if isinstance(node, list):
            for item in node:
                paths.append((prefix + " > " + item).strip(" > "))
        elif isinstance(node, dict):
            for key, val in node.items():
                new_prefix = (prefix + " > " + key).strip(" > ")
                if val is None:
                    paths.append(new_prefix)
                else:
                    walk(val, new_prefix)

    walk(config)
    return paths

ALL_CONFS = [
    'nips', 'acl', 'emnlp', 'cvpr', 'aaai', 'icml', 'iclr', 'ijcai', 'iccv',
    'naacl', 'interspeech', 'coling', 'eccv', 'ijcnlp', 'aistats', 'wacv',
    'jmlr', 'semeval', 'eacl', 'miccai', 'colt', 'conll', 'corl', 'rss',
    'uai', 'aacl', 'acml', 'nsdi', 'l4dc', 'midl', 'osdi', 'alt', 'mlhc',
    'pgm', 'clear', 'automl'
]


def classify_batch(papers_data, allowed_topics=None):
    """Send a batch of papers (title + optional abstract) to OpenCode for classification.

    papers_data: list of dicts with 'title' and optionally 'abstract'
    """
    parts = []
    for i, pd in enumerate(papers_data):
        title = pd['title']
        abstract = pd.get('abstract', '')
        if abstract:
            parts.append('%d. Title: "%s"\n   Abstract: %s' % (i+1, title, abstract[:300]))
        else:
            parts.append('%d. "%s"' % (i+1, title))
    titles_text = "\n".join(parts)

    keyword_rules = """KEYWORD RULES (strict):
- Each keyword must be at least 2 space-separated words (e.g. "image restoration" not "regularization", "bioinformatics", or "super-resolution")
- Use full forms, never abbreviations (e.g. "reinforcement learning" not "RL", "graph neural networks" not "GNN")
- Use lowercase
- Be specific: "variational inference" not "bayesian", "object detection" not "detection"
- No keyword should be a substring of another keyword for the same paper (e.g. don't output both "feature learning" and "multi-task feature learning" — keep only the more specific one)
- Prefer established terms (e.g. "domain adaptation" not "domain shifting")"""

    if allowed_topics:
        topics_list = "\n".join("- %s" % t for t in allowed_topics)
        prompt = """Respond with ONLY valid JSON, no other text or markdown.
Classify these paper titles. For each paper:
- topics: pick 1-3 topic paths from the ALLOWED LIST below. Use the EXACT path strings. Only if nothing fits at all, use "Other".
- keywords: list of 3-6 specific keywords following the rules below.

%s

ALLOWED TOPICS:
%s

Titles:
%s

Return format: {"papers": [{"idx": 1, "topics": ["..."], "keywords": ["..."]}]}""" % (keyword_rules, topics_list, titles_text)
    else:
        prompt = """Respond with ONLY valid JSON, no other text or markdown.
Classify these paper titles into a topic hierarchy. For each paper give:
- topics: list of topic paths using ">" separator (max 3 levels, e.g. "Machine Learning > Deep Learning > Transformers")
- keywords: list of 3-6 specific keywords following the rules below.

%s

Titles:
%s

Return format: {"papers": [{"idx": 1, "topics": ["..."], "keywords": ["..."]}]}""" % (keyword_rules, titles_text)

    cmd = ["opencode", "run", "--format", "json", prompt]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=PROJECT_DIR
        )

        if result.returncode != 0:
            print("  opencode exited with code %d" % result.returncode)
            if result.stderr:
                print("  stderr: %s" % result.stderr.strip())
            return None

        # Parse JSONL output, find text event
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
                if event.get('type') == 'text':
                    text = event['part']['text']
                    # Clean potential markdown wrapping
                    text = text.strip()
                    if text.startswith('```'):
                        text = text.split('\n', 1)[1] if '\n' in text else text
                        text = text.rsplit('```', 1)[0] if '```' in text else text
                        text = text.strip()
                    return json.loads(text)
            except (json.JSONDecodeError, KeyError):
                continue

    except subprocess.TimeoutExpired:
        print("  timeout on batch, skipping...")
    except Exception as e:
        print("  error: %s" % e)

    return None


def load_checkpoint(conf_name):
    """Load classification checkpoint for a conference."""
    path = os.path.join(TAXONOMY_DIR, "checkpoint_%s.json" % conf_name)
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {"classified": {}, "last_index": 0}


def save_checkpoint(conf_name, data):
    """Save classification checkpoint."""
    path = os.path.join(TAXONOMY_DIR, "checkpoint_%s.json" % conf_name)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_taxonomy(conf_name, classified):
    """Save final taxonomy as pickle."""
    path = os.path.join(TAXONOMY_DIR, "taxonomy_%s" % conf_name)
    with open(path, 'wb') as f:
        pickle.dump(classified, f)
    print("  saved taxonomy_%s (%d papers)" % (conf_name, len(classified)))


def build_topic_index(all_classified):
    """Build an index of topics -> papers from all classified papers."""
    topic_index = {}  # topic_path -> list of (conf, title, year)

    for conf, papers in all_classified.items():
        for title, data in papers.items():
            for topic in data.get('topics', []):
                if topic not in topic_index:
                    topic_index[topic] = []
                topic_index[topic].append({
                    'conf': conf,
                    'title': title,
                    'year': data.get('year', 0),
                    'keywords': data.get('keywords', [])
                })

    return topic_index


def build_keyword_index(all_classified):
    """Build an index of keywords -> papers."""
    kw_index = {}

    for conf, papers in all_classified.items():
        for title, data in papers.items():
            for kw in data.get('keywords', []):
                kw_lower = kw.lower()
                if kw_lower not in kw_index:
                    kw_index[kw_lower] = []
                kw_index[kw_lower].append({
                    'conf': conf,
                    'title': title,
                    'year': data.get('year', 0)
                })

    return kw_index


def classify_conference(conf_name, limit=None, resume=False):
    """Classify all papers from a conference."""
    pubs_path = os.path.join(PROJECT_DIR, "pubs_%s" % conf_name)
    if not os.path.exists(pubs_path):
        print("pubs_%s not found, skipping" % conf_name)
        return {}

    pubs = loadPubs(pubs_path)
    if limit:
        pubs = pubs[:limit]

    # Load taxonomy config if available
    allowed_topics = load_taxonomy_config()
    if allowed_topics:
        print("Using config.yaml (%d allowed topics)" % len(allowed_topics))
    else:
        print("No config.yaml found, using free-form classification")

    # Load checkpoint
    checkpoint = load_checkpoint(conf_name) if resume else {"classified": {}, "last_index": 0}
    classified = checkpoint["classified"]
    start_idx = checkpoint["last_index"] if resume else 0

    remaining = [(i, p) for i, p in enumerate(pubs)
                 if "%s|||%s" % (p['title'], p.get('venue', '')) not in classified]
    if start_idx > 0:
        remaining = [(i, p) for i, p in remaining if i >= start_idx]

    if not remaining:
        print("%s: all %d papers already classified" % (conf_name, len(classified)))
        return classified

    print("%s: %d papers to classify (%d already done)" % (
        conf_name, len(remaining), len(classified)))

    batches_since_save = 0
    for batch_start in range(0, len(remaining), BATCH_SIZE):
        batch = remaining[batch_start:batch_start + BATCH_SIZE]
        papers_data = [{'title': p['title'], 'abstract': p.get('abstract', '')} for _, p in batch]
        has_abstracts = sum(1 for pd in papers_data if pd['abstract'])

        print("  batch %d/%d (%d papers, %d with abstracts)..." % (
            batch_start // BATCH_SIZE + 1,
            (len(remaining) + BATCH_SIZE - 1) // BATCH_SIZE,
            len(papers_data),
            has_abstracts
        ))

        result = classify_batch(papers_data, allowed_topics)

        if result and 'papers' in result:
            for item in result['papers']:
                idx = item.get('idx', 0) - 1
                if 0 <= idx < len(batch):
                    orig_idx, pub = batch[idx]
                    key = "%s|||%s" % (pub['title'], pub.get('venue', ''))
                    classified[key] = {
                        'topics': item.get('topics', []),
                        'keywords': item.get('keywords', []),
                        'year': pub.get('year', 0),
                        'venue': pub.get('venue', ''),
                        'authors': pub.get('authors', []),
                        'title': pub['title']
                    }

            checkpoint["last_index"] = batch[-1][0] + 1

        batches_since_save += 1
        if batches_since_save >= CHECKPOINT_EVERY:
            checkpoint["classified"] = classified
            save_checkpoint(conf_name, checkpoint)
            batches_since_save = 0
            print("  checkpoint saved (%d classified)" % len(classified))

        # small delay between API calls
        time.sleep(1)

    # final save
    checkpoint["classified"] = classified
    save_checkpoint(conf_name, checkpoint)
    save_taxonomy(conf_name, classified)

    return classified


def main():
    parser = argparse.ArgumentParser(description='Classify papers into topic taxonomy')
    parser.add_argument('--conf', type=str, help='Conference to classify (e.g. nips)')
    parser.add_argument('--limit', type=int, help='Max papers to classify')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--build-index', action='store_true', help='Build topic/keyword index from existing taxonomies')
    args = parser.parse_args()

    if args.build_index:
        print("Building indexes from existing taxonomies...")
        all_classified = {}
        for conf in ALL_CONFS:
            tax_path = os.path.join(TAXONOMY_DIR, "taxonomy_%s" % conf)
            if os.path.exists(tax_path):
                with open(tax_path, 'rb') as f:
                    all_classified[conf] = pickle.load(f)
                print("  loaded taxonomy_%s (%d papers)" % (conf, len(all_classified[conf])))

        topic_index = build_topic_index(all_classified)
        kw_index = build_keyword_index(all_classified)

        with open(os.path.join(TAXONOMY_DIR, "topic_index.json"), 'w') as f:
            json.dump(topic_index, f, indent=2, ensure_ascii=False)
        with open(os.path.join(TAXONOMY_DIR, "keyword_index.json"), 'w') as f:
            json.dump(kw_index, f, indent=2, ensure_ascii=False)

        print("\nTopic index: %d topics" % len(topic_index))
        print("Keyword index: %d keywords" % len(kw_index))
        print("\nTop 20 topics by paper count:")
        for topic, papers in sorted(topic_index.items(), key=lambda x: -len(x[1]))[:20]:
            print("  [%4d] %s" % (len(papers), topic))
        return

    confs = [args.conf] if args.conf else ALL_CONFS

    for conf in confs:
        classify_conference(conf, limit=args.limit, resume=args.resume)


if __name__ == '__main__':
    main()
