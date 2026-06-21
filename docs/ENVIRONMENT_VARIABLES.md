# Environment Variables

This repository uses environment-driven configuration; never commit real secrets.

## Core backend
- `APP_ENV` (dev/staging/production)
- `DEBUG` (`true`/`false`)
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET_KEY`
- `CORS_ALLOW_ORIGINS` (comma-separated origins, never `*`)

## Frontend
- `NEXT_PUBLIC_API_BASE_URL` (public-safe base URL only)

## Notes
- Production should inject secrets from external secure tooling.
- `.env.example` must contain placeholders only.

## CORS production examples
- Local frontend: `CORS_ALLOW_ORIGINS=http://localhost:3000`
- Vercel frontend: `CORS_ALLOW_ORIGINS=https://bitcoin-bastion.vercel.app`
- Production domain: `CORS_ALLOW_ORIGINS=https://bitcoinbastion.org`
- Multiple environments: `CORS_ALLOW_ORIGINS=http://localhost:3000,https://bitcoin-bastion.vercel.app,https://bitcoinbastion.org`

## Storage Layer configuration foundation

These variables configure the future multi-database Bitcoin Bastion Storage Layer. They do not connect new database clients, create migrations, or imply that TimescaleDB, ClickHouse, Qdrant, Object Storage, SQLite, or DuckDB integrations are implemented yet.

Security rule: never store Bitcoin seed phrases, Bitcoin private keys, wallet files, xprv/yprv/zprv material, raw Access Pass bearer tokens, raw secrets in vector stores, or custody material in any configured storage system. Recovery or access material may only be represented as hashes, fingerprints, encrypted local material, signed metadata, or non-custodial references where appropriate.

### Core profile

- `STORAGE_PROFILE` defaults to `development`. Allowed values are `development`, `test`, `single_node`, `self_hosted`, `staging`, `production`, `enterprise`, and `air_gapped`.

### PostgreSQL

PostgreSQL remains the transactional source of truth for critical state.

- `DATABASE_URL` remains supported for backward compatibility.
- `POSTGRES_URL` is the canonical future PostgreSQL variable.
- `POSTGRES_READ_REPLICA_URL` optionally configures a future read replica.
- `POSTGRES_SSL_MODE` defaults to `prefer`.
- `POSTGRES_POOL_SIZE`, `POSTGRES_MAX_OVERFLOW`, `POSTGRES_POOL_TIMEOUT_SECONDS`, and `POSTGRES_STATEMENT_TIMEOUT_MS` configure future pool behavior.

In production, if `DATABASE_URL` and `POSTGRES_URL` are both set, they must match.

### Redis

Redis is not durable truth. It is only for cache, queues, rate limits, websocket fanout, short-lived locks, idempotency windows, and short-lived coordination. Redis boundary rules, TTL requirements, and key namespace policy are documented in `docs/STORAGE_REDIS_BOUNDARIES.md`.

- `REDIS_URL`
- `REDIS_TLS_ENABLED`
- `REDIS_KEY_PREFIX`
- `REDIS_EPHEMERAL_ONLY` defaults to `true` and should remain true.

### Object Storage / MinIO / S3

Object Storage stores proof packets, evidence archives, signed artifacts, and exports. PostgreSQL stores artifact metadata, object keys, hashes, signatures, lifecycle state, retention policy, and authorization metadata.

- `OBJECT_STORAGE_ENABLED` defaults to `false`.
- `OBJECT_STORAGE_PROVIDER` defaults to `disabled`. Allowed values are `disabled`, `local`, `minio`, `s3`, and `compatible_s3`.
- `OBJECT_STORAGE_ENDPOINT`, `OBJECT_STORAGE_PUBLIC_ENDPOINT`, `OBJECT_STORAGE_BUCKET`, `OBJECT_STORAGE_REGION`, `OBJECT_STORAGE_ACCESS_KEY`, and `OBJECT_STORAGE_SECRET_KEY` configure artifact storage access.
- `OBJECT_STORAGE_USE_SSL`, `OBJECT_STORAGE_SECURE`, and `OBJECT_STORAGE_FORCE_PATH_STYLE` configure S3-compatible client behavior.
- `OBJECT_STORAGE_DEFAULT_RETENTION_DAYS` configures the default artifact retention window.
- `OBJECT_STORAGE_EVIDENCE_RETENTION_DAYS` configures the evidence artifact retention window.
- `OBJECT_STORAGE_MAX_ARTIFACT_BYTES` / `OBJECT_STORAGE_MAX_OBJECT_BYTES` set the maximum artifact object size.
- `OBJECT_STORAGE_WORM_ENABLED` defaults to `false`.
- `OBJECT_STORAGE_CHECKSUM_REQUIRED` defaults to `true` and must remain true when object storage is enabled.

