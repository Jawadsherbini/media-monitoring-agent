# Media Monitoring Agent

An agentic pipeline that replaces a manual three-hour daily media review for a government
communications directorate. It ingests news, classifies every item against the directorate's
priority themes, drafts a fully cited daily briefing for **human approval**, delivers the approved
version on a schedule, and raises batched alerts within 15 minutes when high-risk coverage appears.

Built in Python + Anthropic Claude + n8n. Runs entirely on one machine; nothing leaves the
environment except article text sent to the LLM API.

```
RSS feeds ──► ingest ──► de-dup ──► classify (Haiku) ──► SQLite ──► draft briefing (Sonnet)
                                        │                               │
                                        │                               ▼
                                        │                   n8n: email draft to analyst
                                        │                        WAIT for approval form
                                        │                        approved ──► email DG office
                                        │                        rejected ──► notify analyst
                                        ▼
                            n8n (every 10 min): new high-risk items ──► ONE alert email
                            ask.py: "What was written about visas this week?" ──► grounded answer
```

## Quick start (under 15 minutes)

Requirements: Python 3.11+, Node.js 20+ (for n8n), an Anthropic API key, a Gmail address with
an app password (for sending email).

```bash
# 1. Clone and install (≈2 min)
git clone https://github.com/Jawadsherbini/media-monitoring-agent.git
cd media-monitoring-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Open .env and replace BOTH placeholder values:
#   ANTHROPIC_API_KEY = your key from console.anthropic.com
#   API_KEY           = any long random string (n8n will use it to call the API)
# The pipeline refuses to start while a placeholder is still there.

# 3. Load data and produce a first briefing (≈3 min)
python check_feeds.py              # optional: confirms all 12 sources respond
python -m agent.ingest             # fetch + de-duplicate into media.db
python -m agent.classify 150       # classify the 150 most recent items
python -m agent.briefing 72        # draft a briefing from the last 72 hours, printed to screen

# 4. Start the API (leave running)
uvicorn api:app --port 8000
```

Then n8n, in a second terminal (first start downloads n8n, ≈3 min):

```bash
npx n8n            # open http://localhost:5678 and create the local owner account
```

In n8n:
1. **Credentials → Add**: *Header Auth* with Name `X-API-Key`, Value = your `API_KEY` from `.env`.
   Use `127.0.0.1`, not `localhost`, in any URL you type into n8n: recent Node versions resolve
   `localhost` to IPv6 while the API listens on IPv4.
2. **Credentials → Add**: *SMTP* with your Gmail address, app password, host `smtp.gmail.com`, port 465, SSL on.
3. **⋯ → Import from file** → `n8n/risk-alerts.json`, then `n8n/daily-briefing.json`. Open each
   HTTP Request node and select the Header Auth credential; open each Send Email node and select
   the SMTP credential and set From/To to your address.
4. Open **Daily briefing** → **Execute workflow**. Within 1–3 minutes you receive the draft by
   email; open the form link (on the same machine), approve, and the formatted briefing arrives
   at `<you>+dg@gmail.com`.
5. Open **Risk alerts** → **Execute workflow**. Pending high-risk items arrive as one email.

Set each workflow's timezone (⋯ → Settings) to `Asia/Riyadh` before publishing the schedules.

## Ask the archive (requirement 6, simplest form)

```bash
python -m agent.ask "What has been written about visa changes this week and by whom?" 7
```

Keyword retrieval from SQLite over the last N days (default 7), ranked by keyword and phrase
matches, then Claude Sonnet answers using only the retrieved items, with the same citation check
as the briefing. It names outlets, says when the items don't answer the question, and refuses to
add outside facts. Known limitation: keyword search misses synonyms and matches substrings
("air" also finds "airport"); the next step is embedding-based retrieval.

## Repository layout

| Path | What it is |
|---|---|
| `agent/sources.py` | The 12 feeds: 4 direct RSS, 5 per-outlet Google News feeds, 3 topic feeds |
| `agent/ingest.py` | Fetch, clean, de-duplicate (normalised-title hash), save |
| `agent/classify.py` | Theme / sentiment / priority / justification via Claude Haiku; the high-risk rule |
| `agent/briefing.py` | Cited briefing via Claude Sonnet; citation and truncation checks |
| `agent/ask.py` | Plain-language questions over the archive: keyword retrieval + grounded, cited answer |
| `agent/db.py` | SQLite schema (`articles`, `briefings`) |
| `api.py` | FastAPI endpoints n8n calls; API-key auth; clean JSON errors |
| `n8n/*.json` | The two exported workflows |
| `eval/` | Hand-labelled evaluation set, scoring script, results, token measurement |
| `docs/architecture.md` | One-page architecture note |
| `DECISIONS.md` | Every design decision and its trade-off, in order |

