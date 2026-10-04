import requests, feedparser
from agent.sources import SOURCES

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh) MediaMonitor/0.1"}

for name, url in SOURCES.items():
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        feed = feedparser.parse(r.content)
        status = f"HTTP {r.status_code}"
    except Exception as e:
        feed, status = feedparser.parse(""), f"ERROR {type(e).__name__}"
    print(f"{name:28} {len(feed.entries):4} items   {status}")