### TimescaleDB

TimescaleDB is the future time-series store for metrics, BTC candles, provider health, source health, mempool snapshots, and usage windows.

- `TIMESCALE_ENABLED` defaults to `false`.
- `TIMESCALE_URL` may be empty when TimescaleDB is expected to share the primary PostgreSQL URL.
- `TIMESCALE_SCHEMA` defaults to `timeseries`.
- `TIMESCALE_RETENTION_DAYS` must be positive when set.
- `TIMESCALE_COMPRESSION_ENABLED` and `TIMESCALE_CONTINUOUS_AGGREGATES_ENABLED` configure future time-series behavior.

### ClickHouse

ClickHouse is analytics/projection only. It must not be used for transactional access decisions, entitlement truth, revocation truth, or billing truth.

- `CLICKHOUSE_ENABLED` defaults to `false`.
- `CLICKHOUSE_URL` is required when ClickHouse is enabled.
- `CLICKHOUSE_DATABASE` defaults to `bitcoin_bastion`.
- `CLICKHOUSE_USER`, `CLICKHOUSE_PASSWORD`, and `CLICKHOUSE_SECURE` configure future client behavior.
- `CLICKHOUSE_PROJECTION_LAG_WARN_SECONDS` must be lower than `CLICKHOUSE_PROJECTION_LAG_CRITICAL_SECONDS`.

### Qdrant / pgvector

Qdrant and pgvector are semantic projection stores only. They must not contain raw secrets, custody material, raw Access Pass bearer tokens, or unredacted sensitive content.

- `VECTOR_STORE_PROVIDER` defaults to `disabled`. Allowed values are `disabled`, `pgvector`, and `qdrant`.
- `QDRANT_ENABLED`, `QDRANT_URL`, `QDRANT_API_KEY`, and `QDRANT_COLLECTION_PREFIX` configure future Qdrant usage.
- `PGVECTOR_ENABLED` configures future pgvector usage.
- `EMBEDDING_MODEL_VERSION` records the future embedding model version.
- `VECTOR_REDACTION_REQUIRED` defaults to `true` and cannot be disabled in production-like profiles.

### Local/offline storage

SQLite and DuckDB are local/offline stores for Desktop AI, PayRegister, offline nodes, exports, and reports. They are not global source of truth.

- `LOCAL_STORAGE_ENABLED` defaults to `false`.
- `LOCAL_SQLITE_PATH` configures the future local operational database path.
- `LOCAL_DUCKDB_PATH` configures the future local analytics database path.
- `LOCAL_STORAGE_ENCRYPTION_REQUIRED` defaults to `true`.
- `LOCAL_SYNC_LOG_ENABLED` defaults to `true`.

### Storage health / degraded mode

- `STORAGE_HEALTH_ENABLED` defaults to `true`.
- `STORAGE_DEGRADED_MODE_ENABLED` defaults to `true`.
- `STORAGE_FAIL_FAST_ON_CRITICAL_MISSING` defaults to `true` and must remain true in production-like profiles.
- `STORAGE_REQUIRE_OBJECT_STORAGE_IN_PRODUCTION` defaults to `true` for production.
- `STORAGE_REQUIRE_BACKUP_EVIDENCE_IN_PRODUCTION` defaults to `true`.

Production-like profiles are `staging`, `production`, `enterprise`, and `air_gapped`. In these profiles, PostgreSQL and Redis configuration must be explicit enough for critical runtime validation. The `air_gapped` profile does not require external managed cloud object storage by default; local MinIO-compatible object storage is acceptable when object storage is enabled.

### Object Storage implementation additions

Prompt 4 adds the first Object Storage infrastructure layer. These variables configure backend selection and local development behavior without migrating existing proof packets or evidence workflows.

- `OBJECT_STORAGE_BACKEND` supports `disabled`, `local`, `minio`, and `s3`. `local` is fully implemented for development and tests; `minio` is behind optional dependency handling; `s3` is reserved for compatible future integration.
- `OBJECT_STORAGE_SECURE` configures HTTPS/TLS behavior for MinIO/S3-compatible clients.
- `OBJECT_STORAGE_LOCAL_ROOT` defaults to `.storage/objects` for local filesystem-backed artifacts.
- `OBJECT_STORAGE_MAX_OBJECT_BYTES` defaults to `104857600` bytes.

Every stored artifact must have a SHA-256 checksum. Object keys and metadata must not contain seed phrases, private keys, wallet files, xprv/yprv/zprv material, raw Access Pass bearer tokens, or raw secrets.
