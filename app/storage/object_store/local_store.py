"""Filesystem-backed Object Storage implementation for development and tests."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from app.storage.object_store.checksums import sha256_bytes, sha256_file, validate_sha256
from app.storage.object_store.client import (
    log_object_store_operation,
    normalize_object_key,
    validate_bucket_name,
    validate_metadata,
    validate_write_request,
)
from app.storage.object_store.errors import ObjectStoreNotFoundError, ObjectStoreSecurityError
from app.storage.object_store.schemas import (
    ObjectReadResult,
    ObjectRetentionClass,
    ObjectStatResult,
    ObjectStoreMetadata,
    ObjectWriteRequest,
)


class LocalObjectStore:
    backend = "local"

    def __init__(
        self, root: Path | str = Path(".storage/objects"), max_object_bytes: int = 100 * 1024 * 1024
    ) -> None:
        self.root = Path(root).resolve()
        self.max_object_bytes = max_object_bytes
        self.root.mkdir(parents=True, exist_ok=True)

    def put_object(self, request: ObjectWriteRequest) -> ObjectStatResult:
        started_at = time.monotonic()
        bucket, object_key, metadata = validate_write_request(request, self.max_object_bytes)
        object_path = self._object_path(bucket, object_key)
        metadata_path = self._metadata_path(bucket, object_key)
        object_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)

        sha256 = sha256_bytes(request.content)
        stat = ObjectStatResult(
            bucket=bucket,
            object_key=object_key,
            content_type=request.content_type,
            sha256=sha256,
            size_bytes=len(request.content),
            retention_class=request.retention_class,
            created_at=datetime.now(timezone.utc),
            metadata=metadata,
        )
        tmp_path = object_path.with_name(f".{object_path.name}.tmp")
        tmp_path.write_bytes(request.content)
        validate_sha256(sha256_file(tmp_path), sha256)
        tmp_path.replace(object_path)
        self._write_metadata(metadata_path, stat)
        log_object_store_operation(
            backend=self.backend,
            bucket=bucket,
            operation="put_object",
            object_key=object_key,
            status="ok",
            started_at=started_at,
        )
        return stat

    def get_object(self, bucket: str, object_key: str) -> ObjectReadResult:
        started_at = time.monotonic()
        bucket, object_key = self._safe_bucket_and_key(bucket, object_key)
        object_path = self._object_path(bucket, object_key)
        if not object_path.exists():
            raise ObjectStoreNotFoundError("Object not found.")
        stat = self.stat_object(bucket, object_key)
        content = object_path.read_bytes()
        validate_sha256(sha256_bytes(content), stat.sha256)
        metadata = ObjectStoreMetadata(
            bucket=bucket,
            object_key=object_key,
            content_type=stat.content_type,
            sha256=stat.sha256,
            size_bytes=stat.size_bytes,
            retention_class=stat.retention_class,
            created_at=stat.created_at,
            metadata=stat.metadata,
        )
        log_object_store_operation(
            backend=self.backend,
            bucket=bucket,
            operation="get_object",
            object_key=object_key,
            status="ok",
            started_at=started_at,
        )
        return ObjectReadResult(
            bucket=bucket,
            object_key=object_key,
            content=content,
            content_type=stat.content_type,
            metadata=metadata,
        )

    def delete_object(self, bucket: str, object_key: str) -> None:
        started_at = time.monotonic()
        bucket, object_key = self._safe_bucket_and_key(bucket, object_key)
        object_path = self._object_path(bucket, object_key)
        metadata_path = self._metadata_path(bucket, object_key)
        if object_path.exists():
            object_path.unlink()
        if metadata_path.exists():
            metadata_path.unlink()
        log_object_store_operation(
            backend=self.backend,
            bucket=bucket,
            operation="delete_object",
            object_key=object_key,
            status="ok",
            started_at=started_at,
        )

    def object_exists(self, bucket: str, object_key: str) -> bool:
        bucket, object_key = self._safe_bucket_and_key(bucket, object_key)
        return self._object_path(bucket, object_key).exists()

    def stat_object(self, bucket: str, object_key: str) -> ObjectStatResult:
        bucket, object_key = self._safe_bucket_and_key(bucket, object_key)
        object_path = self._object_path(bucket, object_key)
        metadata_path = self._metadata_path(bucket, object_key)
        if not object_path.exists() or not metadata_path.exists():
            raise ObjectStoreNotFoundError("Object not found.")
        stat = self._read_metadata(metadata_path)
        actual_sha256 = sha256_file(object_path)
        validate_sha256(actual_sha256, stat.sha256)
        if object_path.stat().st_size != stat.size_bytes:
            raise ObjectStoreSecurityError("Object size does not match stored metadata.")
        return stat

    def generate_presigned_get_url(self, bucket: str, object_key: str, expires_seconds: int) -> str:
        bucket, object_key = self._safe_bucket_and_key(bucket, object_key)
        if expires_seconds <= 0:
            raise ObjectStoreSecurityError("Presigned URL expiry must be positive.")
        return f"local://{bucket}/{object_key}?expires_seconds={expires_seconds}"

    def _safe_bucket_and_key(self, bucket: str, object_key: str) -> tuple[str, str]:
        return validate_bucket_name(bucket), normalize_object_key(object_key)

    def _object_path(self, bucket: str, object_key: str) -> Path:
        path = (self.root / bucket / object_key).resolve()
        self._ensure_under_root(path)
        return path

    def _metadata_path(self, bucket: str, object_key: str) -> Path:
        path = (self.root / bucket / f"{object_key}.metadata.json").resolve()
        self._ensure_under_root(path)
        return path

    def _ensure_under_root(self, path: Path) -> None:
        if path != self.root and self.root not in path.parents:
            raise ObjectStoreSecurityError("Object path escapes configured local root.")

    def _write_metadata(self, path: Path, stat: ObjectStatResult) -> None:
        payload = {
            "bucket": stat.bucket,
            "object_key": stat.object_key,
            "content_type": stat.content_type,
            "sha256": stat.sha256,
            "size_bytes": stat.size_bytes,
            "retention_class": stat.retention_class.value,
            "created_at": stat.created_at.isoformat(),
            "metadata": dict(stat.metadata),
        }
        path.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")

    def _read_metadata(self, path: Path) -> ObjectStatResult:
        payload = json.loads(path.read_text(encoding="utf-8"))
        metadata = validate_metadata(payload.get("metadata", {}))
        return ObjectStatResult(
            bucket=validate_bucket_name(payload["bucket"]),
            object_key=normalize_object_key(payload["object_key"]),
            content_type=str(payload["content_type"]),
            sha256=str(payload["sha256"]),
            size_bytes=int(payload["size_bytes"]),
            retention_class=ObjectRetentionClass(str(payload["retention_class"])),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
            metadata=metadata,
        )
