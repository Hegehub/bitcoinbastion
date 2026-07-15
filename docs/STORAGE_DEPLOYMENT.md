# Storage Deployment

This document explains how to expose the initial Bitcoin Bastion Storage Foundation in local, self-hosted, Kubernetes, staging, and production-style deployments. The Helm material is a values contract only, not a working deployment path.

The initial deployment foundation covers:

- PostgreSQL as transactional source of truth.
- Redis as cache, queue, rate-limit, fanout, lock, and short-lived ephemeral state.
- Object Storage / MinIO / S3-compatible storage for proof packets, evidence archives, signed reports, release artifacts, backup evidence, SBOM/provenance artifacts, and redacted exports.

It does not deploy TimescaleDB, ClickHouse, Qdrant, DuckDB, SQLite sync, pgvector, or Access Layer storage. Those are later prompts.

## Local development

Use the standard compose file:

```bash
docker compose up db redis minio minio-init app worker
```

The compose stack includes PostgreSQL, Redis, MinIO, API, worker, and a `minio-init` bucket bootstrap service. The bootstrap creates:

```text
bitcoin-bastion-artifacts
```

Local MinIO defaults use `minioadmin` credentials. These values are unsafe local-development defaults only.

Recommended local object storage environment:

```env
OBJECT_STORAGE_ENABLED=true
OBJECT_STORAGE_PROVIDER=minio
OBJECT_STORAGE_BACKEND=minio
OBJECT_STORAGE_ENDPOINT=http://minio:9000
OBJECT_STORAGE_PUBLIC_ENDPOINT=http://localhost:9000
OBJECT_STORAGE_BUCKET=bitcoin-bastion-artifacts
OBJECT_STORAGE_REGION=local
OBJECT_STORAGE_ACCESS_KEY=minioadmin
OBJECT_STORAGE_SECRET_KEY=minioadmin
OBJECT_STORAGE_SECURE=false
OBJECT_STORAGE_FORCE_PATH_STYLE=true
OBJECT_STORAGE_DEFAULT_RETENTION_DAYS=365
OBJECT_STORAGE_EVIDENCE_RETENTION_DAYS=2555
OBJECT_STORAGE_MAX_ARTIFACT_BYTES=104857600
```

## Single-node and self-hosted setup

Single-node operators may use MinIO with a persistent volume. This is suitable for local/self-host/single-node testing and small deployments only when the operator also maintains:

- persistent volume backups;
- restore drills;
- object retention policy;
- evidence artifact checksums;
- `/api/v1/storage/status` monitoring;
- documented degraded-mode procedures.

Managed S3-compatible storage is safer for serious deployments.

## Kubernetes setup

The canonical Kubernetes base lives under:

```text
deploy/kubernetes/base/
```

The base ConfigMap exposes non-secret object storage settings:

- `OBJECT_STORAGE_ENABLED`
- `OBJECT_STORAGE_PROVIDER`
- `OBJECT_STORAGE_BACKEND`
- `OBJECT_STORAGE_ENDPOINT`
- `OBJECT_STORAGE_PUBLIC_ENDPOINT`
- `OBJECT_STORAGE_BUCKET`
- `OBJECT_STORAGE_REGION`
- `OBJECT_STORAGE_SECURE`
- `OBJECT_STORAGE_FORCE_PATH_STYLE`
- `OBJECT_STORAGE_DEFAULT_RETENTION_DAYS`
- `OBJECT_STORAGE_EVIDENCE_RETENTION_DAYS`
- `OBJECT_STORAGE_MAX_ARTIFACT_BYTES`

The base Secret example exposes placeholders only:

- `OBJECT_STORAGE_ACCESS_KEY`
- `OBJECT_STORAGE_SECRET_KEY`

Use ExternalSecret, SealedSecret, SOPS, Vault, cloud secret manager, or equivalent for real environments. Do not commit real object storage credentials.

## MinIO Kubernetes example

`deploy/kubernetes/base/minio.example.yaml` is an example only. It is not included in the base kustomization and is not a default production dependency.

Use it only for local, self-hosted, or single-node testing after replacing placeholder secrets and choosing a persistent storage class.

## Helm values placeholder

`helm/bitcoin-bastion` contains `Chart.yaml` and the following values contract,
but no `templates/` tree. It cannot currently render or install Bitcoin Bastion
and must not be listed as a supported deployment method.

```yaml
objectStorage:
  enabled: false
  provider: s3
  endpoint: ""
  publicEndpoint: ""
  bucket: bitcoin-bastion-artifacts
  region: ""
  secure: true
  forcePathStyle: false
  defaultRetentionDays: 365
  evidenceRetentionDays: 2555
  maxArtifactBytes: 104857600
  existingSecret: ""
  accessKeySecretKey: OBJECT_STORAGE_ACCESS_KEY
  secretKeySecretKey: OBJECT_STORAGE_SECRET_KEY
```

External object storage is preferred by default. Bundled MinIO is not defined
by this placeholder. Implementing and validating chart templates would be a
separate deployment change.

## Storage health check

Use the operational endpoint:

```http
GET /api/v1/storage/status
```

Expected initial foundation shape:

```json
{
  "stores": {
    "postgres": {"status": "ok"},
    "redis": {"status": "ok"},
    "object_storage": {"status": "ok"},
    "timescale": {"status": "disabled"},
    "clickhouse": {"status": "disabled"},
    "qdrant": {"status": "disabled"}
  }
}
```

Object Storage unavailable means proof packet downloads, evidence exports, release artifacts, and backup evidence workflows may be degraded. PostgreSQL remains artifact metadata truth. Redis remains ephemeral and must not be treated as durable truth.

## Backup and restore implications

Object Storage must be included in backup/restore planning. Operators should collect or generate storage evidence artifacts for:

- PostgreSQL backup evidence;
- PostgreSQL restore evidence;
- Object Storage integrity evidence;
- storage outbox replay evidence;
- storage health evidence.

See `docs/STORAGE_BACKUP_RECOVERY.md` for evidence artifact expectations.

## Security boundaries

Object Storage must never contain:

- Bitcoin seed phrases;
- Bitcoin private keys;
- wallet files;
- `xprv`, `yprv`, or `zprv`;
- raw Access Pass bearer tokens;
- raw API secrets;
- unredacted sensitive material.

Allowed contents include proof packets, evidence archives, signed reports, release artifacts, backup evidence, SBOM/provenance artifacts, and redacted exports.

## Degraded mode behavior

- PostgreSQL down: critical operations unavailable.
- Redis down: cache/rate-limit/fanout/queue behavior degraded; durable truth remains outside Redis.
- Object Storage down: artifact upload/download/export workflows degraded; metadata can remain queryable in PostgreSQL.
- TimescaleDB, ClickHouse, and Qdrant disabled: expected foundation state until later prompts implement those engines.