## API endpoints (what n8n presses)

| Endpoint | Purpose |
|---|---|
| `GET /health` | Liveness check (no auth) |
| `POST /ingest` | Fetch feeds, de-duplicate, store |
| `POST /classify?limit=N` | Classify unclassified items |
| `POST /briefing?since_hours=N` | Draft a briefing |
| `POST /pipeline/daily?since_hours=N` | Ingest → classify → draft, in one call for the morning run |
| `GET /briefing/{id}` · `POST /briefing/{id}/review` | Read a briefing; record the analyst's decision |
| `GET /alerts/pending` · `POST /alerts/ack` | High-risk items not yet alerted; mark them alerted after the message is sent |

All endpoints except `/health` require header `X-API-Key`. Interactive docs at `http://127.0.0.1:8000/docs`.

## Themes and the high-risk definition

Themes: `tourism_strategy`, `destinations_gigaprojects`, `aviation_visa_entry`, `reputational_risk`,
plus `not_relevant` for noise (sport, weather, regional politics with no tourism angle).

**High risk** = sentiment `negative` **and** priority `high` **and** any sector theme. The theme
says which team should respond; the alert fires on tone and urgency. The rule lives in code
(`agent/classify.py::is_high_risk`), not inside the model, so the client can read and change it.

## Evaluation

30-item blind, stratified sample, hand-labelled against a written codebook (`eval/RESULTS.md`):
**83% theme agreement, 80% sentiment agreement.** Four of five theme disagreements are boundary
cases; one is a genuine miss caused by the deliberate "when in doubt, not_relevant" rule.

The briefing is checked in code after generation: every `[n]` citation must point to an item
that was actually supplied (hallucinated citations are flagged), and a draft cut short by the
length limit is flagged. Both warnings appear at the top of the draft the analyst sees.

## Cost at 1,500 items/day

| Step | Model | Monthly tokens | Monthly cost |
|---|---|---|---|
| Classification | Claude Haiku 4.5 ($1 / $5 per M) | ~17.9M in, ~2.7M out | ≈ $31.4 |
| Daily briefing | Claude Sonnet 5.5 ($2 / $10 per M) | ~0.4M in, ~0.1M out | ≈ $2 |
| Alerts | reuse classification | — | $0 |
| **LLM total** | | | **≈ $33.4 / month** |

Classification row measured with `eval/measure_tokens.py` (10-call average). Briefing row
estimated from one measured run (3,624 in / 2,766 out for 15 items) scaled to the 80-item cap.

Prompt caching on the fixed classification prompt (about 350 of the 397 input tokens are
identical every call) would cut the classification line to roughly $17: cached input reads
cost $0.10 per million instead of $1, while output cost is unchanged.
Plus a small VM for n8n inside the client's network. Re-measure with `python -m eval.measure_tokens`.

## Scope decisions

- **Cut:** Arabic sources, WhatsApp and Teams delivery. The brief allows narrowing; the core loop
  had to be reliable first. Arabic is the first thing to add (see architecture note).
- **Email only** for delivery. One channel done properly beats three half-wired.
- **Google News per-outlet feeds** for outlets that block or lack RSS. Every item keeps its
  original publisher and link. Trade-off: a dependency on Google; replace with direct feeds or a
  news API in production.
- **SQLite**, not Postgres. One file, zero setup, enough for half a million rows a year. Standard
  SQL, so moving to Postgres is a small change.
- **No agent framework.** Plain functions calling the LLM, orchestrated by n8n. Every step is
  readable and testable on its own.

## Known limitations

- De-duplication catches identical headlines, not rewritten ones; the same story from 16 outlets
  appeared as 16 items. Alerts are batched so this never becomes 16 emails. Next step: fuzzy or
  embedding-based story clustering.
- Google News links are redirect URLs; they resolve to the publisher but look opaque.
- The approval form link is local (`localhost`) in this prototype.
- Evaluation set is a 30-item smoke test by a single labeller, not a benchmark.

## Failure behaviour

- A failing feed never stops the run; it is listed in `failed_feeds` and surfaced as a warning
  on the draft.
- Classification commits after every item, so a crash mid-run loses nothing.
- Any API error returns clean JSON with a status code n8n treats as failure, so the workflow
  stops at the failing node instead of emailing an empty briefing.
- Alerts are acknowledged only after the message is sent, so a delivery failure re-sends them.
