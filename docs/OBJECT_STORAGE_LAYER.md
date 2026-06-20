# Object Storage Layer

## Purpose

The Bitcoin Bastion Object Storage layer provides an infrastructure boundary for large immutable or semi-immutable artifacts such as proof packets, trace report exports, evidence archives, release artifacts, signed receipts, backup/restore evidence, deployment evidence, and future Access Layer recovery/audit packets.

Object Storage stores artifact bytes. PostgreSQL remains the canonical metadata and authorization store for object keys, checksums, signatures, retention state, lifecycle state, and access policy. Object Storage must not become authorization truth.

## Supported backends

- `disabled`: explicit unavailable mode.
- `local`: filesystem-backed development and test backend rooted under `.storage/objects/` by default.
- `minio`: optional S3-compatible backend using the `minio` Python package when installed.
- `s3`: reserved for future S3-compatible integration; it should follow the same checksum and safety rules.

The default automated tests use `LocalObjectStore` and do not require a real MinIO server.

## Local development mode

`LocalObjectStore` writes objects under the configured local root and stores sidecar metadata JSON files. It prevents path traversal, rejects absolute object keys, validates bucket names, computes SHA-256 checksums, and verifies stored bytes on read/stat operations.

Recommended development settings:

```env
OBJECT_STORAGE_ENABLED=true
OBJECT_STORAGE_BACKEND=local
OBJECT_STORAGE_BUCKET=bastion-local-artifacts
OBJECT_STORAGE_LOCAL_ROOT=.storage/objects
OBJECT_STORAGE_CHECKSUM_REQUIRED=true
```

## MinIO / S3 production mode

`MinIOObjectStore` is an optional adapter. It imports the MinIO client lazily so the repository does not require a MinIO/S3 dependency or server for normal unit tests. Production-style deployments should provide endpoint, bucket, access key, secret key, secure/http setting, and optional region through environment variables or secret management.

Secrets must not be logged, exposed to frontend code, embedded in presigned URL logs, or included in exception messages.

## Checksum requirement

Every stored object must have a SHA-256 checksum. The layer computes checksums on write and validates checksums on read/stat for the local backend. Checksum mismatch raises a typed `ObjectStoreChecksumError`; corrupted objects must not be silently accepted.

## Security restrictions

The Object Storage layer rejects or protects against:

- empty object keys;
- path traversal;
- absolute local paths as object keys;
- obvious sensitive material in object keys or metadata, including seed phrase, private key, xprv, yprv, zprv, wallet.dat, mnemonic, and recovery phrase;
- binary `application/octet-stream` writes without explicit `artifact_type` metadata;
- objects larger than the configured maximum size.

Do not store seed phrases, Bitcoin private keys, wallet files, xprv/yprv/zprv material, raw secrets, raw Access Pass bearer tokens, or custody material in Object Storage.

## Health checks

`ObjectStoreHealthCheck` verifies configuration and backend behavior by writing, reading, validating, and deleting a namespaced health-check object under `_healthcheck/`. Disabled backends return `disabled` cleanly. Health checks must not use raw credentials in logs or messages.

## Future integration

Later prompts may connect this layer to proof packets, trace reports, evidence archives, release artifacts, backup/restore evidence, and Access Layer recovery/audit packets. Those integrations must store canonical metadata in PostgreSQL and use Object Storage only for artifact bytes.
