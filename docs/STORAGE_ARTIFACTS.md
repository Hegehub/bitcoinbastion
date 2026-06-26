# Storage Artifacts

## Purpose

`StorageArtifact` is the generic PostgreSQL metadata primitive for files stored outside the relational database. It is intended for proof packets, trace report exports, evidence archives, release evidence, migration evidence, backup/restore evidence, SBOM/provenance files, signed receipts, audit exports, and enterprise evidence bundles.

PostgreSQL stores canonical artifact metadata. Object Storage / MinIO / S3 stores artifact blobs. SHA-256 links the metadata record to the exact stored content.

## Data model

The `storage_artifacts` table records:

- stable `artifact_id`;
- `artifact_type`, optional `artifact_subtype`, and owning `domain`;
- `object_uri`, `bucket`, and `object_key` for Object Storage lookup;
- required `sha256_hash`, `size_bytes`, and `content_type`;
- optional compression, encryption, signature, retention, redaction, access policy, and domain metadata;
- privacy-preserving `created_by_hash` instead of raw user identifiers;
- lifecycle timestamps and status.

Large artifact bytes must not be stored as SQL blobs in this table.

## Artifact lifecycle

Normal path:

```text
pending
→ available
→ deleted
```

Alternative paths:

```text
pending → failed
available → quarantined
quarantined → deleted
```

`deleted` is metadata lifecycle state in this prompt. Physical Object Storage deletion is deferred until a future retention/deletion policy prompt.

## Security rules

Artifact metadata and access policy fields must not contain seed phrases, private keys, xprv/yprv/zprv material, wallet files, mnemonics, raw passwords, raw API secrets, raw emails, raw wallet identifiers, or raw Access Pass bearer tokens.

Allowed actor references should be hashes, fingerprints, signed metadata, or other non-custodial references.

## Retention policy

Initial retention policy values are:

- `ephemeral`
- `standard`
- `evidence`
- `compliance`
- `worm`
- `enterprise_custom`

Retention metadata is recorded now, but WORM enforcement and physical deletion workflows are future work.

## Examples

```json
{
  "artifact_type": "trace_report_export",
  "artifact_subtype": "json",
  "domain": "trace",
  "object_uri": "s3://bitcoin-bastion-evidence/trace/reports/trace_123.json",
  "bucket": "bitcoin-bastion-evidence",
  "object_key": "trace/reports/trace_123.json",
  "sha256_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "size_bytes": 4096,
  "content_type": "application/json",
  "metadata_json": {"report_id": "trace_123", "schema_version": 1}
}
```

## Future work

- Wire proof packet and evidence archive generation to Object Storage.
- Persist object upload events into the future audit/event layer.
- Add retention enforcement and safe physical deletion workflows.
- Add authorization-aware metadata API endpoints.
- Add signature verification and crypto-agility workflows.
