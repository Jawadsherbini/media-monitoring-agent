"""Ask a plain-language question of the coverage archive.

Retrieval is deliberately simple: keyword match in SQLite, ranked by how many of the
question's keywords an article matches. The answer is grounded in the retrieved articles
only, with the same citation check as the daily briefing.

Usage:  python -m agent.ask "What has been written about visa changes this week and by whom?" [days]
"""
import re, sys
from datetime import datetime, timedelta, timezone
from .llm import client
from .db import get_conn
from .briefing import build_item_list, check_citations, sources_section

MODEL = "claude-sonnet-5-5"
MAX_ITEMS = 20
STOPWORDS = {"what", "has", "have", "been", "written", "about", "this", "week", "month", "and",
             "the", "who", "whom", "which", "were", "was", "are", "did", "does", "any", "there",
             "saudi", "arabia", "news", "coverage", "said", "say", "from", "with", "for", "that",
             "being", "reported", "reporting", "anything", "something", "recent", "recently",
             "latest", "lately", "today", "yesterday", "tell", "give", "show", "know"}

SYSTEM_PROMPT = """You answer questions from a communications analyst using ONLY the numbered
news items provided. Rules:
1. Every claim must carry a citation like [3]. Never cite a number not in the list.
2. If the items do not answer the question, say so plainly. Do not add outside knowledge.
3. When asked "by whom" or "which outlets", name the outlets.
4. Be concise: a short paragraph or a few bullets, British English."""

def keywords(question: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", question.lower())
    return [w for w in words if len(w) > 2 and w not in STOPWORDS]

def retrieve(question: str, days: int):
    kws = keywords(question)
    if not kws:
        return [], kws
    conn = get_conn()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    clauses = " OR ".join("(lower(title) LIKE ? OR lower(summary) LIKE ?)" for _ in kws)
    params = [p for k in kws for p in (f"%{k}%", f"%{k}%")]
    rows = conn.execute(f"""
        SELECT id, outlet, title, link, summary, published_at, theme, sentiment, priority, justification
        FROM articles
        WHERE theme IS NOT NULL AND theme != 'not_relevant' AND published_at >= ? AND ({clauses})
        ORDER BY published_at DESC""", [cutoff, *params]).fetchall()
    conn.close()
    # rank by how many distinct keywords each article matches, newest first on ties
    phrase = " ".join(kws)
    def score(r):
        text = f"{r['title']} {r['summary'] or ''}".lower()
        return sum(k in text for k in kws) + (3 if phrase in text else 0)
    rows = sorted(rows, key=lambda r: (-score(r), r["published_at"] or ""))
    return rows[:MAX_ITEMS], kws

def ask(question: str, days: int = 7) -> dict:
    rows, kws = retrieve(question, days)
    if not rows:
        return {"answer": f"No relevant articles in the last {days} days matched: {', '.join(kws) or '(no keywords)'}.",
                "articles": 0}
    user_msg = (f"Question: {question}\nPeriod: last {days} days\n\nITEMS:\n\n{build_item_list(rows)}")
    resp = client.messages.create(model=MODEL, max_tokens=3000, system=SYSTEM_PROMPT,
                                  messages=[{"role": "user", "content": user_msg}])
    answer = "".join(b.text for b in resp.content if b.type == "text").strip()
    check = check_citations(answer, len(rows))
    if check["invalid"]:
        answer = f"> ⚠️ Review: citations {check['invalid']} do not match any retrieved item.\n\n" + answer
    return {"answer": answer + "\n\n" + sources_section(rows), "articles": len(rows),
            "keywords": kws, "citation_check": check}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit('Usage: python -m agent.ask "your question" [days]')
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    result = ask(sys.argv[1], days)
    print(result["answer"])
    print("\n---", {k: v for k, v in result.items() if k != "answer"})