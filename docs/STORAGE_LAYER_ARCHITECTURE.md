# Bitcoin Bastion Storage Layer Architecture

## 1. Purpose

Bitcoin Bastion's current architecture is a modular monolith with PostgreSQL for durable state and Redis for broker/cache-ready runtime support. This document defines the future multi-database storage contract for the platform without claiming that the target layer is already implemented.

Bitcoin Bastion needs multiple storage engines because it has multiple classes of data with different durability, latency, query, privacy, and recovery requirements:

- transactional access data for access certificates, subscriptions, devices, sessions, revocations, audit events, webhook configuration, and operator decisions;
- time-series market data for BTC price points, candles, mempool snapshots, provider health, source health, access integrity history, and operational metrics;
- long-range analytics for Market Time Machine replay, historical similarity, usage trends, delivery history, and large retrospective analysis;
- semantic memory for narrative search, evidence similarity, trace context retrieval, and historical event discovery;
- proof and evidence files for signed proof packets, evidence archives, deployment evidence, restore evidence, and export artifacts;
- temporary runtime state for rate limits, queues, websocket fanout, cache entries, locks, idempotency windows, and short-lived coordination;
- local/offline operation for Bastion Desktop AI, PayRegister workflows, offline nodes, local project capsules, local sync logs, exports, and offline reports.

The central rule is:

```text
No single database should own the whole system.
Each storage engine must have a bounded responsibility,
a clear source-of-truth rule,
a recovery strategy,
a privacy boundary,
and an audit path.
```

## 2. Design Principles

1. **PostgreSQL remains the source of truth for critical state.** Access decisions, entitlement state, revocation records, webhook endpoint configuration, metadata for evidence artifacts, and audit-critical relational facts must be rooted in PostgreSQL unless a later architecture decision explicitly changes ownership.
2. **Redis is never a source of truth.** Redis may cache, queue, fan out, rate-limit, lock, and coordinate short-lived state, but losing Redis must not lose canonical business facts.
3. **ClickHouse is never a transactional source of truth.** ClickHouse is an analytics warehouse and replay store for projected data. It must not authorize access, own billing state, or decide entitlement truth.
4. **Qdrant is never a canonical source of truth.** Vector stores hold semantic projections, embeddings, chunk references, and similarity indexes. Canonical documents and authorization metadata must live elsewhere.
5. **Object Storage stores large artifacts; PostgreSQL stores their metadata.** Proof packets, evidence archives, signed bundles, and exports belong in Object Storage, while ownership, hashes, signatures, retention policy, lifecycle state, and access metadata belong in PostgreSQL.
6. **Local SQLite and DuckDB are local-first/offline engines, not global truth.** SQLite can be local truth while disconnected, but important business data must sync to canonical stores with audit. DuckDB is for local analytics, exports, and offline reporting.
7. **All projections must be rebuildable.** Timescale continuous aggregates, ClickHouse tables, Qdrant collections, Redis caches, DuckDB exports, and local derived views must have a documented rebuild path from canonical records, outbox events, or immutable artifacts.
8. **Every cross-storage write must go through an outbox or explicit projection pipeline.** Route handlers must not casually write to PostgreSQL, Redis, ClickHouse, Object Storage, and Qdrant in one ad hoc transaction.
9. **No seed phrases, private keys, wallet files, xprv/yprv/zprv, or custody material may be stored.** This applies to every database, cache, log, object, embedding, analytics table, local file, export, and test fixture.
10. **No global `user_id` by default for privacy-sensitive access architecture.** Payment, access, usage, Telegram binding, audit, workspace, device, and product domains should use context-local identifiers unless a deliberate join boundary is approved.
11. **Degraded state must be visible.** Fallback, replay lag, projection failure, stale cache, missing embedding, and object retrieval failure must be reported explicitly.
12. **Audit paths must survive projection failure.** If an analytics, cache, or vector projection fails, the canonical transaction and projection error must remain inspectable.

## 3. Storage Engines Overview

### PostgreSQL

- **Role:** Transactional source of truth for critical relational state.
- **Stores:** Access certificates, subscription entitlements, revocations, devices, sessions, audit records, webhook endpoints, object metadata, proof packet metadata, sync acknowledgements, billing/access truth, outbox rows, and governance decisions.
- **Must not store:** Large proof packet blobs, raw seed phrases, Bitcoin private keys, wallet files, xprv/yprv/zprv material, raw webhook secrets, unbounded time-series history that belongs in TimescaleDB, or large analytics projections that belong in ClickHouse.
- **Failure behavior:** Critical operations are not ready. Read-only public status may respond with explicit database-degraded state if safe.
- **Backup/rebuild approach:** Point-in-time recovery (PITR), WAL archive, migration smoke tests, schema parity validation, staging restore drills, and evidence records for restore operations.

### TimescaleDB

- **Role:** Time-series store for metrics, market data, candles, provider health, source health, and operational history.
- **Stores:** BTC price points, BTC candles, mempool fee snapshots, provider health snapshots, source health snapshots, API usage rollups, access integrity history, and operational metrics that require time-window queries.
- **Must not store:** Access certificate truth, subscription entitlement truth, revocation truth, proof packet blobs, private keys, seed phrases, or canonical long-form documents.
- **Failure behavior:** Metrics, candles, and health history degrade; operational access and entitlement decisions continue from PostgreSQL.
- **Backup/rebuild approach:** PostgreSQL-compatible backups, retention policy, compression policy, aggregate refresh validation, and rebuild from provider ingestion logs or outbox where available.

### ClickHouse

