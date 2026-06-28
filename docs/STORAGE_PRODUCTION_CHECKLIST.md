# Bitcoin Bastion Storage Production Checklist

## 1. Purpose

This checklist is used before enabling the initial Bitcoin Bastion Storage Layer foundation in staging or production-like environments. Completing this checklist does not by itself certify production readiness; it records the minimum evidence operators must gather before making environment-specific readiness claims.

## 2. Scope

- [ ] PostgreSQL is treated as transactional source of truth.
- [ ] Redis is treated as ephemeral runtime state only.
- [ ] Object Storage / MinIO / S3 is treated as the artifact/blob layer.
- [ ] PostgreSQL stores canonical artifact metadata.
- [ ] The storage outbox is the controlled path for future projections.
- [ ] TimescaleDB, ClickHouse, Qdrant/pgvector, SQLite, and DuckDB are treated as future phases unless separately implemented and validated.

## 3. Environment Configuration

- [ ] `STORAGE_PROFILE` is set to the intended environment profile.
- [ ] `DATABASE_URL` or `POSTGRES_URL` is configured through the approved secret mechanism.
- [ ] Redis connection settings are configured through the approved secret/config mechanism.
- [ ] Object Storage endpoint, bucket, provider, region, path-style mode, and retention values are configured.
- [ ] Object Storage credentials are provided only through approved secret mechanisms.
- [ ] Local/dev MinIO defaults such as `minioadmin` are not used in staging or production.
- [ ] Disabled future stores are explicitly disabled rather than silently omitted.
- [ ] `/api/v1/storage/status` is reachable by operators from the expected network boundary.

## 4. PostgreSQL Readiness

- [ ] PostgreSQL connectivity is verified from API and worker runtimes.
- [ ] Required migrations have been applied.
- [ ] `storage_artifacts` table exists if artifact metadata workflows are enabled.
- [ ] `storage_outbox_events` table exists if projection/outbox workflows are enabled.
- [ ] Database pool limits and statement timeout values are reviewed.
- [ ] PITR/WAL archive strategy is documented for the environment.
- [ ] A restore drill has been executed in a non-production environment.
- [ ] Schema parity and migration smoke checks are captured as evidence.

## 5. Redis Readiness

- [ ] Redis is configured as ephemeral state, not canonical truth.
- [ ] Redis key namespaces follow `bb:{env}:...` or the approved equivalent.
- [ ] Locks have TTLs.
- [ ] Challenge, nonce, session-hot, polling, fanout, and idempotency-short-window keys expire.
- [ ] Redis outage behavior is documented as degraded mode.
- [ ] Operators have verified that no critical state exists only in Redis.
- [ ] Redis credentials and connection strings are not logged.

## 6. Object Storage Readiness

- [ ] Object Storage bucket exists and is not public.
- [ ] Bucket access is least-privilege for API and worker identities.
- [ ] Object Storage credentials are not logged or exposed to frontend code.
- [ ] Artifact uploads record SHA-256 metadata in PostgreSQL.
- [ ] Artifact uploads record `size_bytes`, `content_type`, retention policy, and object URI metadata where applicable.
- [ ] Bucket retention/versioning expectations are documented.
- [ ] Evidence and proof artifacts have an approved retention policy.
- [ ] Object Storage health check or manual bucket check has been captured.
- [ ] Object Storage outage behavior is documented as artifact upload/download degradation, not metadata loss.

## 7. Outbox Readiness

- [ ] Domain services do not write casually to multiple storage engines from route handlers.
- [ ] Outbox events are stored durably in PostgreSQL.
- [ ] Outbox event payloads avoid raw secrets and custody material.
- [ ] Idempotency keys are used where duplicate enqueue risk exists.
- [ ] Retry and dead-letter behavior is visible to operators.
- [ ] Outbox backlog thresholds are defined or explicitly deferred.
- [ ] Future projectors are required to be idempotent before replay is enabled.

## 8. Security Checklist

- [ ] No seed phrases stored.
- [ ] No Bitcoin private keys stored.
- [ ] No wallet files stored.
- [ ] No xprv/yprv/zprv stored.
- [ ] No raw secrets in logs.
- [ ] No raw secrets in object storage metadata.
- [ ] No raw secrets in analytics projections.
- [ ] No raw Access Pass bearer tokens in storage payloads, metadata, Redis, Object Storage, evidence, or logs.
- [ ] No Redis-only critical state.
- [ ] No public object storage bucket for evidence artifacts.
- [ ] No route handler directly writes to multiple storage engines.
- [ ] Object Storage must never contain seed phrases, Bitcoin private keys, wallet files, xprv/yprv/zprv material, raw API secrets, unredacted sensitive material, or private signed URLs in evidence.

