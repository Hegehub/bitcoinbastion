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
- `TIMESCALE_CREATE_EXTENSION` defaults to `false`; extension creation must be explicitly enabled and reviewed for the environment.
- `TIMESCALE_SCHEMA` defaults to `public`.
- `TIMESCALE_DEFAULT_CHUNK_INTERVAL` defaults to `1 day` and is validated before hypertable helpers use it.
- `TIMESCALE_HEALTH_TIMEOUT_SECONDS` defaults to `2`.
- `TIMESCALE_RETENTION_DAYS` must be positive when set.
- `TIMESCALE_COMPRESSION_ENABLED` and `TIMESCALE_CONTINUOUS_AGGREGATES_ENABLED` configure future time-series behavior.

### ClickHouse

ClickHouse is analytics/projection only. It must not be used for transactional access decisions, entitlement truth, revocation truth, or billing truth.

- `CLICKHOUSE_ENABLED` defaults to `false`.
- `CLICKHOUSE_URL` defaults to `http://localhost:8123` and must not include credentials.
- `CLICKHOUSE_HOST` and `CLICKHOUSE_PORT` configure the client endpoint.
- `CLICKHOUSE_DATABASE` defaults to `bitcoin_bastion`.
- `CLICKHOUSE_USERNAME`, `CLICKHOUSE_PASSWORD`, and `CLICKHOUSE_SECURE` configure future client behavior.
- `CLICKHOUSE_CONNECT_TIMEOUT_SECONDS`, `CLICKHOUSE_QUERY_TIMEOUT_SECONDS`, and `CLICKHOUSE_INSERT_TIMEOUT_SECONDS` bound client operations.
- `CLICKHOUSE_PROFILE` defaults to `disabled` and must be non-disabled when ClickHouse is enabled.
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

#### TimescaleDB operations policies

- `TIMESCALE_RETENTION_ENABLED` enables retention policy installation for operational time-series hypertables.
- `TIMESCALE_RAW_MARKET_RETENTION_DAYS`, `TIMESCALE_RAW_HEALTH_RETENTION_DAYS`, and `TIMESCALE_RAW_USAGE_RETENTION_DAYS` configure raw hypertable retention windows.
- `TIMESCALE_AGGREGATE_RETENTION_DAYS` and `TIMESCALE_ACCESS_HISTORY_RETENTION_DAYS` document longer-lived aggregate/access-history expectations.
- `TIMESCALE_COMPRESSION_ENABLED`, `TIMESCALE_COMPRESS_AFTER_DAYS`, `TIMESCALE_COMPRESS_MARKET_AFTER_DAYS`, `TIMESCALE_COMPRESS_HEALTH_AFTER_DAYS`, and `TIMESCALE_COMPRESS_USAGE_AFTER_DAYS` configure compression timing.
- Retention must not delete canonical PostgreSQL audit, access, payment, revocation, recovery, or policy truth.

## ClickHouse Analytics Store

ClickHouse is disabled by default and is used only as a rebuildable analytics projection store.

| Variable | Default | Description |
| --- | --- | --- |
| `CLICKHOUSE_ENABLED` | `false` | Enables the ClickHouse analytics-store client foundation. |
| `CLICKHOUSE_URL` | `http://localhost:8123` | Operator-facing ClickHouse HTTP URL; do not include credentials. |
| `CLICKHOUSE_HOST` | `localhost` | Host passed to the ClickHouse client. |
| `CLICKHOUSE_PORT` | `8123` | HTTP port passed to the ClickHouse client. |
| `CLICKHOUSE_DATABASE` | `bitcoin_bastion` | Analytics projection database name. |
| `CLICKHOUSE_USERNAME` | `default` | ClickHouse username. |
| `CLICKHOUSE_PASSWORD` | empty | ClickHouse password; production-like profiles reject placeholders when enabled. |
| `CLICKHOUSE_SECURE` | `false` | Enables TLS for the ClickHouse client. |
| `CLICKHOUSE_CONNECT_TIMEOUT_SECONDS` | `5` | ClickHouse connection timeout. |
| `CLICKHOUSE_QUERY_TIMEOUT_SECONDS` | `15` | ClickHouse query timeout. |
| `CLICKHOUSE_INSERT_TIMEOUT_SECONDS` | `30` | ClickHouse insert timeout. |
| `CLICKHOUSE_MAX_RETRIES` | `2` | Reserved retry budget for analytics operations. |
| `CLICKHOUSE_PROFILE` | `disabled` | One of `disabled`, `development`, `single_node`, `staging`, `production`, `enterprise`. |