- **Role:** Analytics warehouse for Market Time Machine, replay, high-volume delivery history, large event scans, and retrospective analysis.
- **Stores:** Market Time Machine events, historical similarity run facts, long-range provider/source health analytics, webhook delivery analytics, API usage analytics, replayable market/news timelines, and query-optimized event copies.
- **Must not store:** Transactional access truth, revocation truth, billing truth, raw secrets, private keys, seed phrases, wallet files, or data that cannot be rebuilt or traced to canonical ownership.
- **Failure behavior:** Historical analytics, replay, large reports, and time-machine views degrade; transactional APIs continue through PostgreSQL and TimescaleDB.
- **Backup/rebuild approach:** Snapshots, partition export, schema version tracking, and rebuild from canonical stores, object artifacts, and outbox events where possible.

### Qdrant / pgvector

- **Role:** Semantic memory and similarity search. pgvector may be used first inside PostgreSQL for early-stage semantic indexes; Qdrant may become the dedicated vector store when scale or isolation requires it.
- **Stores:** Semantic document chunks, narrative embeddings, evidence embeddings, historical similarity vectors, model version metadata, references to canonical documents, and similarity indexes.
- **Must not store:** Canonical documents without a source record, access truth, billing truth, revocation truth, raw secrets, seed phrases, private keys, wallet files, xprv/yprv/zprv material, or sensitive material embedded into vectors.
- **Failure behavior:** Semantic search and similarity features degrade; canonical document retrieval and transactional flows continue.
- **Backup/rebuild approach:** Snapshots, embedding model versioning, chunk manifest retention, and rebuild from canonical documents and signed artifacts.

### Redis

- **Role:** Cache, queue/broker, rate limit state, websocket fanout, short-lived locks, idempotency windows, and short-lived runtime coordination.
- **Stores:** Cache entries, Celery/broker-compatible state, rate counters, websocket pub/sub messages, short-lived tokens where appropriate, distributed locks, and ephemeral projection hints.
- **Must not store:** Durable access truth, billing truth, revocation truth, proof packet truth, private keys, seed phrases, wallet files, raw secrets, or the only copy of any business fact.
- **Failure behavior:** System enters slower or limited mode. Queues, fanout, rate-limits, and cache-dependent paths degrade, but canonical truth remains in durable stores.
- **Backup/rebuild approach:** Redis is not durable truth. Critical data must exist elsewhere. Cache warming and queue reconciliation must tolerate loss.

### Object Storage / MinIO / S3

- **Role:** Artifact store for large immutable or versioned files.
- **Stores:** Proof packet files, evidence archives, signed artifacts, deployment evidence packs, export bundles, restore drill attachments, raw payload archives when appropriate, checksums, detached signatures, and WORM evidence objects.
- **Must not store:** Seed phrases, private keys, wallet files, xprv/yprv/zprv material, raw browser secrets, or unencrypted sensitive payloads.
- **Failure behavior:** Proof packet download, evidence export, archive retrieval, and signed bundle creation are unavailable; PostgreSQL metadata and audit records remain available.
- **Backup/rebuild approach:** Versioning, checksums, signatures, replication, WORM mode for critical evidence, retention policies, lifecycle rules, and metadata reconciliation against PostgreSQL.

### SQLite

- **Role:** Local operational database for Desktop AI, PayRegister, offline nodes, disconnected work queues, local sync logs, and offline-first business workflows.
- **Stores:** Local PayRegister shifts and sales while offline, Desktop AI project capsules, local device state, local pending sync operations, offline evidence references, and encrypted local configuration.
- **Must not store:** Seed phrases, Bitcoin private keys, wallet files, xprv/yprv/zprv material, raw custody data, or the only long-term copy of important business data without sync/audit.
- **Failure behavior:** Local node or desktop operation may pause, require recovery/import, or enter read-only mode. Global canonical services continue.
- **Backup/rebuild approach:** Encrypted local backups, signed sync logs, export/import tools, device recovery policy, checksum validation, and canonical reconciliation with PostgreSQL after reconnect.

### DuckDB

- **Role:** Local analytics engine for exports, offline reports, Desktop AI analysis, PayRegister reporting, and self-contained analytical datasets.
- **Stores:** Local analytical extracts, report-ready Parquet/CSV imports, offline aggregate views, temporary analysis tables, and generated report datasets.
- **Must not store:** Transactional truth, access truth, raw secrets, seed phrases, private keys, wallet files, or the only authoritative copy of business data.
- **Failure behavior:** Offline analytical reports and local export analysis are unavailable; operational workflows continue through SQLite or canonical services.
- **Backup/rebuild approach:** Rebuild from exports, canonical datasets, signed sync logs, object archives, and repeatable report manifests.

## 4. Source-of-Truth Rules

Canonical ownership must be explicit before implementation. Examples:

### Access Certificate

- **Truth:** PostgreSQL.
- **Cache:** Redis.
- **Analytics projection:** ClickHouse.
- **Export/archive:** Object Storage.
- **Rule:** Redis and ClickHouse may accelerate or analyze access certificate facts, but access authorization must validate against PostgreSQL or a signed, revocation-aware protocol derived from PostgreSQL truth.

### BTC Candle

- **Truth:** TimescaleDB.
- **Analytics projection:** ClickHouse.
- **API cache:** Redis.
- **Rule:** ClickHouse may replay and aggregate candles, but canonical market candle definitions and provider attribution are time-series facts owned by TimescaleDB.

### Proof Packet

- **Metadata truth:** PostgreSQL.
- **File truth:** Object Storage.
- **Search projection:** Qdrant / pgvector.
- **Analytics event copy:** ClickHouse.
- **Rule:** A proof packet is valid only when PostgreSQL metadata, object checksum/signature, and retention state agree. Vector and analytics copies are projections.

### Metric Usage

- **Operational usage:** TimescaleDB.
- **Billing/access truth where needed:** PostgreSQL.
- **Long-range analytics:** ClickHouse.
- **Rule:** Usage analytics can be large-scale and approximate where labeled, but billing/access-affecting facts must reconcile into PostgreSQL.

