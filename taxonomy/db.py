"""
SQLite database for paper taxonomy.

Stores papers, hierarchical topics, keywords, and their relationships.
Can be populated from pubs_* pickles and taxonomy_* classification results.

Usage:
    python taxonomy/db.py --init                    # create DB + import all pubs
    python taxonomy/db.py --import-taxonomy         # import taxonomy classifications
    python taxonomy/db.py --stats                   # show database stats
    python taxonomy/db.py --query "transformer"     # search papers
    python taxonomy/db.py --topic "Deep Learning"   # papers by topic
    python taxonomy/db.py --keyword "attention"     # papers by keyword
    python taxonomy/db.py --tree                    # topic tree
    python taxonomy/db.py --related "attention"     # keywords that co-occur
"""

import os
import sys
import sqlite3
import pickle
import argparse
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TAXONOMY_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TAXONOMY_DIR)
DB_PATH = os.path.join(TAXONOMY_DIR, "research.db")

ALL_CONFS = [
    'nips', 'acl', 'emnlp', 'cvpr', 'aaai', 'icml', 'iclr', 'ijcai', 'iccv',
    'naacl', 'interspeech', 'coling', 'eccv', 'ijcnlp', 'aistats', 'wacv',
    'jmlr', 'semeval', 'eacl', 'miccai', 'colt', 'conll', 'corl', 'rss',
    'uai', 'aacl', 'acml', 'nsdi', 'l4dc', 'midl', 'osdi', 'alt', 'mlhc',
    'pgm', 'clear', 'automl'
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    year INTEGER,
    venue TEXT,
    conf TEXT,
    pdf TEXT,
    authors TEXT,
    UNIQUE(title, venue)
);

CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    parent_id INTEGER REFERENCES topics(id),
    level INTEGER DEFAULT 0,
    full_path TEXT NOT NULL,
    UNIQUE(full_path)
);

CREATE TABLE IF NOT EXISTS keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS paper_topics (
    paper_id INTEGER REFERENCES papers(id),
    topic_id INTEGER REFERENCES topics(id),
    PRIMARY KEY (paper_id, topic_id)
);

CREATE TABLE IF NOT EXISTS paper_keywords (
    paper_id INTEGER REFERENCES papers(id),
    keyword_id INTEGER REFERENCES keywords(id),
    PRIMARY KEY (paper_id, keyword_id)
);

CREATE INDEX IF NOT EXISTS idx_papers_year ON papers(year);
CREATE INDEX IF NOT EXISTS idx_papers_conf ON papers(conf);
CREATE INDEX IF NOT EXISTS idx_papers_title ON papers(title);
CREATE INDEX IF NOT EXISTS idx_topics_parent ON topics(parent_id);
CREATE INDEX IF NOT EXISTS idx_topics_path ON topics(full_path);
CREATE INDEX IF NOT EXISTS idx_keywords_name ON keywords(name);
"""


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create database schema."""
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print("Database created at %s" % DB_PATH)


def import_papers():
    """Import all papers from pubs_* pickles."""
    conn = get_db()
    total = 0

    for conf in ALL_CONFS:
        pubs_path = os.path.join(PROJECT_DIR, "pubs_%s" % conf)
        if not os.path.exists(pubs_path):
            continue

        with open(pubs_path, 'rb') as f:
            pubs = pickle.load(f)

        rows = [
            (p.get('title', ''), p.get('year'), p.get('venue', ''),
             conf, p.get('pdf', ''), ', '.join(p.get('authors', [])))
            for p in pubs
        ]
        conn.executemany(
            "INSERT OR IGNORE INTO papers (title, year, venue, conf, pdf, authors) VALUES (?, ?, ?, ?, ?, ?)",
            rows
        )
        conn.commit()
        count = len(rows)
        total += count
        print("  %-12s %6d papers" % (conf, count))

    conn.close()
    print("Imported %d papers total." % total)


def get_or_create_topic(conn, full_path):
    """Get or create a topic from a path like 'Machine Learning > Deep Learning > GANs'."""
    row = conn.execute("SELECT id FROM topics WHERE full_path = ?", (full_path,)).fetchone()
    if row:
        return row['id']

    parts = [p.strip() for p in full_path.split('>')]
    parent_id = None

    for i, part in enumerate(parts):
        partial_path = ' > '.join(parts[:i+1])
        row = conn.execute("SELECT id FROM topics WHERE full_path = ?", (partial_path,)).fetchone()
        if row:
            parent_id = row['id']
        else:
            conn.execute(
                "INSERT INTO topics (name, parent_id, level, full_path) VALUES (?, ?, ?, ?)",
                (part, parent_id, i, partial_path)
            )
            parent_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    return parent_id


