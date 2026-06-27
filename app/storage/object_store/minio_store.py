"""Optional MinIO/S3-compatible Object Storage adapter.

The repository does not require a MinIO/S3 dependency for the default test suite.
This adapter imports `minio` lazily and raises a safe configuration error when the
optional dependency is not installed.
"""

from io import BytesIO
from time import monotonic
from urllib.parse import urlparse

from app.storage.object_store.checksums import sha256_bytes, validate_sha256
from app.storage.object_store.client import (
    log_object_store_operation,
    normalize_object_key,
    validate_bucket_name,
    validate_metadata,
    validate_write_request,
)
from app.storage.object_store.errors import ObjectStoreConfigurationError, ObjectStoreNotFoundError
from app.storage.object_store.schemas import (
    ObjectReadResult,
    ObjectStatResult,
    ObjectStoreMetadata,
    ObjectWriteRequest,
)


class MinIOObjectStore:
    backend = "minio"

    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = True,
        region: str | None = None,
        max_object_bytes: int = 100 * 1024 * 1024,
    ) -> None:
        try:
            from minio import Minio  # type: ignore[import-not-found]
            from minio.error import S3Error  # type: ignore[import-not-found]
        except ImportError as exc:
            raise ObjectStoreConfigurationError(
                "MinIO Object Storage backend requires the optional 'minio' package."
            ) from exc

        if not endpoint.strip() or not access_key.strip() or not secret_key.strip():
            raise ObjectStoreConfigurationError(
                "MinIO endpoint and credentials must be configured."
            )
        parsed_endpoint = urlparse(endpoint if "://" in endpoint else f"//{endpoint}")
        self.endpoint = parsed_endpoint.netloc or parsed_endpoint.path
        self.bucket = validate_bucket_name(bucket)
        self.max_object_bytes = max_object_bytes
        self._s3_error = S3Error
        self._client = Minio(
            self.endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            region=region,
        )

    def put_object(self, request: ObjectWriteRequest) -> ObjectStatResult:
        started_at = monotonic()
        bucket, object_key, metadata = validate_write_request(request, self.max_object_bytes)
        checksum = sha256_bytes(request.content)
        headers = {
            "x-amz-meta-sha256": checksum,
            "x-amz-meta-retention-class": request.retention_class.value,
            **{f"x-amz-meta-bastion-{key}": value for key, value in metadata.items()},
        }
        self._client.put_object(
            bucket,
            object_key,
            BytesIO(request.content),
            length=len(request.content),
            content_type=request.content_type,
            metadata=headers,
        )
        log_object_store_operation(
            backend=self.backend,
            bucket=bucket,
            operation="put_object",
            object_key=object_key,
            status="ok",
            started_at=started_at,
        )
        return ObjectStatResult(
            bucket=bucket,
            object_key=object_key,
            content_type=request.content_type,
            sha256=checksum,
            size_bytes=len(request.content),
            retention_class=request.retention_class,
            created_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            metadata=metadata,
        )

    def get_object(self, bucket: str, object_key: str) -> ObjectReadResult:
        bucket, object_key = validate_bucket_name(bucket), normalize_object_key(object_key)
        try:
            response = self._client.get_object(bucket, object_key)
            content = response.read()
            response.close()
            response.release_conn()
        except self._s3_error as exc:
            raise ObjectStoreNotFoundError("Object not found.") from exc
        stat = self.stat_object(bucket, object_key)
        validate_sha256(sha256_bytes(content), stat.sha256)
        return ObjectReadResult(
            bucket=bucket,
            object_key=object_key,
            content=content,
            content_type=stat.content_type,
            metadata=ObjectStoreMetadata(
                bucket=bucket,
                object_key=object_key,
                content_type=stat.content_type,
                sha256=stat.sha256,
                size_bytes=stat.size_bytes,
                retention_class=stat.retention_class,
                created_at=stat.created_at,
                metadata=stat.metadata,
            ),
        )

    def delete_object(self, bucket: str, object_key: str) -> None:
        self._client.remove_object(validate_bucket_name(bucket), normalize_object_key(object_key))

    def object_exists(self, bucket: str, object_key: str) -> bool:
        try:
            self.stat_object(bucket, object_key)
            return True
        except ObjectStoreNotFoundError:
            return False

    def stat_object(self, bucket: str, object_key: str) -> ObjectStatResult:
        bucket, object_key = validate_bucket_name(bucket), normalize_object_key(object_key)
        try:
            stat = self._client.stat_object(bucket, object_key)
        except self._s3_error as exc:
            raise ObjectStoreNotFoundError("Object not found.") from exc
        metadata = validate_metadata(getattr(stat, "metadata", {}) or {})
        checksum = metadata.get("x-amz-meta-sha256") or metadata.get("sha256")
        if not checksum:
            raise ObjectStoreConfigurationError("Stored object is missing SHA-256 metadata.")
        from app.storage.object_store.schemas import ObjectRetentionClass

        retention = metadata.get("x-amz-meta-retention-class", ObjectRetentionClass.STANDARD.value)
        return ObjectStatResult(
            bucket=bucket,
            object_key=object_key,
            content_type=getattr(stat, "content_type", "application/octet-stream"),
            sha256=checksum,
            size_bytes=int(getattr(stat, "size", 0)),
            retention_class=ObjectRetentionClass(retention),
            created_at=getattr(stat, "last_modified", None)
            or __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            metadata=metadata,
        )

    def generate_presigned_get_url(self, bucket: str, object_key: str, expires_seconds: int) -> str:
        from datetime import timedelta

        if expires_seconds <= 0:
            raise ObjectStoreConfigurationError("Presigned URL expiry must be positive.")
        return self._client.presigned_get_object(
            validate_bucket_name(bucket),
            normalize_object_key(object_key),
            expires=timedelta(seconds=expires_seconds),
        )