### Local PayRegister Sale

- **Local truth while offline:** SQLite.
- **Canonical sync target:** PostgreSQL.
- **Analytics projection:** ClickHouse.
- **Rule:** Offline SQLite sales must carry signed local sync logs and deterministic conflict rules. Once synced, PostgreSQL owns canonical business state.

## 5. Data Ownership Matrix

| Data Type | Primary Store | Secondary Store / Projection | Reason | Rebuild Strategy |
| --- | --- | --- | --- | --- |
| `access_payment_intents` | PostgreSQL | ClickHouse analytics, Redis idempotency cache | Payment/access state requires transactional audit and reconciliation. | PITR restore; replay payment provider webhooks and outbox events. |
| `access_certificates` | PostgreSQL | Redis cache, ClickHouse analytics, Object Storage export | Critical access proof needs relational truth and audit. | PITR restore; regenerate caches and analytics from PostgreSQL/outbox. |
| `subscription_entitlements` | PostgreSQL | Redis cache, ClickHouse analytics | Entitlement decisions are transactional and revocation-sensitive. | PITR restore; replay entitlement outbox events. |
| `access_devices` | PostgreSQL | Redis session/device cache | Device binding affects access decisions. | PITR restore; rebuild cache from PostgreSQL. |
| `access_sessions` | PostgreSQL for durable session/audit metadata | Redis short-lived session state | Sessions need revocation audit while hot state needs low latency. | Restore PostgreSQL; expire/recreate Redis state. |
| `access_revocations` | PostgreSQL | Redis revocation cache, ClickHouse analytics | Revocation is security-critical canonical state. | PITR restore; warm Redis from PostgreSQL; replay analytics. |
| `access_audit_events` | PostgreSQL | ClickHouse analytics, Object Storage evidence export | Audit chain must be durable and queryable. | PITR restore; export/replay to ClickHouse and artifacts. |
| `btc_price_points` | TimescaleDB | Redis latest-price cache, ClickHouse analytics | Time-series ingestion and window queries. | Reingest provider history where possible; replay ingestion events. |
| `btc_candles` | TimescaleDB | Redis cache, ClickHouse Market Time Machine | Canonical candle series and attribution need time-series semantics. | Recompute from price points/provider records; rebuild projections. |
| `mempool_fee_snapshots` | TimescaleDB | ClickHouse analytics, Redis latest snapshot | Time-windowed fee history. | Reingest from retained provider logs/outbox where available. |
| `provider_health_snapshots` | TimescaleDB | ClickHouse analytics, Redis latest health | Operational provider health is time-series state. | Rebuild from provider polling logs/outbox. |
| `source_health_snapshots` | TimescaleDB | ClickHouse analytics, Redis latest health | News source quality changes over time. | Rebuild from source registry checks and outbox. |
| `news_articles` | PostgreSQL | ClickHouse analytics, Qdrant/pgvector semantic projection | Article metadata and dedup truth are relational; analysis/search are projections. | PITR restore; rebuild vectors and analytics from PostgreSQL. |
| `news_raw_payloads` | Object Storage | PostgreSQL metadata, ClickHouse ingestion analytics | Raw payloads can be large and immutable. | Reconcile object manifests with PostgreSQL; restore object versions. |
| `news_price_impact_history` | TimescaleDB | ClickHouse analytics | Impact windows are time-series derived facts. | Recompute from news events, candles, and attribution rules. |
| `market_time_machine_events` | ClickHouse | Object Storage replay exports, PostgreSQL job metadata | Large replay workloads require analytics warehouse semantics. | Rebuild from TimescaleDB, PostgreSQL, object archives, and outbox. |
| `historical_similarity_runs` | ClickHouse | PostgreSQL run metadata, Qdrant/pgvector vectors | Large retrospective runs are analytical and replayable. | Recompute from canonical events, embeddings, and model versions. |
| `trace_reports` | PostgreSQL | Object Storage exports, Qdrant search, ClickHouse analytics | Trace report metadata and operator-visible state need relational audit. | PITR restore; rebuild exports/search/analytics from reports and evidence. |
| `trace_runtime_events` | TimescaleDB | ClickHouse analytics, Redis live status | Runtime event streams are time-series operational facts. | Replay event outbox and retained runtime logs. |
| `proof_packets` | PostgreSQL metadata + Object Storage files | Qdrant search, ClickHouse analytics | Metadata and artifacts have split canonical ownership. | Restore PostgreSQL and object versions; rebuild vectors/analytics. |
| `evidence_archives` | Object Storage | PostgreSQL metadata, ClickHouse archive index | Archives are large signed artifacts with metadata/audit. | Object version restore; checksum/signature validation; metadata reconciliation. |
| `webhook_endpoints` | PostgreSQL | Redis dispatch cache | Endpoint configuration is operator-controlled truth. | PITR restore; rebuild dispatch cache. |
| `webhook_delivery_events` | PostgreSQL for delivery attempts; ClickHouse for high-volume analytics | Redis retry coordination | Delivery attempts need audit; long-range analysis needs warehouse. | PITR restore for audited attempts; replay outbox to ClickHouse. |
| `api_usage_events` | TimescaleDB | ClickHouse long-range analytics, PostgreSQL billing/access rollups where needed | High-volume usage is time-series; access-affecting rollups need relational truth. | Replay logs/outbox; reconcile billing rollups into PostgreSQL. |
| `semantic_documents` | PostgreSQL metadata/document registry | Qdrant/pgvector embeddings, Object Storage source artifacts | Canonical document registry must remain auditable. | Rebuild embeddings from canonical documents and model version manifests. |
| `narrative_embeddings` | Qdrant/pgvector | PostgreSQL model/version metadata | Embeddings are semantic projections, not canonical content. | Re-embed canonical narratives/articles with recorded model versions. |
| `PayRegister offline shifts` | SQLite while offline; PostgreSQL after sync | ClickHouse analytics, Object Storage shift exports | Offline operation needs local truth with canonical sync. | Signed sync log replay; conflict resolution; analytics rebuild from PostgreSQL. |
| `Desktop AI local project capsules` | SQLite local store + Object Storage optional encrypted export | DuckDB local analytics, Qdrant/pgvector local semantic index | Local-first workspace data should not become global truth by default. | Encrypted local backup restore; signed export/import; rebuild local indexes. |