def get_or_create_keyword(conn, name):
    """Get or create a keyword."""
    name_lower = name.lower().strip()
    if not name_lower:
        return None
    row = conn.execute("SELECT id FROM keywords WHERE name = ?", (name_lower,)).fetchone()
    if row:
        return row['id']
    conn.execute("INSERT INTO keywords (name) VALUES (?)", (name_lower,))
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def import_taxonomy():
    """Import taxonomy classifications into DB."""
    conn = get_db()
    total = 0

    for conf in ALL_CONFS:
        tax_path = os.path.join(TAXONOMY_DIR, "taxonomy_%s" % conf)
        if not os.path.exists(tax_path):
            continue

        with open(tax_path, 'rb') as f:
            classified = pickle.load(f)

        count = 0
        for title, data in classified.items():
            # find paper in DB by (title, venue) to match UNIQUE constraint
            venue = data.get('venue', '')
            row = conn.execute(
                "SELECT id FROM papers WHERE title = ? AND venue = ?",
                (title, venue)
            ).fetchone()
            if not row:
                continue

            paper_id = row['id']

            # add topics
            for topic_path in data.get('topics', []):
                topic_id = get_or_create_topic(conn, topic_path)
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO paper_topics (paper_id, topic_id) VALUES (?, ?)",
                        (paper_id, topic_id)
                    )
                except sqlite3.Error:
                    pass

            # add keywords
            for kw in data.get('keywords', []):
                kw_id = get_or_create_keyword(conn, kw)
                if kw_id:
                    try:
                        conn.execute(
                            "INSERT OR IGNORE INTO paper_keywords (paper_id, keyword_id) VALUES (?, ?)",
                            (paper_id, kw_id)
                        )
                    except sqlite3.Error:
                        pass

            count += 1

        conn.commit()
        total += count
        print("  %-12s %6d classified" % (conf, count))

    conn.close()
    print("Imported %d classified papers total." % total)


def show_stats():
    """Show database statistics."""
    conn = get_db()
    papers = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
    classified = conn.execute("SELECT COUNT(DISTINCT paper_id) FROM paper_topics").fetchone()[0]
    topics = conn.execute("SELECT COUNT(*) FROM topics").fetchone()[0]
    keywords = conn.execute("SELECT COUNT(*) FROM keywords").fetchone()[0]
    confs = conn.execute("SELECT conf, COUNT(*) as cnt FROM papers GROUP BY conf ORDER BY cnt DESC").fetchall()

    print("=== Database Stats ===")
    print("Papers:     %6d" % papers)
    print("Classified: %6d" % classified)
    print("Topics:     %6d" % topics)
    print("Keywords:   %6d" % keywords)
    print()
    print("Papers per conference:")
    for row in confs:
        print("  %-12s %6d" % (row['conf'], row['cnt']))

    print()
    print("Top-level topics:")
    for row in conn.execute("""
        SELECT t.name, COUNT(pt.paper_id) as cnt
        FROM topics t
        JOIN paper_topics pt ON t.id = pt.topic_id
        WHERE t.level = 0
        GROUP BY t.id ORDER BY cnt DESC LIMIT 20
    """):
        print("  %-35s %d" % (row['name'], row['cnt']))

    print()
    print("Top keywords:")
    for row in conn.execute("""
        SELECT k.name, COUNT(pk.paper_id) as cnt
        FROM keywords k
        JOIN paper_keywords pk ON k.id = pk.keyword_id
        GROUP BY k.id ORDER BY cnt DESC LIMIT 20
    """):
        print("  %-35s %d" % (row['name'], row['cnt']))

    conn.close()


def search_papers(query):
    """Search papers by title."""
    conn = get_db()
    rows = conn.execute("""
        SELECT p.title, p.year, p.conf, p.venue,
               GROUP_CONCAT(DISTINCT t.full_path) as topics,
               GROUP_CONCAT(DISTINCT k.name) as keywords
        FROM papers p
        LEFT JOIN paper_topics pt ON p.id = pt.paper_id
        LEFT JOIN topics t ON pt.topic_id = t.id
        LEFT JOIN paper_keywords pk ON p.id = pk.paper_id
        LEFT JOIN keywords k ON pk.keyword_id = k.id
        WHERE p.title LIKE ?
        GROUP BY p.id
        ORDER BY p.year DESC
        LIMIT 30
    """, ('%%%s%%' % query,))

    for row in rows:
        print("[%s] [%s] %s" % (row['year'], row['conf'].upper(), row['title']))
        if row['topics']:
            print("     Topics: %s" % row['topics'])
        if row['keywords']:
            print("     Keywords: %s" % row['keywords'])
        print()

    conn.close()


