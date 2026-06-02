# Market Memory

Market Memory is the persistence and retrieval layer for historical Bitcoin market context. It supports Market Time Machine, reverse explanation, narrative workflows, and operator review screens.

## Architecture

The production package is `app/services/intelligence/market_memory/`:

- `EventFingerprintBuilder` creates replayable fingerprints from event evidence and BTC reaction windows.
- `PatternMatcher` exposes an explicit pattern library and returns confidence plus reason codes; there are no hidden classifications.
- `HistoricalSimilarityEngine` ranks similar historical events and persists reusable `market_memory_records`.
- `PatternStatisticsService` computes per-pattern occurrence counts, median 15m/1h/4h/24h moves, positive/negative/neutral rates, best/worst observed 4h moves, and average confidence.
- `MarketMemoryEvidenceBuilder` packages source events, similarity calculations, pattern matches, reaction summaries, limitations, provider confidence, and generation time.
- `OperatorReviewService` records auditable approvals, rejections, confidence overrides, notes, and false-similarity markers.

## EventFingerprint Design

`EventFingerprint` fields are: `event_id`, `btc_relevance_score`, `market_impact_score`, `sentiment_score`, `institutional_score`, `macro_score`, `regulatory_score`, `security_score`, `source_count`, `price_change_15m`, `price_change_1h`, `price_change_4h`, `price_change_24h`, `direction`, `volatility_profile`, and `confidence_score`.

## Pattern Library

Supported explicit patterns include ETF inflow shock, ETF outflow shock, Fed liquidity shock, SEC enforcement, regulatory approval, exchange hack, security incident, miner capitulation, institutional adoption, treasury adoption, Lightning adoption, Bitcoin Core release, macro risk-on, macro risk-off, and large liquidation cascade.

## Replay Behavior

Replay returns the event analyzed, candidate events, similarity scores, pattern assignment, reason codes, and final ranking. Replay is intended for operator audit and UI evidence drawers.

## Operator Workflow

Operators may approve or reject pattern assignments, override confidence, attach notes, and mark false similarities. Overrides are stored in `market_memory_operator_reviews` with audit metadata.

## Limitations and Safety

Market Memory is informational and Bitcoin-first. It does not predict price and does not make trading recommendations. Required response limitations are: Historical similarity is not prediction. Correlation is not proof of causation. Past market reactions do not guarantee future outcomes. Do not generate trading recommendations.