## 6. Storage Mapping by Product Area

### Access Layer / Proof-of-Access Auth PQ

- **PostgreSQL:** access payment intents, certificates, entitlements, devices, sessions, revocations, audit events, recovery quorum metadata, object metadata for access exports.
- **Redis:** hot certificate/session caches, rate limits, nonce windows, websocket access fanout, short-lived idempotency.
- **ClickHouse:** access analytics, revocation trends, delivery/usage history, fraud/integrity dashboards.
- **Object Storage:** signed access certificate exports, audit bundles, recovery evidence.
- **TimescaleDB:** access integrity history, usage time series, provider availability history for access services.

### Market Time Machine

- **TimescaleDB:** BTC price points, candles, mempool fee snapshots, provider health snapshots, source health snapshots, candle attribution time windows.
- **ClickHouse:** replay timelines, large historical scans, market-time-machine events, historical similarity run facts, long-range analytics.
- **PostgreSQL:** job metadata, operator review state, signal metadata, evidence links, source registry facts.
- **Redis:** latest price/candle cache, dashboard cache, websocket fanout.
- **Object Storage:** replay exports, evidence bundles, raw market provider payload archives when retained.
- **Qdrant/pgvector:** similarity over market narratives and historical event descriptions.

### News Intelligence

- **PostgreSQL:** news articles, events, dedup/clustering metadata, source registry, reputation records, operator annotations.
- **Object Storage:** raw payload archives, signed exports, evidence attachments.
- **TimescaleDB:** source health snapshots, impact windows, source/provider health time series.
- **ClickHouse:** news impact analytics, long-range narrative timelines, replay datasets.
- **Qdrant/pgvector:** semantic article search, narrative embeddings, similarity retrieval.
- **Redis:** ingestion locks, latest dashboard cache, short-lived fetch coordination.

### Bastion Trace

- **PostgreSQL:** trace reports, trace evidence metadata, trace sources, watchlist configuration, access/audit decisions.
- **TimescaleDB:** trace runtime events, source availability history, batch execution metrics.
- **ClickHouse:** large trace analytics, runtime event exploration, public-safe aggregate trends.
- **Object Storage:** trace report exports, proof attachments, evidence archives.
- **Qdrant/pgvector:** advisory semantic search over trace explanations and evidence references.
- **Redis:** live status, progress fanout, short-lived trace queues/locks.

### Evidence / Proof Packets

- **PostgreSQL:** proof packet metadata, lineage, signatures, checksums, access policy, retention metadata, review state.
- **Object Storage:** proof packet files, evidence archives, signed artifacts, deployment evidence packs.
- **ClickHouse:** evidence access analytics, packet creation trends, replay event copies.
- **Qdrant/pgvector:** evidence similarity and semantic retrieval.
- **Redis:** temporary download authorization cache and websocket notifications.

### SDK / MCP / CLI / Developer Layer

- **PostgreSQL:** API keys or key hashes, webhook endpoints, developer workspace metadata, audit logs, endpoint configuration.
- **TimescaleDB:** API usage events and rate-window usage history.
- **ClickHouse:** long-range developer analytics, webhook delivery analytics, SDK adoption reports.
- **Redis:** rate limits, idempotency windows, websocket fanout, short-lived token state.
- **Object Storage:** exported evidence, generated reports, developer audit bundles.

### PayRegister

- **SQLite:** local offline shifts, sales, device-local queue, signed sync log, local operator context.
- **PostgreSQL:** canonical synced sales, access/subscription state, device binding, audit records.
- **Redis:** online sync locks, short-lived conflict resolution coordination.
- **ClickHouse:** sales analytics and historical reports after sync.
- **DuckDB:** local reports, shift summaries, export analysis.
- **Object Storage:** signed shift exports, receipts/evidence where allowed.

### Bastion Desktop AI / Bastion OS

- **SQLite:** local project capsules, local configuration, local sync queue, local workspaces, local history.
- **DuckDB:** local analytics, reports, imported datasets, offline investigations.
- **Qdrant/pgvector:** local or server-side semantic indexes depending on deployment profile.
- **Object Storage:** optional encrypted backups, signed exports, evidence bundles.
- **PostgreSQL:** canonical server-side sync target only for data explicitly synced by policy.
- **Redis:** optional online coordination when connected.

### Observability / Deployment Governance

- **PostgreSQL:** deployment metadata, operations evidence metadata, restore drill metadata, operator approvals, audit records.
- **TimescaleDB:** metrics, provider/service health snapshots, integrity history.
- **ClickHouse:** long-range observability analytics, incident timelines, deployment trend analysis.
- **Object Storage:** deployment evidence packs, logs selected for evidence, restore drill artifacts, signed reports.
- **Redis:** health cache, worker coordination, short-lived locks.

## 7. Write Path

Preferred write pattern:

```text
API / Worker
→ Domain Service
→ PostgreSQL or TimescaleDB canonical write
→ Outbox event
→ Projection workers
→ ClickHouse / Qdrant / Object Storage / Redis
```

Rules:

