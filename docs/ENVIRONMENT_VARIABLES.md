# Environment Variables

This repository uses environment-driven configuration; never commit real secrets.

## Core backend
- `APP_ENV` (dev/staging/production)
- `DEBUG` (`true`/`false`)
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET_KEY` (legacy JWT auth is disabled; do not use as a primary auth secret)
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

- `ACCESS_SERVER_PEPPER` is secret HMAC pepper material for Access Pass/session lookup hashes and must be injected from a secret manager.
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

## Access Proof-of-Access alignment

The canonical Access environment reference is `docs/ACCESS_ENVIRONMENT.md`. `.env.example` includes safe placeholders for `ACCESS_SERVER_PEPPER`, `ACCESS_ISSUER_KEY_ID`, `ACCESS_ISSUER_PRIVATE_KEY`, session/challenge/request-signing TTLs, BTCPay variables, recovery cooldown, lockdown step-up, and reserved PQ flags.

`ACCESS_REQUEST_MAX_CLOCK_SKEW_SECONDS` is the preferred documentation name for request-signing clock skew. `ACCESS_REQUEST_MAX_SKEW_SECONDS` remains a compatibility setting in current code. Production deployments must keep `ACCESS_ALLOW_MANUAL_GRANTS=false`, must inject issuer private keys and BTCPay secrets from secret management, and must not enable reserved PQ flags until real audited implementations exist.

## LNURL entitlement binding

These variables configure the LNURL Payment Proof to Subscription Entitlement binding service. They do not make invoice creation sufficient for access and do not bypass Payment Proof, principal binding, issuer signing, or Policy Engine checks.

- `LNURL_ENTITLEMENT_BINDING_ENABLED` enables the service when LNURL settlement verification and payment proof issuance are available.
- `LNURL_ENTITLEMENT_ACTIVATION_TTL_SECONDS` controls the short lifetime of post-payment activation references.
- `LNURL_ENTITLEMENT_MAX_ACTIVATION_ATTEMPTS` reserves a bounded attempt budget for activation flows.
- `LNURL_ENTITLEMENT_REQUIRE_PRINCIPAL` keeps production binding principal-first unless pending reservations are explicitly enabled.
- `LNURL_ENTITLEMENT_ALLOW_PENDING_RESERVATIONS` permits anonymous paid reservations that still require fresh Wallet Proof or LNURL-auth before activation.
- `LNURL_ENTITLEMENT_OVERPAYMENT_POLICY` must be explicit; overpayment must not silently grant broader scopes.
- `LNURL_ENTITLEMENT_QUOTE_MAX_AGE_SECONDS` limits dynamic quote staleness where product pricing uses signed/versioned quotes.
- `LNURL_ENTITLEMENT_RETRY_MAX_ATTEMPTS` bounds retry attempts for retryable binding failures.

Never configure raw activation references, payment preimages, wallet private keys, seeds, raw invoices, or session tokens in environment variables.

## LNURL successAction activation

| Variable | Default/example | Purpose |
| --- | --- | --- |
| `LNURL_SUCCESS_ACTION_ENABLED` | `true` | Enables emission of safe LNURL `successAction` presentation metadata. |
| `LNURL_SUCCESS_ACTION_DEFAULT_TYPE` | `url` | Default standard action type (`message` or `url`). |
| `LNURL_SUCCESS_ACTION_BASE_URL` | `https://bastion.example.com` | Bastion-controlled origin used to build activation and receipt URLs. |
| `LNURL_SUCCESS_ACTION_ALLOWED_HOSTS` | `bastion.example.com` | Explicit callback/successAction host allowlist; wildcards are not supported. |
| `LNURL_ACTIVATION_TTL_SECONDS` | `3600` | Default short-lived activation-reference TTL. |
| `LNURL_ACTIVATION_MAX_TTL_SECONDS` | `86400` | Maximum accepted activation TTL. |
| `LNURL_ACTIVATION_SERVER_PEPPER` | `change-me-lnurl-activation-pepper` | HMAC pepper for activation-reference lookup hashes; production deployments must provide a secret value. |
| `LNURL_SUCCESS_ACTION_ONION_MODE_ENABLED` | `false` | Allows validated onion handling only when explicitly enabled. |
| `LNURL_PUBLIC_RECEIPTS_ENABLED` | `true` | Enables safe public receipt status links without access privileges. |
| `LNURL_VAULT_SETUP_LINKS_ENABLED` | `false` | Enables vault setup links; setup still requires wallet/device proof. |

## LNURL-pay comments

