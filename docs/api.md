# API endpoints (what n8n calls)

| Endpoint | Purpose |
|---|---|
| `GET /health` | Liveness check (no auth) |
| `POST /ingest` | Fetch feeds, de-duplicate, store |
| `POST /classify?limit=N` | Classify unclassified items |
| `POST /briefing?since_hours=N` | Draft a briefing |
| `POST /pipeline/daily?since_hours=N` | Ingest → classify → draft, in one call for the morning run |
| `GET /briefing/{id}` · `POST /briefing/{id}/review` | Read a briefing; record the analyst's decision |
| `GET /alerts/pending` · `POST /alerts/ack` | High-risk items not yet alerted; mark them alerted after the message is sent |

All endpoints except `/health` require header `X-API-Key`. Interactive docs at http://127.0.0.1:8000/docs.