## 9. Privacy Checklist

- [ ] No global user_id introduced for privacy-sensitive domains.
- [ ] Context-local identifiers are used where possible.
- [ ] Payment, access, usage, Telegram binding, audit, and product data are logically separable.
- [ ] Object Storage metadata avoids personal data by default.
- [ ] Analytics projections avoid raw secrets and unnecessary identifiers.
- [ ] Redis keys avoid raw user identifiers, raw IP addresses, raw access pass tokens, raw API keys, and raw invoice IDs where avoidable.
- [ ] Evidence artifacts contain hashes, fingerprints, counts, statuses, and redacted metadata rather than raw identifiers.

## 10. Backup and Restore Checklist

- [ ] PostgreSQL backup command/path is documented.
- [ ] PostgreSQL restore command/path is documented.
- [ ] PITR/WAL archive configuration is documented or explicitly deferred.
- [ ] Daily or environment-appropriate snapshot cadence is documented.
- [ ] Restore drill has been executed in an isolated non-production environment.
- [ ] `storage_artifacts` metadata was validated during restore drill.
- [ ] Object Storage artifacts were validated by SHA-256 during restore drill.
- [ ] Outbox state was inspected during restore drill.
- [ ] `storage_backup_evidence.json` was generated or a truthful skipped/not_configured record exists.
- [ ] `storage_restore_evidence.json` was generated or a truthful skipped/not_configured record exists.
- [ ] `object_storage_integrity_evidence.json` was generated or a truthful skipped/not_configured record exists.
- [ ] `outbox_replay_evidence.json` was generated or a truthful skipped/not_configured record exists.

## 11. Observability Checklist

- [ ] Storage status endpoint reports PostgreSQL, Redis, Object Storage, TimescaleDB, ClickHouse, Qdrant, SQLite local, and DuckDB local state.
- [ ] Required store failures are visible and not downgraded to success.
- [ ] Optional/future disabled stores are represented as disabled/not implemented.
- [ ] Redis fallback/degraded mode is observable.
- [ ] Object Storage errors do not expose credentials.
- [ ] Outbox backlog, retry, failed, and dead-letter states have an operator inspection path.
- [ ] Artifact integrity failures generate alertable evidence or incident records.

## 12. Degraded Mode Checklist

- [ ] PostgreSQL down → API not ready for critical operations.
- [ ] Redis down → limited/slower mode, but truth remains in PostgreSQL.
- [ ] Object Storage down → artifact upload/download unavailable; metadata still protected.
- [ ] Outbox backlog → visible alert or health degradation.
- [ ] Future ClickHouse/Qdrant/Timescale failure → projection/search/analytics degraded, not transactional truth loss.
- [ ] Degraded mode is documented in operator-facing runbooks.
- [ ] No critical security check silently disappears when a non-canonical store is unavailable.

## 13. Release Gate Checklist

- [ ] Storage deployment configuration is reviewed for the target environment.
- [ ] Kubernetes/Helm/compose values do not contain real secrets committed to source control.
- [ ] Storage docs and runbooks are linked from deployment/release notes where appropriate.
- [ ] Storage tests pass in CI or local release validation.
- [ ] Evidence files are generated or skipped/not_configured records are documented truthfully.
- [ ] Known limitations are recorded before promotion.
- [ ] Operators understand that this foundation is not a claim that future TimescaleDB, ClickHouse, Qdrant, SQLite, or DuckDB phases are implemented.

## 14. Rollback Checklist

- [ ] Rollback plan identifies database migration state and whether rollback is schema-safe.
- [ ] Artifact metadata changes are preserved or intentionally quarantined.
- [ ] Object Storage objects created during the release are listed by non-sensitive object reference.
- [ ] Outbox events created during the release are inspected before retry/replay.
- [ ] Redis caches/locks can be safely flushed or allowed to expire.
- [ ] Operators know which user-visible artifact workflows may be unavailable during rollback.
- [ ] Rollback evidence is generated and reviewed.

## 15. Signoff

- [ ] Engineering owner reviewed storage configuration.
- [ ] Operations owner reviewed runbooks and recovery plan.
- [ ] Security owner reviewed secret handling and no-custody constraints.
- [ ] Privacy owner reviewed identifier boundaries.
- [ ] Release owner reviewed degraded-mode and rollback behavior.
- [ ] Signoff explicitly states which checks passed, warned, failed, skipped, or were not configured.