1. Route handlers validate transport input and delegate to domain services. They must not coordinate casual multi-database writes.
2. Domain services decide the canonical owner before writing.
3. The canonical write and outbox event should be committed atomically where they share the same transactional database.
4. Projection workers read outbox events or explicit projection streams and update Redis, ClickHouse, Qdrant, Object Storage, DuckDB exports, or derived Timescale aggregates.
5. Projection workers must be idempotent, retry-safe, observable, and able to record partial failure.
6. If an artifact must be written to Object Storage as part of a workflow, PostgreSQL must store the metadata, checksum, object key, signature reference, and lifecycle status. Workflows must handle orphan cleanup or reconciliation.
7. Cross-storage writes must not hide failures. If a projection fails, the system must expose lag/degraded status and allow replay.

## 8. Read Path

Read routing should follow the data ownership model:

- **Operational API → PostgreSQL.** Access decisions, certificate metadata, subscriptions, revocations, webhook endpoints, proof packet metadata, trace report state, and operator workflows read from PostgreSQL.
- **Metrics API → TimescaleDB.** Candles, price points, mempool snapshots, provider health history, source health history, access integrity timelines, and operational metrics read from TimescaleDB.
- **Historical analytics → ClickHouse.** Market Time Machine replay, long-range analytics, historical similarity runs, large usage reports, and delivery history scans read from ClickHouse.
- **Semantic search → Qdrant / pgvector.** Narrative search, evidence similarity, historical analogy retrieval, and semantic document discovery read from vector indexes with authorization checked against canonical metadata.
- **Proof packet download → PostgreSQL metadata + Object Storage file.** Download authorization, metadata, checksum, and retention policy come from PostgreSQL; the bytes come from Object Storage.
- **Hot cache / websocket → Redis.** Redis serves low-latency caches, pub/sub, fanout, rate-limit decisions, and short-lived coordination only.
- **Local/offline → SQLite / DuckDB.** Desktop AI, PayRegister, and offline nodes use SQLite for local operational state and DuckDB for local analytics/exports.

A read path may combine stores only when the authorization boundary is clear. For example, vector search may retrieve candidate IDs from Qdrant, but PostgreSQL must enforce access policy before returning private documents.

## 9. Outbox and Projection Model

The future storage projection foundation should include a table named:

```text
storage_outbox_events
```

Proposed fields:

| Field | Purpose |
| --- | --- |
| `id` | Stable event identifier or primary key. |
| `event_type` | Projection event type, such as `proof_packet.created` or `btc_candle.closed`. |
| `aggregate_type` | Domain aggregate type. |
| `aggregate_id` | Domain aggregate identifier. |
| `payload_json` | Sanitized projection payload or reference payload. |
| `target_stores` | Explicit target list such as `redis`, `clickhouse`, `qdrant`, `object_storage`, or `duckdb_export`. |
| `status` | Lifecycle status such as `pending`, `processing`, `projected`, `failed`, or `dead_letter`. |
| `retry_count` | Number of projection attempts. |
| `last_error` | Sanitized last error. Must not contain secrets. |
| `created_at` | Event creation time. |
| `processed_at` | Time the event reached a terminal projected state for the target scope. |

Required properties:

- **Idempotent projection:** Reprocessing the same event must not duplicate business effects.
- **Retry-safe:** Workers may retry after crash, timeout, partial failure, or deployment restart.
- **Replayable:** Operators can rebuild projections from a known point without mutating canonical facts.
- **Auditable:** Status, retry count, last error, target stores, and lag must be inspectable.
- **Does not hide failures:** Projection failure must not be swallowed by cache refresh code or background logs only.
- **Supports degraded mode:** If ClickHouse, Qdrant, Redis, or Object Storage is unavailable, canonical writes may still succeed where product policy allows, while projection lag is visible.

This storage outbox complements the existing domain event outbox concept. Future implementation must decide whether to extend the existing outbox table or introduce `storage_outbox_events`, but the architectural contract is that cross-store projections are explicit and replayable.

## 10. Privacy and Identifier Boundaries

Privacy-sensitive systems should avoid one global `user_id` that silently joins payments, access, usage, Telegram bindings, audit trails, devices, workspaces, product activity, and local/offline data.

Prefer context-local identifiers:

- `payment_id_hash`
- `pass_lookup_hash`
- `session_id_hash`
- `api_key_hash`
- `telegram_binding_id`
- `workspace_id_hash`
- `device_binding_id`
- `object_hash`

Database separation principles:

```text
Payment DB != Access DB
Access DB != Usage DB
Usage DB != Telegram Binding DB
Audit DB != Product Data DB
Business DB != Personal Access DB
```

This separation can begin as logical separation inside one PostgreSQL deployment through schemas, table ownership, limited joins, repository boundaries, and access controls. It can later become physical separation through separate databases, clusters, encryption domains, retention policies, and deployment profiles.

Rules:

1. Do not add cross-domain identifiers because they are convenient for dashboards.
2. Use hashed, scoped, salted, or signed identifiers where possible.
3. Keep payment processor references out of product analytics unless explicitly minimized and hashed.
4. Keep Telegram binding identifiers separate from usage analytics.
5. Keep audit records useful without turning them into a universal identity graph.
6. Ensure vector stores receive only authorized, minimized, redacted content.
7. Object keys should not leak identity or sensitive business context.

## 11. Backup, Restore, and Rebuild Strategy

### PostgreSQL

- Use PITR and WAL archive for critical state.
- Run migration smoke checks before promotion.
- Validate schema parity after restore.
- Perform restore drills into staging before production promotion.
- Attach restore evidence, operator sign-off, backup ID, and migration revision to operations evidence.

### TimescaleDB

- Use PostgreSQL-compatible backup and restore workflows.
- Define retention policies by metric class.
- Define compression policies for high-volume historical data.
- Validate continuous aggregate refresh after restore.
- Rebuild derived aggregates from raw hypertables where possible.

### ClickHouse

