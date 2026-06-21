# Bitcoin Bastion Storage Layer Runbook

## 1. Purpose

This runbook gives operators a practical procedure for running and investigating the initial Bitcoin Bastion Storage Layer foundation. It documents the currently intended operating model for PostgreSQL, Redis, Object Storage, and the durable storage outbox without claiming that later engines or production automation are complete.

The current operational contract is:

- PostgreSQL is the source of truth for critical state and metadata.
- Redis is not a source of truth; it is ephemeral runtime infrastructure.
- Object Storage stores artifact bytes while PostgreSQL stores canonical artifact metadata.
- The storage outbox is the controlled PostgreSQL path for future projections into other stores.
- No seed phrases, Bitcoin private keys, wallet files, xprv/yprv/zprv material, raw Access Pass bearer tokens, raw API secrets, or custody material may be stored in any storage component.

## 2. Storage Components

| Component | Current role | Canonical responsibility | Notes |
| --- | --- | --- | --- |
| PostgreSQL | Transactional source of truth | Critical metadata, durable outbox rows, artifact metadata, policy/audit metadata | Critical API operations depend on it. |
| Redis | Ephemeral runtime state | Rate limits, locks, short-lived challenge/nonce/session hot state, fanout, worker coordination | Redis is not durable and must be rebuildable or safely discarded. |
| Object Storage / MinIO / S3 | Artifact/blob layer | Proof packets, evidence archives, signed reports, release evidence, SBOM/provenance artifacts, backup evidence | PostgreSQL stores object URI, SHA-256, size, content type, retention, signature, and access metadata. |
| Storage Outbox | Durable projection control path | PostgreSQL-backed event queue for future cross-store projectors | Projectors must be idempotent, retry-safe, observable, and replayable. |
| TimescaleDB | Future time-series layer | Candles, metrics, provider/source health | Not implemented by this runbook. |
| ClickHouse | Future analytics warehouse | Market Time Machine, replay, large analytics | Not implemented by this runbook. |
| Qdrant / pgvector | Future semantic memory | Narrative/evidence similarity search | Not implemented by this runbook. |
| SQLite / DuckDB | Future local/offline layer | Desktop AI, PayRegister, exports, offline reports | Not implemented by this runbook. |

## 3. Normal Operating Mode

Normal operation means:

1. API and worker processes can reach PostgreSQL.
2. Redis is available for cache, queue, rate-limit, lock, polling, and fanout use cases.
3. Object Storage is configured for artifact uploads/downloads when artifact workflows are enabled.
4. `GET /api/v1/storage/status` reports required stores as `ok` or truthfully reports degraded/unavailable state.
5. Storage artifact metadata records include SHA-256 commitments for object bytes.
6. Outbox events are persisted in PostgreSQL before future projectors attempt any cross-store write.
7. Disabled future stores are reported as disabled/not implemented instead of being treated as successful.

## 4. Startup Checks

Before promoting an environment, operators should verify:

- `DATABASE_URL` or `POSTGRES_URL` is configured through the approved secret mechanism.
- PostgreSQL migrations have been applied and schema parity is documented.
- Redis connection information is configured when Redis-backed runtime features are enabled.
- Redis keys are namespaced and time-limited according to `docs/STORAGE_REDIS_BOUNDARIES.md`.
- Object Storage endpoint, bucket, region, path-style mode, retention settings, and credentials are configured through approved deployment surfaces.
- Object Storage bucket creation is complete before artifact-producing workflows are enabled.
- Object Storage credentials are not present in ConfigMaps, logs, frontend bundles, evidence JSON, or public documentation.
- The storage outbox table exists before services enqueue projection work.
- Future engines such as TimescaleDB, ClickHouse, Qdrant, SQLite, and DuckDB remain explicitly disabled or not implemented until their prompts add real integrations.

## 5. Health Checks

Operators should use existing liveness/readiness endpoints for process-level checks and `GET /api/v1/storage/status` for storage-specific interpretation.

