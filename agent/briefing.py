import os, re
from datetime import datetime, timedelta, timezone
from anthropic import Anthropic
from dotenv import load_dotenv
from .db import get_conn

load_dotenv()
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-sonnet-5-5"
MAX_ARTICLES = 80

THEME_LABEL = {
    "tourism_strategy":          "National tourism strategy & visitor numbers",
    "destinations_gigaprojects": "Destinations & giga-project launches",
    "aviation_visa_entry":       "Aviation, visa & entry policy",
    "reputational_risk":         "Reputational risk & negative coverage",
}

SYSTEM_PROMPT = """You write the daily media briefing for the communications directorate of a
Saudi government tourism entity. The reader is the Director General: senior, busy, non-technical.

You will receive a numbered list of news items. Rules:
1. Use ONLY the items provided. Do not add facts, context or events that are not in the list.
2. Put a citation like [3] or [3][7] immediately after EVERY claim. A sentence without a
   citation is not allowed. Never cite a number that is not in the list.
3. If the same story appears in several outlets, mention it once and cite all of them.
4. British English, plain language, no jargon, no adjectives of praise.

Produce Markdown with exactly these four sections:

## Headline summary
Three lines maximum: the three things the Director General must know this morning.

## Coverage by theme
One sub-heading per theme that has items (use the theme labels given). Under each, 2–5
bullet points, each a one-sentence summary with citations. Skip themes with no items.

## Items requiring a response
Items that are negative or high-priority and may need a statement, correction or line to take.
For each: what was said, by whom, why it matters, in one or two sentences with citations.
If none, write "None identified in this period."

## Look-ahead
Only events, dates or decisions explicitly mentioned in the items as upcoming. Cite each.
If none, write "No scheduled items identified in the coverage."
"""

def fetch_articles(since_hours: int):
    conn = get_conn()
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=since_hours)).isoformat()
    rows = conn.execute("""
        SELECT id, outlet, title, link, summary, published_at, theme, sentiment, priority, justification
        FROM articles
        WHERE theme IS NOT NULL AND theme != 'not_relevant' AND published_at >= ?
        ORDER BY CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END,
                 published_at DESC
        LIMIT ?""", (cutoff, MAX_ARTICLES)).fetchall()
    conn.close()
    return rows

def build_item_list(rows) -> str:
    lines = []
    for i, r in enumerate(rows, start=1):
        lines.append(
            f"[{i}] ({THEME_LABEL[r['theme']]} | {r['sentiment']} | {r['priority']} priority)\n"
            f"    Outlet: {r['outlet']} | Published: {(r['published_at'] or '')[:16]}\n"
            f"    Headline: {r['title']}\n"
            f"    Summary: {(r['summary'] or '')[:300]}\n"
            f"    Classifier note (machine-generated, for context only, do not quote or attribute): {r['justification']}")
    return "\n\n".join(lines)

def check_citations(markdown: str, n_items: int) -> dict:
    """Every [n] in the text must be in 1..n_items. Anything else is a hallucinated citation."""
    cited = {int(x) for x in re.findall(r"\[(\d+)\]", markdown)}
    return {"cited": sorted(cited),
            "invalid": sorted(c for c in cited if c < 1 or c > n_items),
            "uncited_items": [i for i in range(1, n_items + 1) if i not in cited]}

def sources_section(rows) -> str:
    lines = ["## Sources"]
    for i, r in enumerate(rows, start=1):
        lines.append(f"[{i}] {r['outlet']} — {r['title']} — {r['link']}")
    return "\n".join(lines)

def generate_briefing(since_hours: int = 24) -> dict:
    rows = fetch_articles(since_hours)
    if not rows:
        return {"error": f"No classified relevant articles in the last {since_hours} hours."}

    date_str = datetime.now(timezone.utc).strftime("%A %d %B %Y")
    user_msg = (f"Date: {date_str}\nPeriod covered: last {since_hours} hours\n"
                f"Number of items: {len(rows)}\n\nITEMS:\n\n{build_item_list(rows)}")

    resp = client.messages.create(
        model=MODEL, max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}])
    body = "".join(b.text for b in resp.content if b.type == "text").strip()

    check = check_citations(body, len(rows))
    truncated = resp.stop_reason == "max_tokens"
    header = f"# Daily Media Briefing — {date_str}\n\n"
    if truncated:
        header += "> ⚠️ Review: the draft was cut short by the length limit; later sections may be missing.\n\n"
    if check["invalid"]:
        header += f"> ⚠️ Review: citations {check['invalid']} do not match any source item.\n\n"
    markdown = header + body + "\n\n" + sources_section(rows)

    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO briefings (created_at, since_hours, article_count, markdown) VALUES (?,?,?,?)",
        (datetime.now(timezone.utc).isoformat(), since_hours, len(rows), markdown))
    conn.commit()
    briefing_id = cur.lastrowid
    conn.close()

    return {"briefing_id": briefing_id, "articles": len(rows), "citation_check": check,
            "truncated": truncated, "stop_reason": resp.stop_reason,
            "tokens_in": resp.usage.input_tokens, "tokens_out": resp.usage.output_tokens,
            "markdown": markdown}


if __name__ == "__main__":
    import sys
    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    result = generate_briefing(hours)
    if "error" in result:
        print(result["error"]); sys.exit(1)
    print(result["markdown"])
    print("\n---")
    print({k: v for k, v in result.items() if k != "markdown"})