- Use snapshots and partition export for large analytics tables.
- Track projection schema versions.
- Rebuild from outbox events where possible.
- Rebuild from PostgreSQL, TimescaleDB, and Object Storage canonical sources when outbox retention is insufficient.
- Validate row counts, partition coverage, and replay window completeness after restore.

### Qdrant / pgvector

- Use snapshots for vector indexes.
- Store embedding model versions and chunk manifests.
- Rebuild from canonical documents, proof metadata, object artifacts, and approved text extraction outputs.
- Validate vector collection dimensions and model-version compatibility.
- Never rebuild vectors from unredacted sensitive material.

### Redis

- Treat Redis loss as acceptable for ephemeral state.
- Do not rely on Redis durability for critical state.
- Recreate caches from PostgreSQL, TimescaleDB, ClickHouse, or Object Storage metadata.
- Reconcile queues and locks through durable outbox records where required.

### Object Storage

- Enable versioning for critical buckets.
- Store checksums and signatures.
- Use WORM mode for critical evidence where appropriate.
- Define retention policies and lifecycle rules.
- Reconcile object manifests against PostgreSQL metadata.
- Validate signatures and object hashes during restore drills.

### SQLite

- Use encrypted local backups for Desktop AI, PayRegister, and offline nodes.
- Keep signed sync logs for offline business actions.
- Define device recovery policy, import/export flow, and conflict handling.
- Validate local database integrity before sync.

### DuckDB

- Treat DuckDB as rebuildable local analytics.
- Rebuild from exports, canonical datasets, object archives, and report manifests.
- Do not make DuckDB the only copy of operational facts.

## 12. Degraded Mode Behavior

- **PostgreSQL down:** API is not ready for critical operations. Access decisions, entitlement changes, proof metadata writes, webhook configuration, and audit-critical writes must pause or fail closed. Public health may expose degraded status.
- **Redis down:** System enters slower or limited mode. Caches, rate limits, queues, and websocket fanout degrade. Critical truth remains available from durable stores.
- **Object Storage down:** Proof packet download/export, evidence archive retrieval, signed artifact creation, and deployment evidence export are unavailable. PostgreSQL metadata remains available.
- **TimescaleDB down:** Metrics, candles, provider/source health history, usage time series, and market data views degrade. Operational access still works through PostgreSQL.
- **ClickHouse down:** Historical analytics, Market Time Machine replay, large reports, and long-range delivery analytics degrade. Transactional system continues.
- **Qdrant down:** Semantic search, narrative similarity, evidence similarity, and historical analogy retrieval degrade. Canonical data remains available.
- **SQLite local corruption:** Local recovery/import path is required. Affected Desktop AI, PayRegister, or offline node enters recovery mode and must not silently overwrite canonical state.
- **DuckDB unavailable:** Offline analytical reports and local export analysis are unavailable. Operational workflows continue.

## 13. Security Rules

Strict storage rules apply to every engine, export, log, cache, projection, embedding, test fixture, and backup:

- Do not store seed phrases.
- Do not store Bitcoin private keys.
- Do not store wallet files.
- Do not store xprv/yprv/zprv.
- Do not store raw secrets in logs, embeddings, object storage, ClickHouse, or analytics tables.
- Do not embed sensitive material into vector stores.
- Do not treat browser storage as root of trust.
- Do not store Access Pass as a bearer token.
- Store only hashes, fingerprints, encrypted local material, or signed metadata where appropriate.
- Redact `payload_json`, `metadata_json`, `last_error`, and worker logs before persistence.
- Ensure object keys, cache keys, vector IDs, and analytics dimensions do not leak private identifiers.
- Enforce authorization against canonical metadata before returning object bytes, vector search results, analytics rows, or exports.

## 14. What Not To Do

- Do not replace Postgres entirely.
- Do not put all analytics into Postgres forever.
- Do not use Redis as durable truth.
- Do not use ClickHouse for transactional access decisions.
- Do not use Qdrant as canonical storage.
- Do not store proof packet blobs directly in relational tables.
- Do not write to multiple databases directly from route handlers.
- Do not create one global `user_id` for all privacy-sensitive domains.
- Do not make local SQLite the only copy of important business data without sync/audit.
- Do not let analytics schemas dictate transactional domain boundaries.
- Do not store raw secrets, wallet material, or access bearer tokens in projections.
- Do not hide degraded mode behind stale caches.
- Do not treat object existence as sufficient proof without metadata, checksum, and signature validation.

## 15. Implementation Phases

### Phase 1: Storage Foundation

- PostgreSQL + Redis + Object Storage.
- Storage interfaces and repository boundaries.
- Storage outbox or extension of the existing event outbox for projection workflows.
- Dependency health checks and degraded-state reporting.
- Backup, restore, evidence, and runbook updates.

### Phase 2: Time-Series Upgrade

- TimescaleDB for candles, metrics, provider/source health, access integrity history, mempool fee snapshots, and API usage time series.
- Retention and compression policies.
- Aggregate refresh validation and restore drills.

### Phase 3: Analytics Warehouse

- ClickHouse for Market Time Machine, replay, large analytics, webhook delivery history, provider/source health analytics, and historical similarity run facts.
- Projection workers and replay validation.
- Partitioning, snapshot, and rebuild runbooks.

### Phase 4: Semantic Memory

- pgvector first for constrained semantic use cases when operationally simpler.
- Qdrant later for narrative memory, evidence search, historical similarity, and scale/isolation needs.
- Embedding model versioning, redaction gates, chunk manifests, and rebuild workflows.

### Phase 5: Access Layer Storage

- Access certificates, subscription entitlements, revocation, audit chain, recovery quorum, device binding, session metadata, and privacy-preserving identifiers.
- Redis hot caches and rate limits derived from PostgreSQL truth.
- ClickHouse analytics projections that cannot authorize access.

### Phase 6: Local Sovereignty