Storage health checks should be read as operational signals:

- PostgreSQL failure is critical for transactional truth.
- Redis failure is degraded mode unless a current runtime path explicitly requires it for process readiness.
- Object Storage failure degrades artifact upload/download/export workflows.
- Future-store disabled/not implemented statuses should not be hidden or converted into success.

Health output must not expose database URLs, passwords, access keys, secret keys, signed private URLs, raw IP addresses, wallet addresses, or user-specific identifiers.

## 6. Storage Status Endpoint

Use:

```text
GET /api/v1/storage/status
```

Expected current-store interpretation:

```json
{
  "postgres": "ok",
  "redis": "ok",
  "object_storage": "ok",
  "timescale": "disabled",
  "clickhouse": "disabled",
  "qdrant": "disabled"
}
```

The actual response is structured and may include role, purpose, latency, details, summary, and degraded-mode impact. Treat this endpoint as a storage/degraded-mode endpoint, not a replacement for liveness/readiness unless operations policy explicitly adopts it.

## 7. Common Failure Scenarios

| Scenario | Expected status | Operator action |
| --- | --- | --- |
| PostgreSQL unavailable | `unavailable` or critical degraded status | Stop critical writes, inspect database connectivity, fail readiness, preserve logs/evidence. |
| Redis unavailable | degraded runtime state | Confirm no critical truth is Redis-only, restart Redis, allow caches/locks/sessions to rebuild safely. |
| Object Storage unavailable | artifact workflows degraded | Preserve PostgreSQL metadata, pause artifact export/upload/download flows, validate bucket/credentials/network. |
| Outbox backlog growing | degraded projection path | Inspect pending/retry/dead-letter counts, pause projectors if unsafe, avoid manual cross-store writes. |
| SHA-256 mismatch | integrity failure | Quarantine artifact metadata, block trust in object bytes, generate integrity evidence, escalate. |
| Future store disabled | disabled/not implemented | Confirm expected for current phase; do not mark as production-ready. |

## 8. Degraded Mode Behavior

Degraded mode must be explicit, observable, and reversible.

- PostgreSQL down → API is not ready for critical operations; workers should stop writing critical truth; outbox processing should pause or fail safely.
- Redis down → critical truth remains recoverable from PostgreSQL; access checks may become slower; rate limiting may fall back to bounded in-memory behavior where implemented; WebSocket/fanout/locks may degrade.
- Object Storage down → artifact upload/download/export is unavailable; metadata can remain visible in PostgreSQL; proof packet export may fail without losing metadata truth.
- Outbox degraded → future projections may lag; events must remain inspectable and retry/dead-letter outcomes must be visible.
- Future ClickHouse/Qdrant/Timescale failure → analytics/search/time-series projections degrade; transactional truth remains PostgreSQL-owned.

No critical security check may silently disappear because a non-canonical store is unavailable.

## 9. Outbox Operations

The storage outbox is the only approved foundation for future cross-store projections.

Operator expectations:

- Domain services write canonical PostgreSQL state and outbox rows in the same transaction when projection is needed.
- Projector workers claim events, process them idempotently, and record success, retryable failure, permanent failure, or dead-letter state.
- Retries must be bounded and visible.
- Failed projections must not silently disappear.
- Dead-letter events must be observable and included in incident review.
- Replay must be safe because projectors use idempotency keys, aggregate identifiers, and deterministic target behavior.

Do not write from route handlers directly to ClickHouse, TimescaleDB, Qdrant, Redis fanout, webhooks, SDK/MCP projections, or Object Storage projections as a casual side effect.

## 10. Object Storage Operations

Object Storage stores large immutable or semi-immutable artifacts, including:

- proof packets;
- evidence archives;
- release evidence;
- trace exports;
- signed reports;
- SBOM/provenance artifacts;
- backup/restore evidence;
- redacted enterprise evidence bundles.

PostgreSQL metadata must include, where applicable:

