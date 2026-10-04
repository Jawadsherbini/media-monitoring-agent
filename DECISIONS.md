# Decisions log

1. Sources: 4 direct RSS feeds + per-outlet Google News RSS feeds for outlets that block
   or no longer publish RSS, + 3 topic feeds. Every item keeps its original outlet name
   and link, so citations point to the publisher, not to Google. Trade-off: Google News
   adds a dependency, but it is far more stable than scraping 8 different websites in
   3 days. Replace with direct feeds / a paid news API in production.

2. Dependencies are pinned in requirements.txt (pip freeze). The Anthropic SDK 1.x
   changed its interface mid-project; pinning means the panel installs exactly the
   versions we tested, not whatever is newest on the day.