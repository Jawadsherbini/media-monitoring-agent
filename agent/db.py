import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "media.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    id            TEXT PRIMARY KEY,   -- hash of the normalised title
    outlet        TEXT,               -- publisher name
    feed          TEXT,               -- which feed we got it from
    title         TEXT,
    link          TEXT,
    summary       TEXT,
    published_at  TEXT,               -- ISO timestamp from the feed
    fetched_at    TEXT,               -- when we saved it
    -- filled in by classify.py (Monday)
    theme         TEXT,
    sentiment     TEXT,
    priority      TEXT,
    justification TEXT,
    classified_at TEXT,
    alerted_at    TEXT
);
"""

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row      # lets us access columns by name
    conn.execute(SCHEMA)
    return conn