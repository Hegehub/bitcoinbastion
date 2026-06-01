# Architecture

## System style
Bitcoin Bastion is implemented as a **modular monolith** with explicit boundaries that keep business logic out of transport layers.

Primary boundaries:
- `app/api`: FastAPI route handlers, dependencies, middleware, error envelopes.
- `app/services`: orchestration and domain logic (scoring, policy, explainability, wallet/treasury, delivery).
- `app/db/models`: relational domain models.
- `app/db/repositories`: persistence access patterns and pagination/query helpers.
- `app/integrations`: external provider adapters (RSS, Bitcoin provider abstractions).
- `app/tasks`: Celery entrypoints for scheduled and async workflows.
- `app/schemas`: request/response and envelope contracts.

## Runtime topology
Core runtime components:
1. **API process** (FastAPI / Uvicorn)
2. **Celery worker** (task execution)
3. **Celery beat** (scheduled jobs)
4. **PostgreSQL** (durable state)
5. **Redis** (Celery broker/result + cache-ready layer)

## Request lifecycle
1. Request enters API with request ID middleware and rate limiting middleware.
2. Route validates input schema and delegates to service layer.
3. Service orchestrates repositories/integrations.
4. Results are wrapped in standardized response envelopes.
5. Metrics and error handlers provide observability and stable failure contracts.

## Current intelligence pipeline shape
- **Ingestion**: RSS ingestion service + on-chain ingestion service.
- **Scoring**: News scoring and fee/wallet/privacy scoring services.
- **Signals**: Signal engine + explainability service with evidence graph persistence.
- **Delivery**: Telegram formatter/delivery service + delivery logs.
- **Governance**: Policy runtime checks and execution logs.

## Design constraints
- Thin routes and thin Telegram handlers.
- Explainability-first for scores and recommendations.
- Retry-safe and idempotency-aware background tasks.
- Security baseline through JWT auth, RBAC-oriented dependencies, and audit logs.

## Schema governance notes
- Alembic is the source of schema evolution truth; `create_all()` is not a deployment path.
- Current schema truth audit confirms complete table coverage for all SQLAlchemy model tables (27/27 mapped through migrations).
- SQLite-specific migration behavior (batch mode, default/constraint representation) can produce autogenerate drift signals that require explicit review before accepting migration deltas.
- Runtime drift checks now validate tables, columns, nullability, type affinity, indexes, unique constraints, foreign keys, and explicit server defaults via `python scripts/check_schema_runtime_parity.py`.
- Advanced drift checks intentionally degrade gracefully when a dialect does not expose a reflection surface (e.g., unsupported index/constraint APIs) to avoid false positives in CI.

## Deduplication & Clustering Engine
Deterministic, replayable dedup and conservative clustering feed canonical NewsEvent attribution.

- Market-data foundation now includes provider health snapshot API and canonical BTC price history retrieval.

- News scoring foundation now includes deterministic rule-based scoring service with config-driven weights in `config/news_scoring.yaml`.

## Historical similarity subsystem

The historical similarity subsystem lives under `app/services/intelligence`. It materializes `HistoricalEventProfile` rows from NewsEvents, NewsPriceImpacts, and CandleAttributions, then computes explainable component scores for narrative similarity, sentiment similarity, impact similarity, price-behavior similarity, confidence similarity, and dominant-window similarity.

Similarity results are persisted for auditability and can be embedded into evidence packets as `similar_historical_events` plus `historical_similarity_summary`. The subsystem is deterministic, rule-based, and intentionally avoids prediction language.

## Production Historical Similarity Engine

The production Historical Similarity Engine adds `market_pattern_library` and `historical_similarity_records` alongside the historical profile/result tables. Pattern classification is handled by `PatternClassificationService`, while `HistoricalSimilarityService` builds reports with top analogs, median/average reaction statistics, confidence reasoning, and replayable evidence. The API layer exposes event, article, and pattern-library endpoints without introducing prediction or trading-advice semantics.

## BMTM Narrative Heatmap

The Market Time Machine Intelligence Layer includes a Narrative Heatmap subsystem. It persists narrative taxonomy, narrative observations, and narrative snapshots; classifies NewsArticles and NewsEvents into multiple deterministic `NarrativeType` values; computes heat, volume, impact, growth, confidence, dominance, and trend state; and emits narrative timeline entries for rising/spiking narratives. It integrates with news, scoring, timeline, historical similarity, and future dashboard widgets while preserving correlation-only language.

### Narrative registry and UI contracts

The Narrative Heatmap subsystem now reads the operator-editable `config/narratives.yaml` registry, persists observation-level strength/relevance/confidence, and stores snapshot-level heat, velocity, dominance, and supporting-event counts. The API returns frontend-ready DTOs for heatmaps, trend charts, leaderboards, and narrative timelines without claiming causation.
