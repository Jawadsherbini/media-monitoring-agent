import re, hashlib, html
from datetime import datetime, timezone
import requests, feedparser
from .sources import SOURCES
from .db import get_conn

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh) MediaMonitor/0.1"}

def normalise_title(title: str) -> str:
    """Lowercase, drop the ' - Outlet' suffix Google News adds, strip punctuation."""
    title = title.rsplit(" - ", 1)[0] if " - " in title else title
    title = re.sub(r"[^a-z0-9 ]", "", title.lower())
    return re.sub(r"\s+", " ", title).strip()

def make_id(title: str) -> str:
    return hashlib.sha1(normalise_title(title).encode()).hexdigest()

def clean_text(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()

def to_iso(entry) -> str | None:
    t = entry.get("published_parsed") or entry.get("updated_parsed")
    return datetime(*t[:6], tzinfo=timezone.utc).isoformat() if t else None

def fetch_feed(name: str, url: str):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return feedparser.parse(r.content).entries

def ingest() -> dict:
    conn = get_conn()
    now = datetime.now(timezone.utc).isoformat()
    stats = {"fetched": 0, "new": 0, "duplicates": 0, "failed_feeds": []}

    for name, url in SOURCES.items():
        try:
            entries = fetch_feed(name, url)
        except Exception as e:
            stats["failed_feeds"].append(f"{name}: {type(e).__name__}")
            continue

        for e in entries:
            stats["fetched"] += 1
            title = clean_text(e.get("title", ""))
            if not title:
                continue
            # Google News items carry the real publisher in e.source.title
            outlet = e.get("source", {}).get("title") or name.split(":")[-1].strip()
            row = (make_id(title), outlet, name, title, e.get("link"),
                   clean_text(e.get("summary", ""))[:1000], to_iso(e), now)
            cur = conn.execute(
                "INSERT OR IGNORE INTO articles "
                "(id, outlet, feed, title, link, summary, published_at, fetched_at) "
                "VALUES (?,?,?,?,?,?,?,?)", row)
            stats["new" if cur.rowcount else "duplicates"] += 1

    conn.commit()
    conn.close()
    return stats

if __name__ == "__main__":
    print(ingest())