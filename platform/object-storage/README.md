# Object storage

Owns S3-compatible artifact storage, MinIO/S3 configuration, evidence pack persistence, retention policy and storage health checks.

Current canonical paths:

- `app/api/v1/storage_status.py`
- `artifacts/`
- object-storage settings in `.env.example` and deployment manifests

Migration rule: object storage is for artifacts and evidence, not for secret material or custody-related keys.
