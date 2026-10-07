# Classification evaluation

**Method:** 30-item blind, stratified sample (15 items the model called relevant, 15 it called
not_relevant), hand-labelled by a human using the codebook below. Compared against model output
(Claude Haiku, temperature 0). Priority is not scored: it is a judgement call even between two
analysts, and is reported qualitatively instead.

## Results

Labelled: 30
Theme accuracy: 83%
Sentiment accuracy: 80%
Theme mistakes:
High-profile Saudi music festival postponed: email to ticket | model=reputational_risk gold=destinations_gigaprojects
[sentiment] High-profile Saudi music festival postponed: email to ticket | model=negative gold=neutral
[sentiment] Saudi and French officials cement AlUla partnership during m | model=positive gold=neutral
New Flagship Space for SAMoCA Announced As Part of Saudi Vis | model=destinations_gigaprojects gold=tourism_strategy
[sentiment] Saudi Red Sea Authority Presents Red Sea Global with License | model=positive gold=neutral
Saudi Arabia plans to reopen to foreign tourists soon, touri | model=aviation_visa_entry gold=tourism_strategy
[sentiment] Saudi Arabia hotel market: Makkah and Madinah outperform as | model=neutral gold=negative
[sentiment] Developing tourism sector in Saudi Arabia: Ten new regulatio | model=positive gold=neutral
Saudi Tourism Authority Concludes Monaco Yacht Show 2026 wit | model=destinations_gigaprojects gold=tourism_strategy
Saudi OTA Almosafer on Track for Year-End IPO Despite Iran W | model=not_relevant gold=tourism_strategy
[sentiment] Saudi OTA Almosafer on Track for Year-End IPO Despite Iran W | model=neutral gold=positive


## Reading the results

- **Theme:** 4 of 5 disagreements are boundary cases (cultural venue or yacht show as
  destination vs strategy; border reopening as entry policy vs strategy; a postponed festival as
  risk vs destination). 1 clear miss: Almosafer IPO labelled not_relevant. That miss is the direct
  cost of the "when in doubt, not_relevant" rule: we chose precision (less noise in the briefing)
  over recall (catching every marginal item).
- **Sentiment:** 3 of 6 disagreements are factual announcements the model read as positive and
  the labeller as neutral (partnership signed, licences granted, regulations launched). 1 clear
  miss: a mixed hotel-market story (Riyadh RevPAR -23%) called neutral.
- **No further tuning after this run**, to avoid fitting the prompt to 30 items. Boundary
  definitions belong to the client's analysts in deployment; the engineer's job is the measuring
  tool, not the sector judgement.

## Earlier iteration (20-item smoke test)

First prompt produced one false high-risk alert (a Yemen conflict story with no tourism angle)
and missed a real one (NEOM Stadium shelved, filed under destinations). Fixes: tightened the
reputational_risk and not_relevant definitions, and made the high-risk rule depend on tone and
urgency (negative + high priority + any sector theme) rather than theme alone. Re-run on the same
20: false alert gone, NEOM flagged.

## Codebook used for labelling

| Story is mainly about | Theme |
|---|---|
| Visitor numbers, tourism spending, hotel market, tourism jobs, sector regulations, minister statements, tourism companies | tourism_strategy |
| A specific destination or project (AlUla, Red Sea, NEOM, Diriyah, cultural venues, marinas) | destinations_gigaprojects |
| Flights, airports, airspace, visas, passports, entry rules | aviation_visa_entry |
| Coverage that embarrasses or threatens the sector: cancellations, failing projects, incidents, negative press about visiting | reputational_risk |
| Weather, accidents, labour/residency enforcement, sport, regional conflict without a tourism angle, other countries | not_relevant |

Sentiment is judged towards the Saudi tourism sector, not the news itself: items not about the
sector are neutral even when the news is sad.

## Known limitations

- 30 items establishes the method and a baseline; a production evaluation set would be 200+ items
  labelled by two analysts, with inter-annotator agreement reported alongside model accuracy.
- One labeller for this version; six of the labeller's own first-pass labels changed after a codebook check,
  which shows the theme boundaries are ambiguous for humans too — hence draft-for-approval,
  never auto-publish.