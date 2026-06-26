# Bitcoin Bastion Storage Backup and Recovery

## 1. Purpose

This document defines the backup, restore, and evidence expectations for the initial Bitcoin Bastion Storage Layer foundation. It does not claim production readiness, disaster-recovery readiness, successful point-in-time recovery, or completed restore drills by itself.

The current foundation covers:

- PostgreSQL as transactional source of truth.
- Redis as ephemeral runtime state only.
- Object Storage / MinIO / S3 as the artifact/blob layer.
- PostgreSQL artifact metadata and durable storage outbox rows.
- Evidence JSON artifacts that record what was checked, skipped, failed, or not configured.

Future engines such as TimescaleDB, ClickHouse, Qdrant/pgvector, SQLite, and DuckDB are mentioned only as future phases unless later prompts implement them.

## 2. Recovery Objectives

Environment-specific recovery objectives must be defined before claiming production readiness. The baseline targets to document per environment are:

| Objective | Required evidence before production claims |
| --- | --- |
| RPO for PostgreSQL | WAL archive/PITR strategy, backup cadence, and restore verification. |
| RTO for PostgreSQL | Timed restore drill in an isolated environment. |
| Object Storage integrity | SHA-256 validation for sampled or complete artifact sets. |
| Redis recovery | Proof that critical truth does not exist only in Redis. |
| Outbox replay | Demonstration that pending/retry events can be inspected and safely replayed. |
| Operator signoff | Evidence artifact plus human review for release/deployment gates. |

If these objectives are not defined or tested, the correct status is `skipped`, `not_configured`, `warn`, or `fail`, not `pass`.

## 3. PostgreSQL Backup Strategy

PostgreSQL is the source of truth for critical state, including artifact metadata, outbox records, policy metadata, audit metadata, access/payment/subscription records in future Access Layer work, and other transactional records.

The backup strategy should include:

- Point-in-time recovery (PITR) design.
- WAL archive storage and retention policy.
- Daily or environment-appropriate snapshots.
- Backup encryption and secret-managed access.
- Backup verification that does not rely only on command exit code.
- Migration smoke checks against backup/restore targets.
- Schema parity validation between expected metadata and restored database schema.
- Backup evidence generation for every scheduled or release-gate backup check.

Do not store database passwords, private URLs, object storage secrets, seed phrases, Bitcoin private keys, wallet files, xprv/yprv/zprv material, raw API secrets, or raw Access Pass bearer tokens in backup evidence.

## 4. PostgreSQL Restore Strategy

PostgreSQL restore must be validated in an isolated environment before production readiness is claimed.

The restore strategy should verify:

1. The restore point is known and documented.
2. WAL replay or snapshot restore completes without hidden errors.
3. Migrations can run or are already at the expected revision.
4. Schema parity is validated for `storage_artifacts`, `storage_outbox_events`, and other critical tables.
5. Representative artifact metadata rows resolve to Object Storage objects.
6. Storage outbox rows preserve pending, retry, failed, and dead-letter state.
7. Application health and storage status checks report truthful results.
8. Restore evidence is generated and reviewed before signoff.

A restore drill that skips schema parity, artifact integrity, and outbox inspection is incomplete.

## 5. Redis Recovery Strategy

Redis is not a source of truth. Redis may hold rate limits, locks, short-lived challenge or nonce caches, session hot state, queue/fanout data, idempotency short-window caches, and temporary polling state.

Redis recovery is:

1. Restart or replace Redis.
2. Rebuild caches naturally from PostgreSQL or other canonical stores.
3. Recreate temporary runtime state as requests and workers resume.
4. Invalidate affected sessions or require re-authentication/challenge re-signing if security semantics require it.
5. Allow workers to reacquire locks with TTLs.
6. Validate that no critical truth existed only in Redis.
7. Record degraded-mode evidence when applicable.

Redis loss must not cause loss of Access Certificates, subscription entitlements, payment proof, revocation registry state, audit chains, treasury policy, PSBT workflows, business roles, proof packet metadata, storage artifact metadata, issuer keys, device keys, private keys, seed phrases, wallet files, or xprv/yprv/zprv material.

## 6. Object Storage Backup Strategy

Object Storage stores artifact bytes. PostgreSQL stores canonical metadata for those bytes.

The backup strategy should include:

- Bucket versioning where supported.
- Retention policy documentation.
- SHA-256 commitments stored in PostgreSQL metadata.
- Optional detached signatures and signature key identifiers.
- Object replication or backup bucket strategy for critical evidence.
- WORM/immutable archive controls for future enterprise evidence mode where required.
- Periodic integrity sampling or complete validation for critical evidence sets.
- Evidence records for bucket configuration and checksum validation.

Object Storage must never contain seed phrases, Bitcoin private keys, wallet files, xprv/yprv/zprv material, raw Access Pass bearer tokens, raw API secrets, unredacted sensitive material, or private signed URLs in evidence.

## 7. Object Storage Restore Strategy

Object Storage restore must preserve the relationship between object bytes and PostgreSQL metadata.

Restore validation should:

1. Restore or access the target bucket/prefix.
2. Verify bucket privacy, retention, and versioning expectations.
3. Select artifact metadata rows from PostgreSQL.
4. Fetch corresponding object bytes by `bucket` and `object_key`.
5. Calculate SHA-256 for each sampled or required object.
6. Compare calculated SHA-256 to `storage_artifacts.sha256_hash`.
7. Validate `size_bytes`, `content_type`, and retention metadata where available.
8. Quarantine any metadata/object pair with a mismatch.
9. Generate `object_storage_integrity_evidence.json`.

Object restore success is not complete until PostgreSQL metadata and object bytes agree.

## 8. Artifact Integrity Checks

Artifact integrity is anchored by SHA-256.

For each artifact validation check, record:

- artifact identifier or non-sensitive object reference;
- bucket and object key if safe to disclose in the evidence context;
- expected SHA-256;
- actual SHA-256;
- checksum match status;
- size in bytes;
- content type;
- retention policy;
- optional signature presence;
- validation timestamp and operator/job identifier where available.

A SHA-256 mismatch must be treated as a failure. Do not silently accept corrupted objects or overwrite metadata to match unexpected bytes.

## 9. Outbox Replay Strategy

The storage outbox is durable and stored in PostgreSQL. It is the controlled path for future projections into TimescaleDB, ClickHouse, Qdrant/pgvector, Object Storage projections, Redis fanout, webhooks, SDK, and MCP surfaces.

Recovery logic:

- Unprocessed `pending` or `retry` events can be retried.
- `processing` events with stale locks can be released according to lock policy.
- Failed events must retain `last_error` or a sanitized failure reason.
- Dead-letter events must be observable and included in incident review.
- Projectors must be idempotent before replay is enabled.
- Projection targets must be rebuildable from PostgreSQL truth and outbox/event history where applicable.

Do not repair projection drift by writing directly from route handlers to multiple storage engines.

## 10. Restore Drill Procedure

A minimum restore drill should follow these steps:

1. Select restore point.
2. Restore PostgreSQL into an isolated environment.
3. Validate migrations/schema.
4. Validate `storage_artifacts` metadata.
5. Validate Object Storage artifacts by checksum.
6. Validate outbox state.
7. Run storage health checks.
8. Generate restore evidence.
9. Record operator signoff.

Extended drills should also test Redis restart behavior, Object Storage version restore, outbox stale-lock release, degraded-mode reporting, and rollback communication.

## 11. Evidence Generation

Storage evidence helpers write machine-readable JSON files under:

```text
artifacts/storage/
```

Expected evidence files include:

| Evidence file | Purpose |
| --- | --- |
| `storage_backup_evidence.json` | Records PostgreSQL backup hook readiness from supplied check results. |
| `storage_restore_evidence.json` | Records PostgreSQL restore/schema-parity/PITR hook readiness from supplied check results. |
| `object_storage_integrity_evidence.json` | Records Object Storage checksum/integrity evidence. |
| `outbox_replay_evidence.json` | Records durable outbox replay/idempotency evidence. |
| `storage_health_evidence.json` | Records storage health summaries for current and future engines. |
| `redis_degraded_mode_evidence.json` | Records that Redis is treated as degraded-mode ephemeral infrastructure, not durable truth. |

Expected evidence fields include:

- timestamp or `generated_at`;
- environment;
- storage profile;
- operator or job identifier;
- status;
- checks performed;
- failures;
- artifact count;
- checksum count;
- restore target;
- commit SHA if available;
- warnings and errors;
- non-sensitive metadata.

Evidence checks use `pass`, `warn`, `fail`, `skipped`, and `not_configured`. Missing infrastructure must be recorded truthfully rather than marked as passing.

## 12. Recovery Acceptance Criteria

A recovery exercise is acceptable only when:

- PostgreSQL restore completed in an isolated environment.
- Schema parity and migration smoke checks passed or failures are documented.
- Redis recovery did not require restoring critical truth from Redis.
- Object Storage artifact checks compare SHA-256 metadata against object bytes.
- Outbox state is inspectable and retry/dead-letter records are visible.
- Storage health reports are captured and sanitized.
- Evidence JSON files are generated without secrets.
- Operator signoff records what was tested, skipped, failed, or deferred.

## 13. Future Storage Engines

Later phases may add:

- TimescaleDB backup/restore for time-series hypertables, retention, compression, and continuous aggregate validation.
- ClickHouse partition backup/export and warehouse rebuild procedures.
- Qdrant/pgvector snapshot, embedding model versioning, and rebuild-from-canonical-document procedures.
- SQLite encrypted local backup and signed sync-log procedures.
- DuckDB export/rebuild procedures for offline reports.

Until those engines are implemented and tested, their backup/restore evidence must be `not_configured`, `skipped`, or future-scoped.

## 14. Known Risks

- Backup commands may exist without proven restore success.
- PITR may be documented before it is fully automated in every environment.
- Object Storage bucket versioning or WORM controls may differ by provider.
- Artifact metadata may outlive object bytes if retention and deletion policies are misconfigured.
- Outbox replay can duplicate side effects unless projectors are idempotent.
- Redis loss can invalidate short-lived sessions/challenges and degrade fanout/locks.
- Evidence artifacts prove only the checks they record; they do not by themselves prove production readiness.