- `object_uri`;
- `bucket` and `object_key`;
- `sha256_hash`;
- `size_bytes`;
- `content_type`;
- `retention_policy` and `retention_until`;
- signature metadata;
- access-policy metadata.

Object Storage must never contain seed phrases, Bitcoin private keys, wallet files, xprv/yprv/zprv material, raw Access Pass bearer tokens, raw API secrets, or unredacted sensitive material.

## 11. Redis Loss Scenario

If Redis is restarted, flushed, or unavailable:

1. Confirm PostgreSQL is available and critical truth is intact.
2. Confirm no active runbook, incident, or service has placed critical truth only in Redis.
3. Expect caches, locks, rate-limit counters, polling state, challenge state, nonce caches, session hot state, and fanout buffers to be lost or recreated.
4. Invalidate affected sessions or require challenge re-signing where security semantics require it.
5. Allow workers to reacquire locks rather than restoring old lock state.
6. Verify storage status reports Redis degradation or recovery truthfully.
7. Record incident notes if user re-authentication or operational delay occurred.

Redis is not a source of truth and must not be recovered as though it held canonical business state.

## 12. PostgreSQL Degradation Scenario

If PostgreSQL is degraded or unavailable:

1. Treat critical API operations as not ready.
2. Stop or pause workers that write critical metadata, artifact records, audit records, policy records, or outbox rows.
3. Avoid writing canonical truth to Redis, Object Storage metadata sidecars, analytics stores, or local files as a substitute.
4. Inspect database connectivity, disk, migration state, and pool saturation.
5. Preserve logs and generate incident evidence where safe.
6. Restore from verified backups only through the approved restore procedure.
7. Validate schema parity, migrations, artifact metadata, outbox state, and storage health before resuming critical writes.

## 13. Artifact Integrity Validation

Artifact integrity validation compares PostgreSQL metadata to object bytes:

1. Read `storage_artifacts` metadata for `bucket`, `object_key`, `sha256_hash`, `size_bytes`, and `content_type`.
2. Fetch or stream object bytes through the approved Object Storage abstraction.
3. Calculate SHA-256 without logging object bytes or secrets.
4. Compare calculated SHA-256 to the stored `sha256_hash`.
5. Validate expected size and content type where available.
6. If mismatch occurs, quarantine metadata, block trust in the object, generate evidence, and escalate.

A checksum match proves byte consistency for that object at that time. It does not prove business correctness, authorization correctness, or production readiness by itself.

## 14. Operator Commands

Use project-specific commands where available. Example commands for local validation:

```bash
# Inspect local storage status endpoint once the app is running.
curl -s http://localhost:8000/api/v1/storage/status | python -m json.tool

# Run storage-focused tests.
pytest tests/storage

# Render local compose configuration without starting services.
docker compose config
```

Do not paste secrets into shell history. Prefer approved secret managers or local `.env` files that are excluded from version control.

## 15. Escalation Rules

Escalate immediately when:

- PostgreSQL is unavailable in a staging or production-like environment.
- Artifact SHA-256 validation fails.
- Object Storage evidence bucket is public or has unexpected retention changes.
- Outbox dead-letter volume grows or contains security/audit-critical events.
- Redis appears to be the only holder of any critical business, authorization, recovery, or audit state.
- Any seed phrase, Bitcoin private key, wallet file, xprv/yprv/zprv material, raw Access Pass bearer token, or raw API secret is found in logs, evidence, Object Storage, Redis, outbox payloads, or metadata.

## 16. Known Limitations

- This runbook documents the initial foundation; it does not certify production readiness.
- TimescaleDB, ClickHouse, Qdrant/pgvector, SQLite, and DuckDB are future phases unless later prompts add real integrations.
- Backup, PITR, restore drills, WORM retention, and enterprise evidence gates require environment-specific proof before they can be claimed as operational.
- The storage outbox currently provides the durable foundation; actual projectors must be implemented and validated separately.
- Object Storage metadata in PostgreSQL and SHA-256 checks prove artifact integrity, not authorization truth.
