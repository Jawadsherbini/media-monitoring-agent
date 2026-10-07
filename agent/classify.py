import json
from datetime import datetime, timezone
from anthropic import AuthenticationError
from .db import get_conn
from .llm import client

MODEL = "claude-haiku-4-5-20251001"

THEMES = ["tourism_strategy", "destinations_gigaprojects", "aviation_visa_entry",
          "reputational_risk", "not_relevant"]

SYSTEM_PROMPT = """You classify news items for the communications team of a Saudi
government tourism entity. Return ONLY a JSON object, no other text.

Themes (choose exactly one):
- tourism_strategy: national tourism strategy, visitor numbers, targets, tourism economy
- destinations_gigaprojects: destination and giga-project launches (NEOM, Red Sea, Diriyah, AlUla, Qiddiya etc.)
- aviation_visa_entry: airlines, airports, visas, entry policy, travel rules
- reputational_risk: coverage that criticises or embarrasses the Saudi tourism sector ITSELF: incidents at tourist sites or hotels, cancelled or failing projects, visitor complaints, safety or environmental or labour criticism of tourism projects, negative international press about visiting Saudi Arabia
- not_relevant: anything not about Saudi tourism, travel or destinations. This includes regional conflict, politics, sports results, weather, and other countries. Regional instability is NOT reputational_risk unless the article itself links it to tourism or visitors.

Rule: when in doubt, choose not_relevant. The team would rather miss a marginal item than read noise.

sentiment: "positive" | "neutral" | "negative"  (towards the Saudi tourism sector)
priority:  "high" | "medium" | "low"  (how urgently the directorate should see it)
justification: one sentence, max 25 words.

Format: {"theme": "...", "sentiment": "...", "priority": "...", "justification": "..."}"""

def classify_article(outlet: str, title: str, summary: str) -> dict:
    user_msg = f"Outlet: {outlet}\nHeadline: {title}\nSummary: {summary or '(none)'}"
    resp = client.messages.create(
        
        model=MODEL, max_tokens=200, extra_body={"temperature": 0},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text")
    text = text.strip().strip("`").removeprefix("json").strip()
    result = json.loads(text)
    if result.get("theme") not in THEMES:          # guard against made-up labels
        result["theme"] = "not_relevant"
    return result

SECTOR_THEMES = {"tourism_strategy", "destinations_gigaprojects",
                 "aviation_visa_entry", "reputational_risk"}

def is_high_risk(row) -> bool:
    """Negative, urgent, and about the sector — regardless of which theme it sits under."""
    return (row["theme"] in SECTOR_THEMES
            and row["sentiment"] == "negative"
            and row["priority"] == "high")

def classify_pending(limit: int = 50) -> dict:
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, outlet, title, summary FROM articles "
        "WHERE theme IS NULL ORDER BY published_at DESC LIMIT ?", (limit,)).fetchall()
    stats = {"classified": 0, "errors": 0, "high_risk": 0}
    for r in rows:
        try:
            c = classify_article(r["outlet"], r["title"], r["summary"])
        except AuthenticationError:
            conn.close()
            raise RuntimeError("Anthropic rejected the API key. Check ANTHROPIC_API_KEY in .env.")
        except Exception as e:
            stats["errors"] += 1
            print(f"ERROR {r['id'][:8]} {type(e).__name__}: {e}")
            continue
        conn.execute(
            "UPDATE articles SET theme=?, sentiment=?, priority=?, justification=?, "
            "classified_at=? WHERE id=?",
            (c["theme"], c["sentiment"], c["priority"], c["justification"],
             datetime.now(timezone.utc).isoformat(), r["id"]))
        conn.commit()
        stats["classified"] += 1
        if is_high_risk(c):
            stats["high_risk"] += 1
    conn.close()
    return stats

if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    print(classify_pending(limit=limit))