- SQLite + DuckDB for Desktop AI, PayRegister, offline reports, local sync logs, and local-first project capsules.
- Signed sync logs, encrypted backups, device recovery, import/export, and conflict resolution.

### Phase 7: Enterprise / Self-hosted

- Tenant isolation.
- WORM evidence archive.
- Air-gapped profile.
- Multi-region strategy.
- Physical database separation where logical boundaries need stronger enforcement.
- Enterprise restore drills and evidence gates.

## 16. Acceptance Criteria for Future Prompts

- [ ] The document defines bounded responsibility for every storage engine.
- [ ] The document clearly states Postgres remains the critical source of truth.
- [ ] Redis is explicitly forbidden as durable truth.
- [ ] ClickHouse is explicitly described as analytics/projection only.
- [ ] Object Storage is used for large evidence/proof artifacts with Postgres metadata.
- [ ] Privacy boundaries and no-global-user-id rules are documented.
- [ ] Backup/restore/rebuild behavior is documented per storage engine.
- [ ] Degraded mode behavior is documented per storage engine.
- [ ] Implementation phases are clear enough to drive the next 64 prompts.
- [ ] No runtime code or migrations are changed in this task.

## Runtime Configuration Contract

Prompt 2 introduces the runtime configuration foundation for this architecture. The settings layer exposes grouped storage configuration under `settings.storage`, including `profile`, `postgres`, `redis`, `object_storage`, `timescale`, `clickhouse`, `vector`, `local`, and `health` groups.

This configuration layer is intentionally contract-first. It validates environment variables, production-like profile requirements, object storage requirements, vector redaction rules, local/offline encryption rules, and degraded-mode controls, but it does not create database clients, run migrations, or connect to TimescaleDB, ClickHouse, Qdrant, Object Storage, SQLite, or DuckDB.

The runtime configuration contract preserves the architecture rules in this document:

- PostgreSQL remains the critical transactional source of truth.
- Redis remains ephemeral and is not durable truth.
- ClickHouse remains analytics/projection only.
- Qdrant/pgvector remain semantic projection stores only, with redaction required.
- Object Storage stores large proof/evidence artifacts while PostgreSQL stores artifact metadata.
- SQLite/DuckDB remain local/offline stores, not global truth.
- No seed phrases, Bitcoin private keys, wallet files, xprv/yprv/zprv material, raw Access Pass bearer tokens, or custody material may be stored in any configured storage system.

## Code-Level Interface Boundary

Initial code-level storage interfaces live in `app/storage/`. These interfaces define engine names, descriptors, profile expectations, safety validation, and health aggregation boundaries only. Concrete TimescaleDB, ClickHouse, Qdrant, Object Storage, SQLite, DuckDB, Redis, and PostgreSQL adapters are added in later phases and must continue to follow the source-of-truth, privacy, and rebuildability rules in this document.

## Object Storage Implementation Note

Prompt 4 begins the Object Storage implementation under `app/storage/object_store/`. The implementation currently provides a tested local filesystem backend, checksum helpers, safety checks, health probing, and an optional MinIO adapter boundary. Existing proof packets, trace reports, evidence archives, release artifacts, and access workflows are not migrated in this prompt; PostgreSQL remains the future canonical metadata and authorization store while Object Storage owns artifact bytes only.

### Storage Artifact Metadata

`StorageArtifact` introduces the PostgreSQL metadata source of truth for large files stored outside relational rows. PostgreSQL records artifact type, domain, object URI, bucket/key, SHA-256 hash, size, content type, retention, redaction, signature metadata, access policy, lifecycle status, and privacy-preserving creator references. Object Storage owns the artifact blob bytes. SHA-256 links metadata to content. Large proof/evidence files, release artifacts, report exports, signed receipts, SBOM/provenance files, and enterprise bundles must not be stored as SQL blobs.

### Storage Outbox Foundation

`storage_outbox_events` is the durable PostgreSQL outbox foundation for future cross-storage projection. Domain services should write canonical PostgreSQL state and enqueue storage outbox rows instead of writing directly to ClickHouse, TimescaleDB, Qdrant/pgvector, Redis, Object Storage, webhook/WebSocket, SDK, or MCP projections. See `docs/STORAGE_OUTBOX.md` for lifecycle, idempotency, retry, dead-letter, and security rules.

## Redis Boundary Policy

Redis remains an ephemeral runtime store for cache, rate limits, short-lived challenge/nonce/session hot state, worker coordination, and fanout. It must not own durable business truth, authorization truth, artifact metadata, audit chains, recovery material, or treasury policy. See `docs/STORAGE_REDIS_BOUNDARIES.md` for allowed use cases, forbidden use cases, key namespace rules, TTL requirements, degraded mode behavior, recovery behavior, and security/privacy requirements.

## Storage Health API

`GET /api/v1/storage/status` reports operational status for PostgreSQL, Redis, Object Storage, TimescaleDB, ClickHouse, Qdrant, SQLite local storage, and DuckDB local storage. The endpoint is a sanitized degraded-mode/status view, not a replacement for liveness/readiness unless operations policy explicitly adopts it. See `docs/STORAGE_HEALTH_API.md` for status meanings, required/optional roles, degraded-mode interpretation, and redaction rules.

## Storage Evidence Artifacts

Prompt 9 adds storage backup/restore evidence helpers under `app/storage/evidence/`. These helpers write redacted JSON artifacts under `artifacts/storage/` for PostgreSQL backup/restore hook evidence, Redis degraded-mode evidence, Object Storage integrity evidence, outbox replay evidence, and storage health evidence. The artifacts are proof inputs only; they do not claim production readiness, successful PITR, or completed restore drills unless supplied checks truthfully support those statuses. See `docs/STORAGE_BACKUP_RECOVERY.md`.

## Storage Deployment Foundation

