"""Draw a blind, stratified 30-item sample for hand labelling."""
import csv
from agent.db import get_conn

conn = get_conn()
q = ("SELECT id, outlet, title, summary FROM articles WHERE theme {} 'not_relevant' "
     "AND theme IS NOT NULL ORDER BY RANDOM() LIMIT 15")
rows = conn.execute(q.format("!=")).fetchall() + conn.execute(q.format("=")).fetchall()

with open("eval/sample.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "outlet", "title", "summary", "gold_theme", "gold_sentiment"])
    for r in rows:
        w.writerow([r["id"], r["outlet"], r["title"], (r["summary"] or "")[:300], "", ""])
print(f"Wrote {len(rows)} rows to eval/sample.csv — fill in gold_theme and gold_sentiment")