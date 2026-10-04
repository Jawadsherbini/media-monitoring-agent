"""Compare hand labels with model labels."""
import csv
from agent.db import get_conn

conn = get_conn()
rows = list(csv.DictReader(open("eval/sample.csv")))
theme_ok = sent_ok = n = 0
mistakes = []
for r in rows:
    if not r["gold_theme"]:
        continue
    pred = conn.execute("SELECT theme, sentiment FROM articles WHERE id=?", (r["id"],)).fetchone()
    n += 1
    theme_ok += pred["theme"] == r["gold_theme"]
    sent_ok  += pred["sentiment"] == r["gold_sentiment"]
    if pred["theme"] != r["gold_theme"]:
        mistakes.append(f"  {r['title'][:60]} | model={pred['theme']} gold={r['gold_theme']}")
    if pred["sentiment"] != r["gold_sentiment"]:
        mistakes.append(f"  [sentiment] {r['title'][:60]} | model={pred['sentiment']} gold={r['gold_sentiment']}")

print(f"Labelled: {n}\nTheme accuracy:     {theme_ok/n:.0%}\nSentiment accuracy: {sent_ok/n:.0%}")
print("Theme mistakes:\n" + "\n".join(mistakes))