# Decisions log

1. Sources: 4 direct RSS feeds + per-outlet Google News RSS feeds for outlets that block
   or no longer publish RSS, + 3 topic feeds. Every item keeps its original outlet name
   and link, so citations point to the publisher, not to Google. Trade-off: Google News
   adds a dependency, but it is far more stable than scraping 8 different websites in
   3 days. Replace with direct feeds / a paid news API in production.

2. Dependencies are pinned in requirements.txt (pip freeze). The Anthropic SDK 1.x
   changed its interface mid-project; pinning means the panel installs exactly the
   versions we tested, not whatever is newest on the day.

3. High-risk definition: sentiment=negative AND priority=high AND theme is a sector theme.
   First test (20 items) produced one false alert (regional conflict) and missed a real one
   (NEOM Stadium shelved). Fixed by tightening the reputational_risk definition and making
   the alert rule depend on tone + urgency rather than theme alone. "When in doubt, not_relevant."

4. Alerts are batched: the 10-minute check sends one message listing all new high-risk
   items, not one per article. Reason: a single story (NEOM scale-back) produced 16
   negative/high items across outlets. Story-level clustering is the next improvement.

5. SQLite over Postgres: one file, zero setup, standard SQL, enough for ~500k rows/year. Keeps
   the archive inside the client's environment and lets the panel run everything with pip alone.
   Postgres is the production step when concurrent users and backups matter.

6. Two models, one vendor: Haiku 4.5 for classification (1,500 small decisions/day; cost and
   speed dominate), Sonnet 5.5 for the briefing (one document/day read by the DG; quality
   dominates). One API key, one SDK.

7. No agent framework (LangChain etc.). Plain Python functions call the LLM; n8n orchestrates.
   Every step is readable, testable alone, and defensible line by line.

8. "When in doubt, not_relevant." The classifier is tuned for precision over recall: the
   directorate would rather miss a marginal business story than read noise. Measured cost: one
   genuine miss in 30 (Almosafer IPO).

9. Citations are enforced in code, not trusted from the model. Every [n] in the draft must map
   to an item we supplied; unknown numbers are flagged in a banner at the top of the draft.
   Truncated drafts (stop_reason = max_tokens) are flagged the same way.

10. Responses are read by block type, not position. Newer models can return a thinking block
    before the text; indexing content[0] broke the briefing once. Fixed with a type filter.

11. Alerts use two endpoints (pending, then ack) instead of one. Acknowledgement happens only
    after the message is sent, so a delivery failure re-sends rather than silently losing alerts.

12. Email only for delivery; Arabic sources, WhatsApp/Teams and archive Q&A cut. The brief says to
    protect the core loop first. All three are in the "next two weeks" list in docs/architecture.md.

13. n8n runs locally over plain HTTP for the prototype (Safari refuses its secure cookie on
    localhost). Production puts HTTPS in front of both n8n and the API.

14. 127.0.0.1 rather than localhost in n8n URLs. Node resolves localhost to IPv6 (::1); uvicorn
    listens on IPv4. Cost us 10 minutes once; documented so it never costs anyone else.

15. Evaluation by a blind, stratified 30-item hand-labelled sample with a written codebook, scored
    on theme and sentiment only (priority is judgement). No prompt tuning after scoring, to avoid
    fitting to 30 items. In deployment the client's analysts own the codebook and labels.
