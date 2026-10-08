# Decisions log

1. Sources: 4 direct RSS feeds + per-outlet Google News RSS feeds for outlets that block
   or no longer publish RSS, + 3 topic feeds. Every item keeps its original outlet name
   and link, so citations point to the publisher, not to Google. Trade-off: Google News
   adds a dependency, but it is far more stable than scraping 8 different websites in
   3 days. Replace with direct feeds / a paid news API in production.

2. Dependencies are pinned in requirements.txt (pip freeze). The Anthropic SDK 1.x
   changed its interface mid-project; pinning means anyone installing it gets exactly the
   versions we tested, not whatever is newest on the day.

3. High-risk definition: sentiment=negative AND priority=high AND theme is a sector theme.
   First test (20 items) produced one false alert (regional conflict) and missed a real one
   (NEOM Stadium shelved). Fixed by tightening the reputational_risk definition and making
   the alert rule depend on tone + urgency rather than theme alone. "When in doubt, not_relevant."

4. Alerts are batched: the 10-minute check sends one message listing all new high-risk
   items, not one per article. Reason: a single story (NEOM scale-back) produced 16
   negative/high items across outlets. Story-level clustering is the next improvement.

5. SQLite over Postgres: one file, zero setup, standard SQL, enough for ~500k rows/year. Keeps
   the archive inside the client's environment and lets it run everything with pip alone.
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

12. Email only for delivery; Arabic sources and WhatsApp/Teams cut (archive Q&A was added later,
    see 17). The core loop had to be reliable first. Both are in the "What's next"
    list in docs/architecture.md.

13. n8n runs locally over plain HTTP for the prototype (Safari refuses its secure cookie on
    localhost). Production puts HTTPS in front of both n8n and the API.

14. 127.0.0.1 rather than localhost in n8n URLs. Node resolves localhost to IPv6 (::1); uvicorn
    listens on IPv4. Cost us 10 minutes once; documented so it never costs anyone else.

15. Evaluation by a blind, stratified 30-item hand-labelled sample with a written codebook, scored
    on theme and sentiment only (priority is judgement). No prompt tuning after scoring, to avoid
    fitting to 30 items. In deployment the client's analysts own the codebook and labels.

16. README verified by fresh clone on 7 Oct: pip install → first briefing in under 10 minutes.
    The test caught two real issues (placeholder key not obvious; 150 retries on a dead key),
    both fixed the same day.

17. Archive Q&A built as keyword retrieval + grounded answer, no vector store. Reason: it reuses the
    exact numbering/citation-check pattern of the briefing, adds ~60 lines, and cannot affect the
    core loop. Tested on three questions: every citation valid, and the model declined to count an
    item that did not name the subject. Embedding retrieval is the stated next step.

18. Hard daily cap on classification calls (DAILY_CLASSIFY_CAP, default 5,000 ≈ 3× expected
    volume), plus per-call output caps and per-step item caps already in place. A runaway feed or
    a loop bug costs at most one capped day. The API key's own spend limit is the second backstop.
    The cap protects against bugs, not costs (a capped day is about $3.50); it sits well above any
    plausible real news day, and reaching it is surfaced as a warning on the next draft so the
    pause is never silent.

19. Articles are untrusted input. Prompt-injection defence is structural, not prompt-based: fixed
    label validation on classification, citation verification on drafts, and mandatory human
    approval before delivery. A hostile page can waste one classification call; it cannot change
    what reaches the Director General.

20. Prompt caching was implemented and measured, then removed. The classification rulebook is
    ~350 tokens; Haiku's minimum cacheable prefix is 2,048, so cache_control was accepted but
    silently did nothing (0 cache reads over 10 calls). Shipping a no-op would have been
    misleading. Caching becomes worthwhile if the prompt grows (e.g. few-shot examples from
    the feedback loop), which is the point to re-test it.
