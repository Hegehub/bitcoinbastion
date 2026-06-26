"""Object Storage abstractions and local/optional MinIO backends."""

from app.storage.object_store.checksums import sha256_bytes, sha256_file, validate_sha256
from app.storage.object_store.client import DisabledObjectStore, ObjectStore, ObjectStoreHealthCheck
from app.storage.object_store.local_store import LocalObjectStore
from app.storage.object_store.minio_store import MinIOObjectStore
from app.storage.object_store.schemas import (
    ObjectReadResult,
    ObjectRetentionClass,
    ObjectStatResult,
    ObjectStoreConfig,
    ObjectStoreMetadata,
    ObjectWriteRequest,
)

__all__ = [
    "DisabledObjectStore",
    "LocalObjectStore",
    "MinIOObjectStore",
    "ObjectReadResult",
    "ObjectRetentionClass",
    "ObjectStatResult",
    "ObjectStore",
    "ObjectStoreConfig",
    "ObjectStoreHealthCheck",
    "ObjectStoreMetadata",
    "ObjectWriteRequest",
    "sha256_bytes",
    "sha256_file",
    "validate_sha256",
]
