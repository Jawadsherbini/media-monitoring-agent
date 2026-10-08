"""Measure average tokens per classification call, for the cost estimate."""
from agent.classify import client, MODEL, SYSTEM_PROMPT
from agent.db import get_conn

rows = get_conn().execute(
    "SELECT outlet, title, summary FROM articles ORDER BY RANDOM() LIMIT 10").fetchall()
tin = tout = 0
cached = created = 0
for r in rows:
    msg = f"Outlet: {r['outlet']}\nHeadline: {r['title']}\nSummary: {r['summary'] or '(none)'}"
    resp = client.messages.create(model=MODEL, max_tokens=200, system=SYSTEM_PROMPT,
                                  messages=[{"role": "user", "content": msg}])
    tin += resp.usage.input_tokens; tout += resp.usage.output_tokens
    cached += getattr(resp.usage, "cache_read_input_tokens", 0) or 0
    created += getattr(resp.usage, "cache_creation_input_tokens", 0) or 0
print(f"Average per classification: {tin/len(rows):.0f} input tokens ({cached/len(rows):.0f} read from cache, {created/len(rows):.0f} written to cache), {tout/len(rows):.0f} output tokens")
