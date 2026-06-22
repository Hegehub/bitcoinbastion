from pathlib import Path
from uuid import uuid4

from app.db.models.storage_artifact import StorageArtifact
from app.db.repositories.storage_artifact_repository import StorageArtifactRepository
from app.schemas.storage_artifact import (
    StorageArtifactCreate,
    StorageArtifactRead,
    validate_no_sensitive_material,
)
from app.storage.object_store.checksums import sha256_file
from app.storage.object_store.schemas import ObjectStatResult


class StorageArtifactServiceError(RuntimeError):
    pass


class StorageArtifactService:
    def __init__(self, repository: StorageArtifactRepository) -> None:
        self.repository = repository

    def register_artifact(self, payload: StorageArtifactCreate) -> StorageArtifact:
        self._validate_metadata_safety(payload)
        artifact_id = payload.artifact_id or self._new_artifact_id()
        artifact = StorageArtifact(
            artifact_id=artifact_id,
            artifact_type=payload.artifact_type,
            artifact_subtype=payload.artifact_subtype,
            domain=payload.domain,
            object_uri=payload.object_uri,
            bucket=payload.bucket,
            object_key=payload.object_key,
            sha256_hash=payload.sha256_hash,
            size_bytes=payload.size_bytes,
            content_type=payload.content_type,
            compression=payload.compression,
            encryption_status=payload.encryption_status,
            signature_alg=payload.signature_alg,
            signature_value=payload.signature_value,
            signature_key_id=payload.signature_key_id,
            retention_policy=payload.retention_policy,
            retention_until=payload.retention_until,
            legal_hold=payload.legal_hold,
            redaction_status=payload.redaction_status,
            access_policy_json=payload.access_policy_json,
            metadata_json=payload.metadata_json,
            created_by_hash=payload.created_by_hash,
            status=payload.status,
        )
        return self.repository.create(artifact)

    def register_uploaded_artifact(
        self,
        *,
        artifact_type: str,
        domain: str,
        object_uri: str,
        stat: ObjectStatResult,
        artifact_subtype: str | None = None,
        compression: str | None = None,
        encryption_status: str = "unknown",
        access_policy_json: dict[str, object] | None = None,
        metadata_json: dict[str, object] | None = None,
        created_by_hash: str | None = None,
    ) -> StorageArtifact:
        payload = StorageArtifactCreate(
            artifact_type=artifact_type,  # type: ignore[arg-type]
            artifact_subtype=artifact_subtype,
            domain=domain,  # type: ignore[arg-type]
            object_uri=object_uri,
            bucket=stat.bucket,
            object_key=stat.object_key,
            sha256_hash=stat.sha256,
            size_bytes=stat.size_bytes,
            content_type=stat.content_type,
            compression=compression,
            encryption_status=encryption_status,  # type: ignore[arg-type]
            retention_policy="standard",
            access_policy_json=access_policy_json or {},
            metadata_json={**dict(stat.metadata), **(metadata_json or {})},
            created_by_hash=created_by_hash,
            status="available",
        )
        return self.register_artifact(payload)

    def register_artifact_from_path(
        self,
        *,
        path: Path,
        payload: StorageArtifactCreate,
    ) -> StorageArtifact:
        if not path.is_file():
            raise StorageArtifactServiceError("artifact path must reference a file")
        actual_hash = sha256_file(path)
        if actual_hash != payload.sha256_hash:
            raise StorageArtifactServiceError("artifact file checksum does not match metadata")
        if path.stat().st_size != payload.size_bytes:
            raise StorageArtifactServiceError("artifact file size does not match metadata")
        return self.register_artifact(payload)

    def get_artifact(self, artifact_id: str) -> StorageArtifact | None:
        return self.repository.get_by_artifact_id(artifact_id)

    def find_by_hash(self, sha256_hash: str) -> list[StorageArtifact]:
        return self.repository.get_by_sha256_hash(sha256_hash)

    def list_artifacts(
        self,
        *,
        domain: str | None = None,
        artifact_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[StorageArtifact]:
        return self.repository.list_artifacts(
            domain=domain,
            artifact_type=artifact_type,
            status=status,
            limit=limit,
            offset=offset,
        )

    def mark_artifact_deleted(self, artifact_id: str) -> StorageArtifact:
        return self.repository.mark_deleted(artifact_id)

    def mark_artifact_quarantined(self, artifact_id: str) -> StorageArtifact:
        return self.repository.mark_quarantined(artifact_id)

    def to_read_schema(self, artifact: StorageArtifact) -> StorageArtifactRead:
        return StorageArtifactRead.model_validate(artifact)

    def _validate_metadata_safety(self, payload: StorageArtifactCreate) -> None:
        validate_no_sensitive_material(payload.access_policy_json, "access_policy_json")
        validate_no_sensitive_material(payload.metadata_json, "metadata_json")
        if payload.created_by_hash:
            validate_no_sensitive_material(payload.created_by_hash, "created_by_hash")

    def _new_artifact_id(self) -> str:
        return f"art_{uuid4().hex}"
