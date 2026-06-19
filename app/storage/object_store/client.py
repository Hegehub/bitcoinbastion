"""Common Object Storage interface and shared helpers."""

from __future__ import annotations

import logging
import re
import time
from hashlib import sha256
from pathlib import PurePosixPath
from typing import Mapping, Protocol

from app.storage.constants import OBJECT_STORAGE
from app.storage.interfaces import StorageHealthResult
from app.storage.object_store.checksums import validate_sha256
from app.storage.object_store.errors import ObjectStoreSecurityError, ObjectStoreSizeError
from app.storage.object_store.schemas import ObjectReadResult, ObjectStatResult, ObjectWriteRequest

logger = logging.getLogger(__name__)

FORBIDDEN_OBJECT_STORE_TERMS = (
    "seed phrase",
    "private key",
    "xprv",
    "yprv",
    "zprv",
    "wallet.dat",
    "mnemonic",
    "recovery phrase",
)


class ObjectStore(Protocol):
    backend: str

    def put_object(self, request: ObjectWriteRequest) -> ObjectStatResult: ...

    def get_object(self, bucket: str, object_key: str) -> ObjectReadResult: ...

    def delete_object(self, bucket: str, object_key: str) -> None: ...

    def object_exists(self, bucket: str, object_key: str) -> bool: ...

    def stat_object(self, bucket: str, object_key: str) -> ObjectStatResult: ...

    def generate_presigned_get_url(
        self, bucket: str, object_key: str, expires_seconds: int
    ) -> str: ...


def object_key_hash(object_key: str) -> str:
    return sha256(object_key.encode("utf-8")).hexdigest()[:16]


def normalize_object_key(object_key: str) -> str:
    candidate = object_key.strip()
    if not candidate:
        raise ObjectStoreSecurityError("Object key must not be empty.")
    if candidate.startswith(("/", "\\")):
        raise ObjectStoreSecurityError("Object key must not be an absolute path.")
    if "\x00" in candidate:
        raise ObjectStoreSecurityError("Object key contains an invalid character.")
    normalized = PurePosixPath(candidate.replace("\\", "/"))
    if normalized.is_absolute() or any(part in {"", ".", ".."} for part in normalized.parts):
        raise ObjectStoreSecurityError("Object key must not contain path traversal segments.")
    safe_key = normalized.as_posix()
    _guard_sensitive_text("object key", safe_key)
    return safe_key


def validate_bucket_name(bucket: str) -> str:
    candidate = bucket.strip()
    if not candidate:
        raise ObjectStoreSecurityError("Bucket must not be empty.")
    if "/" in candidate or "\\" in candidate or candidate in {".", ".."}:
        raise ObjectStoreSecurityError("Bucket must be a simple storage bucket name.")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{1,253}", candidate):
        raise ObjectStoreSecurityError("Bucket contains unsupported characters.")
    return candidate


def validate_metadata(metadata: Mapping[str, str]) -> dict[str, str]:
    safe_metadata: dict[str, str] = {}
    for key, value in metadata.items():
        safe_key = str(key).strip()
        safe_value = str(value).strip()
        if not safe_key:
            raise ObjectStoreSecurityError("Metadata keys must not be empty.")
        _guard_sensitive_text("metadata", safe_key)
        _guard_sensitive_text("metadata", safe_value)
        safe_metadata[safe_key] = safe_value
    return safe_metadata


def validate_write_request(
    request: ObjectWriteRequest, max_object_bytes: int
) -> tuple[str, str, dict[str, str]]:
    bucket = validate_bucket_name(request.bucket)
    object_key = normalize_object_key(request.object_key)
    metadata = validate_metadata(request.metadata)
    size_bytes = request.size_bytes if request.size_bytes is not None else len(request.content)
    if size_bytes != len(request.content):
        raise ObjectStoreSizeError("Object size does not match provided content length.")
    if size_bytes > max_object_bytes:
        raise ObjectStoreSizeError("Object exceeds configured maximum size.")
    if request.content_type == "application/octet-stream" and "artifact_type" not in metadata:
        raise ObjectStoreSecurityError("Binary objects require explicit artifact_type metadata.")
    actual_sha256 = sha256(request.content).hexdigest()
    validate_sha256(actual_sha256, request.sha256 or actual_sha256)
    return bucket, object_key, metadata


def log_object_store_operation(
    *,
    backend: str,
    bucket: str,
    operation: str,
    object_key: str,
    status: str,
    started_at: float,
) -> None:
    logger.info(
        "object_store_operation",
        extra={
            "backend": backend,
            "bucket": bucket,
            "operation": operation,
            "object_key_hash": object_key_hash(object_key),
            "status": status,
            "latency_ms": round((time.monotonic() - started_at) * 1000, 3),
        },
    )


class DisabledObjectStore:
    backend = "disabled"

    def put_object(self, request: ObjectWriteRequest) -> ObjectStatResult:
        raise ObjectStoreSecurityError("Object Storage is disabled.")

    def get_object(self, bucket: str, object_key: str) -> ObjectReadResult:
        raise ObjectStoreSecurityError("Object Storage is disabled.")

    def delete_object(self, bucket: str, object_key: str) -> None:
        raise ObjectStoreSecurityError("Object Storage is disabled.")

    def object_exists(self, bucket: str, object_key: str) -> bool:
        return False

    def stat_object(self, bucket: str, object_key: str) -> ObjectStatResult:
        raise ObjectStoreSecurityError("Object Storage is disabled.")

    def generate_presigned_get_url(self, bucket: str, object_key: str, expires_seconds: int) -> str:
        raise ObjectStoreSecurityError("Object Storage is disabled.")


class ObjectStoreHealthCheck:
    name = OBJECT_STORAGE

    def __init__(self, store: ObjectStore, bucket: str, enabled: bool) -> None:
        self.store = store
        self.bucket = bucket
        self.enabled = enabled

    async def check_health(self) -> StorageHealthResult:
        started_at = time.monotonic()
        if not self.enabled:
            return StorageHealthResult(
                name=self.name,
                status="disabled",
                enabled=False,
                degraded=False,
                latency_ms=0.0,
                message="Object Storage is disabled.",
            )

        test_key = f"_healthcheck/{time.time_ns()}.txt"
        content = b"bitcoin-bastion-object-store-healthcheck"
        try:
            stat = self.store.put_object(
                ObjectWriteRequest(
                    bucket=self.bucket,
                    object_key=test_key,
                    content=content,
                    content_type="text/plain",
                    metadata={"artifact_type": "healthcheck"},
                )
            )
            read_result = self.store.get_object(self.bucket, test_key)
            validate_sha256(read_result.metadata.sha256, stat.sha256)
            self.store.delete_object(self.bucket, test_key)
        except (
            Exception
        ) as exc:  # noqa: BLE001 - health probe returns degraded state instead of raising.
            return StorageHealthResult(
                name=self.name,
                status="unavailable",
                enabled=True,
                degraded=True,
                latency_ms=round((time.monotonic() - started_at) * 1000, 3),
                message=f"Object Storage health check failed: {type(exc).__name__}",
            )

        return StorageHealthResult(
            name=self.name,
            status="ok",
            enabled=True,
            degraded=False,
            latency_ms=round((time.monotonic() - started_at) * 1000, 3),
            message="Object Storage health check succeeded.",
        )


def _guard_sensitive_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in FORBIDDEN_OBJECT_STORE_TERMS):
        raise ObjectStoreSecurityError(
            f"Object Storage {label} contains forbidden sensitive material."
        )
