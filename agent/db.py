import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "media.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    id            TEXT PRIMARY KEY,
    outlet        TEXT,
    feed          TEXT,
    title         TEXT,
    link          TEXT,
    summary       TEXT,
    published_at  TEXT,
    fetched_at    TEXT,
    theme         TEXT,
    sentiment     TEXT,
    priority      TEXT,
    justification TEXT,
    classified_at TEXT,
    alerted_at    TEXT
);
CREATE TABLE IF NOT EXISTS briefings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at    TEXT,
    since_hours   INTEGER,
    article_count INTEGER,
    markdown      TEXT,
    status        TEXT DEFAULT 'draft',   -- draft | approved | rejected | delivered
    reviewed_by   TEXT,
    reviewed_at   TEXT
);
"""

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)       # executescript runs more than one statement
    return conn