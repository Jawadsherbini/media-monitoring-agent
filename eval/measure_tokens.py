"""Measure average tokens per classification call, for the cost estimate."""
from agent.classify import client, MODEL, SYSTEM_PROMPT
from agent.db import get_conn

rows = get_conn().execute(
    "SELECT outlet, title, summary FROM articles ORDER BY RANDOM() LIMIT 10").fetchall()
tin = tout = 0
for r in rows:
    msg = f"Outlet: {r['outlet']}\nHeadline: {r['title']}\nSummary: {r['summary'] or '(none)'}"
    resp = client.messages.create(model=MODEL, max_tokens=200, system=SYSTEM_PROMPT,
                                  messages=[{"role": "user", "content": msg}])
    tin += resp.usage.input_tokens; tout += resp.usage.output_tokens
print(f"Average per classification: {tin/len(rows):.0f} input tokens, {tout/len(rows):.0f} output tokens")
