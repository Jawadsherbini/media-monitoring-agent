# LLM provider choice and alternatives

| Need | Anthropic (chosen) | OpenAI | Google Gemini | Gulf-hosted / sovereign |
|---|---|---|---|---|
| Bulk classification tier | Haiku 4.5, $1 / $5 per M tokens | mini/nano tiers, similar band | Flash tiers, $0.75–1.50 / $3.75–9 | Varies; often open-weight models on local GPUs |
| Writing tier | Sonnet 5.5, $2 / $10 | GPT-5-class, ~$1.25–2 / $10–12 | Gemini 3.x Pro, $2 / $12 | Quality gap on long structured English drafting |
| Monthly cost at 1,500 items/day | ≈ $33 (measured) | ≈ $25–45 (est.) | ≈ $20–40 (est.) | Hardware/licence cost, not per-token |
| Data residency today | Public API; also via AWS Bedrock / Google Vertex regional endpoints | Public API; Azure regional endpoints | Public API; Vertex regional endpoints | Strongest residency story |
| Why not chosen for the prototype | — | Comparable; no decisive advantage for this task | Comparable; cheapest at the floor | No time in 3 days to stand up and evaluate; quality unproven on this task |

Prices are per million tokens, from the vendors' published price lists in the first week of
October 2026; they change monthly and must be re-checked before any quote to a client.

The decision was not price: all three major vendors land within a few dollars a month at this
volume. It was made on (1) how reliably the model obeys "use only the supplied items and cite
each claim" — demonstrated in every test run, including declining to connect two stories without
evidence; (2) two quality tiers behind one SDK and one key, so bulk and quality work cost what
they should; (3) prompt caching for the fixed classification prompt; (4) a credible path to
regional hosting through the hyperscalers if the client requires it.

**Swapping providers.** `agent/llm.py` is the only file that creates an LLM client; classification
and drafting import it from there. A provider abstraction (one function per provider behind the
same `client` interface, chosen by an `LLM_PROVIDER` setting in `.env`) is a next-step item,
deliberately not built in the prototype to keep the delivered loop simple and tested. The
evaluation set makes a provider switch measurable: re-run `eval/score.py` and compare.