| Variable | Default/example | Purpose |
| --- | --- | --- |
| `LNURL_COMMENT_ALLOWED_DEFAULT` | `0` | Disables LNURL-pay comments unless a product/merchant/request policy explicitly permits them. |
| `LNURL_COMMENT_GLOBAL_MAX_CHARS` | `280` | Hard character-count ceiling for `commentAllowed`; booleans/floats/negative values are invalid. |
| `LNURL_COMMENT_GLOBAL_MAX_BYTES` | `2048` | Server-safety byte ceiling for decoded UTF-8 comment input. |
| `LNURL_COMMENT_STORAGE_ENABLED` | `false` | Raw comment storage is disabled by default; the normal persistence mode is hash-only. |
| `LNURL_COMMENT_RETENTION_DAYS` | `7` | Short retention window for comment metadata or explicitly encrypted merchant storage. |
| `LNURL_COMMENT_ALLOW_CONTROL_CHARACTERS` | `false` | Rejects NUL, CRLF, and other control characters by default. |

LNURL comments are untrusted external metadata. They must not authenticate a principal, authorize access, influence settlement, change entitlements, approve refunds/withdrawals, or become AI/system instructions.

## LNURL payerData.auth

- `LNURL_PAYERDATA_AUTH_ENABLED=true` enables the payerData.auth feature for LNURL-pay contexts that request it.
- `LNURL_PAYERDATA_AUTH_DEFAULT_MODE=required` is the recommended unauthenticated checkout policy; deployments may choose `optional` or `disabled` per product policy.
- `LNURL_PAYERDATA_MAX_BYTES=4096` bounds encoded payerdata callbacks.
- `LNURL_PAYERDATA_AUTH_TTL_SECONDS=300` keeps k1 challenges short-lived.
- `LNURL_PAYERDATA_STORE_RAW=false` preserves the default hash/fingerprint-only privacy posture.
- `LNURL_PAYERDATA_ALLOW_EMAIL=false`, `LNURL_PAYERDATA_ALLOW_NAME=false`, `LNURL_PAYERDATA_ALLOW_IDENTIFIER=false`, and `LNURL_PAYERDATA_ALLOW_PUBKEY=false` keep personal payer fields disabled by default.

## LNURL Lightning Address

- `LNURL_LIGHTNING_ADDRESS_ENABLED=true` enables the internal Lightning Address resolver; public `/.well-known/lnurlp` routes are added separately.
- `LNURL_PRIMARY_DOMAIN=bitcoin-bastion.com` is the first-party product Lightning Address domain.
- `LNURL_PAYREGISTER_DOMAIN=payregister.bitcoin-bastion.com` is the separately classified PayRegister Lightning Address domain.
- `LNURL_ALLOWED_CUSTOM_DOMAINS=` must contain only verified merchant domains; unverified domains fail closed.
- `LNURL_ALLOW_ONION_ADDRESSES=false` keeps onion routing disabled unless privacy mode is explicitly configured.
- `LNURL_LIGHTNING_ADDRESS_DEFAULT_MIN_MSAT=1000` and `LNURL_LIGHTNING_ADDRESS_DEFAULT_MAX_MSAT=10000000` bound default descriptor amounts; product pricing remains delegated to the LNURL-pay request service.

- `LNURL_PUBLIC_BASE_URL=https://bitcoin-bastion.com` is the trusted public origin for LNURL discovery documentation and future route generation; do not derive it from untrusted request headers.
- `LNURL_CALLBACK_BASE_URL=https://bitcoin-bastion.com` is the trusted HTTPS (or explicitly enabled onion) origin used to build LNURL-pay callback URLs returned from `/.well-known/lnurlp/{name}`.
- `LNURL_ALLOWED_PUBLIC_HOSTS=bitcoin-bastion.com,payregister.bitcoin-bastion.com` allowlists public discovery hosts and blocks Host/X-Forwarded-Host callback substitution.
- `LNURL_LIGHTNING_ADDRESS_RATE_LIMIT_PER_MINUTE=120` bounds low-cost public Lightning Address discovery requests while returning LNURL-compatible error JSON when exceeded.


## LNURL product Lightning Addresses

- `LNURL_PRODUCT_ADDRESSES_ENABLED=true` enables the versioned product-address registry for first-party subscription products.
- `LNURL_PRODUCT_ADDRESS_DOMAIN=bitcoin-bastion.com` defines the canonical product Lightning Address domain.
- `LNURL_PRODUCT_CONFIG_PATH=config/lnurl_product_addresses.yaml` points at the versioned product catalog; prices and product hashes must come from this trusted server-side catalog or an equivalent signed pricing service.
- `LNURL_PRODUCT_CALLBACK_BASE_URL=https://bitcoin-bastion.com` and `LNURL_PRODUCT_ACTIVATION_BASE_URL=https://bitcoin-bastion.com` are trusted HTTPS origins; do not derive them from user-supplied `Host` headers.
- `LNURL_ENTERPRISE_PUBLIC_PAYMENT_ENABLED=false` keeps Enterprise contract-only unless a dedicated policy and commercial agreement enables a fixed public product.
- `LNURL_PRODUCT_RESPONSE_CACHE_SECONDS=120` bounds any public product discovery cache window to reduce stale-price risk.

### PayRegister LNURL Static QR/NFC

