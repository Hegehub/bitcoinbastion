# Bitcoin Bastion Storage Package

`app/storage/` is the first code-level scaffolding layer for the future Bitcoin Bastion multi-database Storage Layer.

## What this package is

- A stable boundary for storage engine names, responsibilities, descriptors, safety checks, profile expectations, and health aggregation.
- A lightweight set of interfaces that future prompts can implement for PostgreSQL, TimescaleDB, ClickHouse, Qdrant/pgvector, Redis, Object Storage, SQLite, and DuckDB.
- A safety contract that keeps source-of-truth rules explicit before storage engines are wired into product services.

## What this package is not

- It is not a database client layer yet.
- It does not connect to TimescaleDB, ClickHouse, Qdrant, MinIO/S3, SQLite, DuckDB, Redis, or PostgreSQL.
- It does not add migrations, change models, move repositories, or modify Trace, Market, News, Access, SDK, MCP, CLI, frontend, or worker business logic.
- It does not mean every storage engine is implemented or production-ready.

## Storage engines and responsibilities

| Engine | Responsibility |
| --- | --- |
| PostgreSQL | Transactional source of truth for critical relational state and artifact metadata. |
| TimescaleDB | Canonical time-series storage for metrics, candles, provider health, source health, and usage windows. |
| ClickHouse | Analytics warehouse and replay/projection target only. |
| Qdrant / pgvector | Semantic memory and similarity projection only. |
| Redis | Cache, queues, rate limits, websocket fanout, locks, and short-lived state only. |
| Object Storage | Proof packet and evidence archive artifact bytes; PostgreSQL owns metadata. |
| SQLite | Local/offline operational store until sync; not global truth. |
| DuckDB | Local analytics, exports, and offline reports; rebuildable and not operational truth. |

## Source-of-truth rules

- PostgreSQL is the transactional source of truth for critical state.
- TimescaleDB may be canonical only for time-series facts.
- ClickHouse must not be used for transactional access decisions.
- Qdrant and pgvector must not be canonical stores.
- Redis must never be durable truth.
- Object Storage may be canonical for artifact bytes only; PostgreSQL stores metadata, hashes, signatures, retention state, and authorization policy.
- SQLite may be local offline truth only until sync.
- DuckDB must not be operational truth.

## Security rules

This package and future implementations must not store seed phrases, Bitcoin private keys, wallet files, xprv/yprv/zprv material, mnemonics, raw secrets, raw Access Pass bearer tokens, or custody material.

If recovery or access material is ever represented, only hashes, fingerprints, encrypted local material, signed metadata, or non-custodial references are acceptable.

## How future prompts should extend this package

- Add concrete adapters in new modules without changing the stable interfaces unless necessary.
- Keep adapters behind explicit configuration and profile gates.
- Add health checks that report degraded state without hiding failures.
- Preserve rebuildable projection boundaries for ClickHouse, vector stores, Redis, DuckDB, and derived views.
- Add tests for every new source-of-truth or safety claim.
