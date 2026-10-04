import os, secrets
from datetime import datetime, timezone
from typing import Literal
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from agent.db import get_conn
from agent.ingest import ingest
from agent.classify import classify_pending
from agent.briefing import generate_briefing

load_dotenv()
API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY is not set. Add API_KEY=... to .env (see .env.example).")

BRIEFING_COLUMNS = ("id, created_at, since_hours, article_count, status, "
                    "reviewed_by, reviewed_at, markdown")

def require_api_key(x_api_key: str = Header(default="")):
    # compare_digest avoids leaking the key through response timing
    if not secrets.compare_digest(x_api_key, API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def error_text(e: Exception) -> str:
    return f"{type(e).__name__}: {e}"

def get_briefing_row(briefing_id: int):
    conn = get_conn()
    row = conn.execute(f"SELECT {BRIEFING_COLUMNS} FROM briefings WHERE id=?",
                       (briefing_id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Briefing {briefing_id} not found")
    return dict(row)

class ReviewIn(BaseModel):
    decision: Literal["approved", "rejected"]
    reviewer: str = Field(min_length=1)
    notes: str | None = None    # accepted but not stored: briefings has no notes column

class AckIn(BaseModel):
    ids: list[str]

app = FastAPI(title="Media Monitoring Agent")
api = APIRouter(dependencies=[Depends(require_api_key)])   # everything except /health

@app.exception_handler(Exception)
def unexpected_error(request: Request, e: Exception):
    # Any uncaught error becomes a clean JSON 500 instead of a stack trace
    return JSONResponse(status_code=500, content={"error": error_text(e)})

# n8n: uptime check before the morning run (no auth)
@app.get("/health")
def health():
    conn = get_conn()
    articles = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    briefings = conn.execute("SELECT COUNT(*) FROM briefings").fetchone()[0]
    conn.close()
    return {"status": "ok", "articles": articles, "briefings": briefings}

# n8n: pull the latest RSS items on a schedule
@api.post("/ingest")
def run_ingest():
    return ingest()

# n8n: classify new articles after each ingest
@api.post("/classify")
def run_classify(limit: int = 200):
    return classify_pending(limit)

# n8n: generate a briefing on demand
@api.post("/briefing")
def run_briefing(since_hours: int = 24):
    result = generate_briefing(since_hours)
    if "error" in result:
        return JSONResponse(status_code=404, content=result)
    return result

# n8n: the single morning call — ingest, classify, brief
@api.post("/pipeline/daily")
def run_daily(since_hours: int = 24):
    steps = [("ingest", ingest),
             ("classify", lambda: classify_pending(limit=500)),
             ("briefing", lambda: generate_briefing(since_hours))]
    results = {}
    for name, step in steps:
        try:
            results[name] = step()
        except Exception as e:
            return JSONResponse(status_code=500, content={
                "error": error_text(e), "failed_step": name, "completed": results})
    if "error" in results["briefing"]:
        return JSONResponse(status_code=500, content={
            "error": results["briefing"]["error"], "failed_step": "briefing", "completed": results})
    return results

# n8n: fetch a briefing to send it for review or delivery
@api.get("/briefing/{briefing_id}")
def read_briefing(briefing_id: int):
    return get_briefing_row(briefing_id)

# n8n: record the reviewer's approve/reject decision
@api.post("/briefing/{briefing_id}/review")
def review_briefing(briefing_id: int, body: ReviewIn):
    get_briefing_row(briefing_id)            # 404 if missing
    conn = get_conn()
    conn.execute("UPDATE briefings SET status=?, reviewed_by=?, reviewed_at=? WHERE id=?",
                 (body.decision, body.reviewer, now_iso(), briefing_id))
    conn.commit()
    conn.close()
    return get_briefing_row(briefing_id)

# n8n: poll for high-risk articles that still need an alert sent
@api.get("/alerts/pending")
def pending_alerts():
    conn = get_conn()
    rows = conn.execute("""
        SELECT id, outlet, title, link, published_at, theme, justification
        FROM articles
        WHERE theme IS NOT NULL AND theme != 'not_relevant'
          AND sentiment = 'negative' AND priority = 'high' AND alerted_at IS NULL
        ORDER BY published_at DESC""").fetchall()
    conn.close()
    return [dict(r) for r in rows]

# n8n: mark alerts as sent so they are not repeated
@api.post("/alerts/ack")
def ack_alerts(body: AckIn):
    if not body.ids:
        return {"acknowledged": 0}
    placeholders = ",".join("?" * len(body.ids))
    conn = get_conn()
    # alerted_at IS NULL keeps the first alert time if an id is acked twice
    cur = conn.execute(
        f"UPDATE articles SET alerted_at=? WHERE alerted_at IS NULL AND id IN ({placeholders})",
        (now_iso(), *body.ids))
    conn.commit()
    conn.close()
    return {"acknowledged": cur.rowcount}

app.include_router(api)