def papers_by_topic(topic_query):
    """Find papers by topic path."""
    conn = get_db()
    rows = conn.execute("""
        SELECT p.title, p.year, p.conf, t.full_path,
               GROUP_CONCAT(DISTINCT k.name) as keywords
        FROM papers p
        JOIN paper_topics pt ON p.id = pt.paper_id
        JOIN topics t ON pt.topic_id = t.id
        LEFT JOIN paper_keywords pk ON p.id = pk.paper_id
        LEFT JOIN keywords k ON pk.keyword_id = k.id
        WHERE t.full_path LIKE ?
        GROUP BY p.id
        ORDER BY p.year DESC
        LIMIT 30
    """, ('%%%s%%' % topic_query,))

    results = rows.fetchall()
    print("Found %d papers matching topic '%s':" % (len(results), topic_query))
    print()
    for row in results:
        print("[%s] [%s] %s" % (row['year'], row['conf'].upper(), row['title']))
        print("     Topic: %s" % row['full_path'])
        if row['keywords']:
            print("     Keywords: %s" % row['keywords'])
        print()

    conn.close()


def papers_by_keyword(kw_query):
    """Find papers by keyword."""
    conn = get_db()
    rows = conn.execute("""
        SELECT p.title, p.year, p.conf,
               GROUP_CONCAT(DISTINCT t.full_path) as topics,
               GROUP_CONCAT(DISTINCT k.name) as keywords
        FROM papers p
        JOIN paper_keywords pk ON p.id = pk.paper_id
        JOIN keywords k ON pk.keyword_id = k.id
        LEFT JOIN paper_topics pt ON p.id = pt.paper_id
        LEFT JOIN topics t ON pt.topic_id = t.id
        WHERE k.name LIKE ?
        GROUP BY p.id
        ORDER BY p.year DESC
        LIMIT 30
    """, ('%%%s%%' % kw_query.lower(),))

    results = rows.fetchall()
    print("Found %d papers with keyword '%s':" % (len(results), kw_query))
    print()
    for row in results:
        print("[%s] [%s] %s" % (row['year'], row['conf'].upper(), row['title']))
        if row['topics']:
            print("     Topics: %s" % row['topics'])
        print()

    conn.close()


def related_keywords(kw_query):
    """Find keywords that co-occur with the given keyword."""
    conn = get_db()
    rows = conn.execute("""
        SELECT k2.name, COUNT(*) as cnt
        FROM keywords k1
        JOIN paper_keywords pk1 ON k1.id = pk1.keyword_id
        JOIN paper_keywords pk2 ON pk1.paper_id = pk2.paper_id
        JOIN keywords k2 ON pk2.keyword_id = k2.id
        WHERE k1.name LIKE ? AND k2.name != k1.name
        GROUP BY k2.id
        ORDER BY cnt DESC
        LIMIT 30
    """, ('%%%s%%' % kw_query.lower(),))

    results = rows.fetchall()
    print("Keywords related to '%s':" % kw_query)
    print()
    for row in results:
        print("  [%3d] %s" % (row['cnt'], row['name']))

    conn.close()


def show_tree(max_depth=2):
    """Show topic tree from DB."""
    conn = get_db()

    def print_children(parent_id, prefix, depth):
        if depth >= max_depth:
            return
        rows = conn.execute("""
            SELECT t.id, t.name, COUNT(pt.paper_id) as cnt
            FROM topics t
            LEFT JOIN paper_topics pt ON t.id = pt.topic_id
            WHERE t.parent_id IS ?
            GROUP BY t.id
            ORDER BY cnt DESC
        """, (parent_id,)).fetchall()

        for i, row in enumerate(rows):
            is_last = i == len(rows) - 1
            connector = "└── " if is_last else "├── "
            print("%s%s%s (%d)" % (prefix, connector, row['name'], row['cnt']))
            child_prefix = prefix + ("    " if is_last else "│   ")
            print_children(row['id'], child_prefix, depth + 1)

    print_children(None, "", 0)
    conn.close()


def main():
    parser = argparse.ArgumentParser(description='Research paper taxonomy database')
    parser.add_argument('--init', action='store_true', help='Create DB and import papers')
    parser.add_argument('--import-taxonomy', action='store_true', help='Import taxonomy classifications')
    parser.add_argument('--stats', action='store_true', help='Show stats')
    parser.add_argument('--query', type=str, help='Search papers by title')
    parser.add_argument('--topic', type=str, help='Papers by topic')
    parser.add_argument('--keyword', type=str, help='Papers by keyword')
    parser.add_argument('--related', type=str, help='Related keywords')
    parser.add_argument('--tree', action='store_true', help='Show topic tree')
    parser.add_argument('--depth', type=int, default=2, help='Tree depth')
    args = parser.parse_args()

    if args.init:
        init_db()
        import_papers()
    elif args.import_taxonomy:
        import_taxonomy()
    elif args.stats:
        show_stats()
    elif args.query:
        search_papers(args.query)
    elif args.topic:
        papers_by_topic(args.topic)
    elif args.keyword:
        papers_by_keyword(args.keyword)
    elif args.related:
        related_keywords(args.related)
    elif args.tree:
        show_tree(args.depth)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
