# BMTM Narrative Heatmap

The Bitcoin Narrative Heatmap is a Market Time Machine intelligence layer for identifying, tracking, scoring, and replaying dominant Bitcoin market narratives over time. It is not sentiment analysis, price prediction, or financial advice.

## Narrative taxonomy

`NarrativeType` covers ETF, Institutional Adoption, Treasury Adoption, Self Custody, Sovereignty, Bitcoin Core, Lightning, Mining, Hashrate, Macro, Fed, Inflation, Interest Rates, Liquidity, Regulation, SEC, CFTC, Banking, Exchange Liquidity, Exchange Failure, Security, Exchange Hack, Wallet Security, Privacy, Nation State Adoption, Corporate Adoption, Energy, Layer2, Stablecoins, Market Structure, Liquidation Cascade, Risk Off, and Risk On.

## Storage

- `market_narratives` stores narrative type, display name, description, active status, and compatibility slug/name fields.
- `narrative_observations` stores article/event-level narrative matches with observation score, confidence, source confidence, and observed time.
- `narrative_snapshots` stores replayable heatmap windows with heat, volume, impact, growth, confidence, evidence metadata, and trend state.

## Classification

`NarrativeClassifierService` uses deterministic keyword and pattern rules. Multiple narratives can match one article/event: an ETF article can match ETF and Institutional Adoption; a Fed liquidity article can match Macro, Fed, and Liquidity; a Lightning article can match Lightning and Layer2.

## Heat, growth, impact, dominance

`NarrativeHeatEngine` normalizes heat scores to `0-100` and maps them to Quiet, Emerging, Active, Dominant, or Major Narrative bands. Growth compares the current snapshot with prior heat. Impact uses impact confidence and market evidence rather than article count alone. The dominance index shows each narrative's share of total heatmap attention.

## History and replay

`NarrativeHistoryService` API contracts expose recent top narratives, growth leaders, declining narratives, impactful narratives, and placeholders for narratives before major BTC moves pending deeper candle-attribution backfill.

## Safety

Narrative outputs are evidence-based and correlation-based. They may show association with volatility or market context, but they must not claim causation, predict price, or provide trading advice.

## Task 34 production registry

Task 34 adds `config/narratives.yaml` as the operator-editable local narrative registry and `app/cli/seed_narratives.py` as the seed command. The classifier remains fully local: it uses keyword, title, category, and event-type text matching and never requires OpenAI or another external AI provider.

## Task 34 scoring fields

Narrative observations now preserve `narrative_id`, `observation_time`, `strength_score`, `relevance_score`, and confidence for replay. Snapshots expose `heat_score`, `velocity_score`, `dominance_score`, `confidence_score`, and `supporting_events_count` for heatmaps, trend charts, leaderboards, and narrative timelines.

## Task 34 API additions

`GET /api/v1/intelligence/narratives/emerging` returns rising/spiking narratives ordered by velocity. Narrative snapshot DTOs expose supporting articles, supporting events, source count, confidence, and limitations so web dashboards can render heatmaps without inferring hidden state.