- `PAYREGISTER_LNURL_STATIC_ENABLED` enables the static PayRegister LNURL endpoint services.
- `PAYREGISTER_LNURL_PUBLIC_BASE_URL` is the trusted public HTTPS base URL encoded into QR and NFC payloads.
- `PAYREGISTER_LNURL_CALLBACK_BASE_URL` is the trusted HTTPS base URL used for server-generated LNURL-pay callbacks.
- `PAYREGISTER_LNURL_CONTEXT_TTL_SECONDS` bounds checkout-context lifetime before callback invoice creation.
- `PAYREGISTER_LNURL_COMMENT_ALLOWED_DEFAULT` defaults merchant comments to disabled unless explicitly configured.
- `PAYREGISTER_LNURL_PAYERDATA_AUTH_MODE` defaults payer authentication to optional for PayRegister payments.
- `PAYREGISTER_LNURL_ALLOW_ONION` remains disabled unless an explicit Onion deployment policy is configured.

### Merchant Lightning Address

- `MERCHANT_LN_ADDRESS_ENABLED=true` enables merchant Lightning Address services.
- `MERCHANT_LN_CUSTOM_DOMAINS_ENABLED=false` keeps custom merchant domains disabled unless infrastructure and policy are ready.
- `MERCHANT_LN_DOMAIN_VERIFY_TTL_SECONDS=900` bounds DNS/HTTP verification token lifetime.
- `MERCHANT_LN_HTTP_VERIFY_MAX_REDIRECTS=2` and `MERCHANT_LN_HTTP_VERIFY_MAX_RESPONSE_BYTES=4096` constrain HTTP verification SSRF and amplification risk.
- `MERCHANT_LN_ALLOW_OPERATOR_APPROVAL=false` disables operator-approved custom-domain verification by default.
- `MERCHANT_LN_ALLOW_ONION=false` keeps Onion merchant domains disabled unless explicitly configured.

### LNURL Receipt Packet

- `LNURL_RECEIPT_SIGNING_ENABLED=true` enables issuer signatures for LNURL Receipt Packets when an approved issuer key provider is configured.
- `LNURL_RECEIPT_SCHEMA_EPOCH=1` pins the packet schema epoch used for canonical hashing and verification.
- `LNURL_RECEIPT_PUBLIC_EXPORT_ENABLED=false` keeps public redacted exports disabled unless product policy explicitly enables them.
- `LNURL_RECEIPT_STORE_SANITIZED_COMMENTS=false` keeps raw/sanitized comments out of receipt storage by default; receipts normally retain `comment_hash` only.
- `LNURL_RECEIPT_INCLUDE_PREIMAGE_HASH=true` permits a preimage hash commitment while never exporting raw preimages by default.
- `LNURL_RECEIPT_RETENTION_DAYS=365` documents the default receipt retention policy window for deployments that persist packets.
- `LNURL_RECEIPT_MAX_COMMENT_LENGTH=256` bounds any policy-approved display of sanitized comments.

### LNURL-withdraw Request Service

- `LNURL_WITHDRAW_ENABLED=false` keeps withdraw request creation disabled until policy, callback verification, and payout execution are configured.
- `LNURL_WITHDRAW_CALLBACK_BASE_URL=https://bitcoin-bastion.com` is the trusted origin used for server-generated withdraw callback references; never derive it from client input.
- `LNURL_WITHDRAW_DEFAULT_TTL_SECONDS=300` and `LNURL_WITHDRAW_MAX_TTL_SECONDS=900` bound short-lived k1 request validity.
- `LNURL_WITHDRAW_GLOBAL_MAX_MSAT=10000000` caps policy-approved withdraw request amounts before purpose-specific checks.
- `LNURL_WITHDRAW_REQUIRE_POLICY=true` requires a structured Policy Engine allow decision for valuable withdraw requests.
- `LNURL_WITHDRAW_ALLOW_TEST_FAUCET=false` prevents test/signet faucet issuance unless explicitly enabled for non-mainnet deployments.
- `LNURL_WITHDRAW_ONION_ENABLED=false` keeps Onion callback support disabled unless a deployment-specific Onion policy is configured.

### LNURL withdraw risk and reconciliation

- `LNURL_WITHDRAW_MAINNET_ENABLED=false` keeps Bitcoin mainnet payouts disabled unless explicitly enabled with finite limits.
- `LNURL_WITHDRAW_MAX_SINGLE_MSAT`, daily limit variables, and request-count variables define conservative hard ceilings for risk evaluation.
- `LNURL_WITHDRAW_REQUIRE_ORIGINAL_PAYMENT=true` requires authoritative original payment evidence for refund purposes.
- `LNURL_WITHDRAW_ALLOW_OVER_REFUNDS=false` prevents cumulative refunds above the configured refund percentage.
- `LNURL_WITHDRAW_RECONCILIATION_ENABLED=true` requires ambiguous provider outcomes to be reconciled rather than blindly retried.