ClickHouse must not store seed phrases, Bitcoin private keys, wallet files, raw access tokens, raw Access Pass values, raw API secrets, or custody material. It is not a source of truth for access, policy, revocation, subscription, payment, or recovery decisions.
## Bastion Proof-of-Access issuer signing

These variables configure future Access Certificate and Subscription Entitlement signing. They do not enable the full Proof-of-Access auth flow by themselves.

- `ACCESS_ISSUER_KEY_ID` is a stable, non-secret key identifier for the active issuer key.
- `ACCESS_ISSUER_PRIVATE_KEY` is secret Ed25519 issuer private-key material. Production must inject it from a secret manager or Kubernetes secret and must never commit it to the repository or bake it into an image.
- `ACCESS_CRYPTO_EPOCH` defaults to `1` and identifies the active Access crypto epoch.
- `ACCESS_SIGNATURE_ALG` defaults to `ed25519`. Future PQ signature suites must remain disabled unless real audited implementations and tests are integrated.
## Bastion Access payment provider foundation

These variables configure the payment intent foundation. They do not enable BTCPay integration or certificate issuance by themselves.

- `ACCESS_ALLOW_MANUAL_GRANTS` defaults to `false`; manual grants must remain disabled unless explicitly authorized for local development, tests, emergency admin grants, or controlled contract grants.
- `ACCESS_DEFAULT_PAYMENT_PROVIDER` defaults to `manual` as a placeholder until a production payment provider is configured. Public endpoints must not expose manual grants without admin/internal authorization.
- `ACCESS_PAYMENT_INTENT_TTL_SECONDS` defaults to `900` and controls payment intent invoice expiry windows.
- `ACCESS_CHALLENGE_TTL_SECONDS` defaults to `300` and controls origin-bound challenge lifetime before Proof-of-Possession session creation.
- `ACCESS_SESSION_TTL_SECONDS` defaults to `900` and controls short-lived Proof-of-Possession session lifetime; raw session tokens must never be stored.
- `ACCESS_REQUEST_MAX_SKEW_SECONDS` defaults to `300` and limits timestamp skew for per-request Proof-of-Possession signatures.
- `ACCESS_REQUEST_SIGNATURE_REQUIRED` defaults to `true`; protected Access requests must fail closed if request signatures are missing or invalid.

## Bastion Access BTCPay Server provider

These variables configure the future production BTCPay payment provider for Access payment intents. Enabling BTCPay does not make invoice creation an entitlement and does not issue Access Certificates by itself. Only verified settled provider events may mark an Access payment intent as paid.

- `ACCESS_BTCPAY_ENABLED` defaults to `false`.
- `ACCESS_BTCPAY_BASE_URL` is the BTCPay Server base URL and is required in production when BTCPay is enabled.
- `ACCESS_BTCPAY_API_KEY` is secret provider API-key material and must be injected from a secret manager or Kubernetes secret.
- `ACCESS_BTCPAY_STORE_ID` identifies the BTCPay store used for Bastion Access invoices.
- `ACCESS_BTCPAY_WEBHOOK_SECRET` is required for webhook HMAC verification and must never be logged or committed.
- `ACCESS_BTCPAY_DEFAULT_CURRENCY` defaults to `BTC`.
- `ACCESS_BTCPAY_CHECKOUT_EXPIRY_MINUTES` defaults to `30`.
- `ACCESS_BTCPAY_HTTP_TIMEOUT_SECONDS` defaults to `10`.
- `ACCESS_BTCPAY_WEBHOOK_TOLERANCE_SECONDS` defaults to `300` for future timestamp-aware webhook policy.
