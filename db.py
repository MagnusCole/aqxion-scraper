import sqlite3
from contextlib import contextmanager

DB_PATH = "scraping.db"

DDL = """
CREATE TABLE IF NOT EXISTS posts (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    url TEXT NOT NULL,
    title TEXT,
    body TEXT,
    lang TEXT,
    created_at TEXT NOT NULL,
    keyword TEXT,
    tag TEXT,
    published_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at);
CREATE INDEX IF NOT EXISTS idx_posts_tag ON posts(tag);
CREATE INDEX IF NOT EXISTS idx_posts_keyword ON posts(keyword);
CREATE INDEX IF NOT EXISTS idx_posts_published ON posts(published_at);
"""

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    yield conn
    conn.close()

def init_db():
    with get_conn() as c:
        c.executescript(DDL)

def upsert_post(p):
    with get_conn() as c:
        c.execute("""
        INSERT OR REPLACE INTO posts(id, source, url, title, body, lang, created_at, keyword, tag, published_at)
        VALUES(:id, :source, :url, :title, :body, :lang, :created_at, :keyword, :tag, :published_at)
        """, p)
        c.commit()