Prompt 11 connects the initial storage foundation to deployment surfaces. Local compose can run PostgreSQL, Redis, MinIO, API, and worker; Kubernetes exposes S3-compatible object storage settings and placeholder secrets. Helm values expose an external-object-storage-first `objectStorage` configuration contract, but the repository has no Helm templates and therefore no Helm deployment method. See `docs/STORAGE_DEPLOYMENT.md` for local, single-node, Kubernetes, health-check, degraded-mode, and security guidance.

## Operational Runbooks and Production Checklist

Prompt 12 adds production-facing storage operations documents. Operators should use `docs/STORAGE_LAYER_RUNBOOK.md` for incident/degraded-mode handling, `docs/STORAGE_BACKUP_RECOVERY.md` for backup/restore and evidence expectations, and `docs/STORAGE_PRODUCTION_CHECKLIST.md` before enabling the initial PostgreSQL, Redis, Object Storage, and outbox foundation in staging or production-like environments. These documents do not claim production readiness; they define the evidence and signoff required before such claims can be made.

## TimescaleDB Foundation

Prompt 13 begins the Time-Series Upgrade phase by adding an optional TimescaleDB foundation under `app/storage/timeseries/`. The foundation includes configuration, health/status reporting, identifier-safe hypertable helpers, and a base time-series repository abstraction. No BTC candle, provider health, metric usage, access integrity, or market domain tables are migrated in this prompt. PostgreSQL remains the transactional source of truth for access certificates, subscription entitlements, revocations, recovery quorums, policy decisions, artifact metadata, and outbox records.

## Prompt 14/65 Timescale Market Time-Series Status

BTC price points, BTC candles, and mempool fee snapshots are now compatible with the TimescaleDB foundation. Plain PostgreSQL and SQLite-compatible test fallback remain supported when `TIMESCALE_ENABLED=false`. TimescaleDB is the operational time-series store for these bounded market queries; ClickHouse analytics projection and Market Time Machine warehouse work remain future prompts.

## Provider and Source Health Time-Series Storage

Prompt 15 moves provider/source health history into the Storage Layer without changing the canonical ownership model. PostgreSQL remains the source of truth for provider/source definitions, policy metadata, and any transactional decisions. TimescaleDB-compatible tables now store historical observations for provider health, source health, provider confidence events, and source confidence events so operators can build bounded dashboards, degraded-mode evidence, provider trust matrices, and future ClickHouse projections.

Redis may cache current health state for speed, but it is not durable truth. ClickHouse remains future analytics/replay work and must receive provider/source health history through projectors rather than direct route-handler writes. The time-series records must not contain seed phrases, Bitcoin private keys, wallet files, xprv/yprv/zprv, API secrets, raw auth headers, private provider credentials, or unredacted URLs containing tokens.

When TimescaleDB is disabled, the new tables operate as normal PostgreSQL-compatible tables. When TimescaleDB is enabled, migrations may convert them to hypertables on `observed_at`; failure of historical health storage should degrade dashboards and operator reporting, not critical transactional truth.

## Metric Usage Time-Series Storage

Prompt 16 adds `metric_usage_events` as a TimescaleDB-compatible operational usage table. It records metric/API/SDK/MCP/webhook/WebSocket usage with privacy-safe subject hashes, request counts, credit costs, decisions, and bounded metadata. TimescaleDB supports dashboards, quota analysis, access-integrity history, developer reports, and future billing evidence; it does not become canonical truth for Access Certificates, Subscription Entitlements, Payment Proofs, Revocation Records, Recovery Quorums, or Policy Rules.

When TimescaleDB is disabled, `metric_usage_events` remains a normal PostgreSQL-compatible table. When enabled and available, migrations may convert it to a hypertable on `recorded_at`. Raw emails, IP addresses, API keys, access tokens, seed phrases, Bitcoin private keys, wallet files, xprv/yprv/zprv, and raw session tokens are forbidden.

## Timescale Operations Layer

Prompt 17 adds operational TimescaleDB definitions for continuous aggregates, retention policies, compression policies, rebuild/status checks, and operator validation scripts. These policies control operational time-series growth and dashboard speed only; they must not delete canonical PostgreSQL audit, access, payment, revocation, recovery, or policy truth. If TimescaleDB is unavailable, dashboards and time-series endpoints degrade without blocking critical PostgreSQL-owned operations.

## Prompt 18/65 Status — ClickHouse Analytics Store Foundation

Prompt 18 introduces the ClickHouse analytics-store foundation only. ClickHouse is disabled by default, exposed through a small `AnalyticsStore` interface, and represented in storage health as a rebuildable analytics projection store.

ClickHouse is for future Market Time Machine, replay, event analytics, and dashboard workloads. PostgreSQL and TimescaleDB remain canonical for operational writes; the storage outbox is the planned handoff path for projections. No ClickHouse production tables, DDL, Market Time Machine projections, or access-control decisions are implemented in this prompt.

## Prompt 20/65 Status — ClickHouse Projection Worker

Prompt 20 adds the initial outbox-to-ClickHouse projection worker. It reads `storage_outbox_events` targeted to `clickhouse`, maps supported event families into analytics rows, inserts through the analytics-store abstraction, and marks outbox events processed only after successful insert. See `docs/STORAGE_CLICKHOUSE_PROJECTIONS.md` for idempotency, retry, dry-run, and privacy rules.

## Prompt 21/65 Status — Market Time Machine Analytics Query Layer

Prompt 21 adds a bounded ClickHouse-backed query service for Market Time Machine analytics. It uses the analytics-store abstraction, isolates SQL builders, returns runtime metadata and degraded-mode responses, and keeps ClickHouse as projection-only analytics storage. See `docs/MARKET_TIME_MACHINE_ANALYTICS.md` for query limits and endpoint behavior.
