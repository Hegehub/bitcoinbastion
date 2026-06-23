from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import pytest
from pydantic import ValidationError

from app.db.base import Base
from app.db.models.storage_artifact import StorageArtifact
from app.db.repositories.storage_artifact_repository import StorageArtifactRepository
from app.schemas.storage_artifact import StorageArtifactCreate
from app.services.storage_artifacts import StorageArtifactService
from app.storage.object_store.schemas import ObjectRetentionClass, ObjectStatResult
from app.db.models.time_utils import utcnow


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine, tables=[StorageArtifact.__table__])
    return Session(engine)


def _payload(**overrides: object) -> StorageArtifactCreate:
    payload: dict[str, object] = {
        "artifact_type": "trace_report_export",
        "artifact_subtype": "json",
        "domain": "trace",
        "object_uri": "s3://bastion-evidence/trace/report.json",
        "bucket": "bastion-evidence",
        "object_key": "trace/report.json",
        "sha256_hash": "c" * 64,
        "size_bytes": 512,
        "content_type": "application/json",
        "metadata_json": {"report_id": "trace_123"},
        "access_policy_json": {"roles": ["operator"]},
        "created_by_hash": "actor_hash_123",
    }
    payload.update(overrides)
    return StorageArtifactCreate(**payload)


def test_service_register_artifact() -> None:
    with _session() as db:
        service = StorageArtifactService(StorageArtifactRepository(db))
        artifact = service.register_artifact(_payload())

        assert artifact.artifact_id.startswith("art_")
        assert artifact.object_key == "trace/report.json"
        assert artifact.sha256_hash == "c" * 64
        assert not hasattr(artifact, "content")
        assert service.get_artifact(artifact.artifact_id).id == artifact.id
        assert service.find_by_hash(artifact.sha256_hash)[0].id == artifact.id


def test_service_register_uploaded_artifact_from_object_stat() -> None:
    with _session() as db:
        service = StorageArtifactService(StorageArtifactRepository(db))
        stat = ObjectStatResult(
            bucket="bastion-evidence",
            object_key="evidence/archive.tar.zst",
            content_type="application/zstd",
            sha256="d" * 64,
            size_bytes=1024,
            retention_class=ObjectRetentionClass.EVIDENCE,
            created_at=utcnow(),
            metadata={"artifact_type": "evidence_archive"},
        )

        artifact = service.register_uploaded_artifact(
            artifact_type="evidence_archive",
            domain="evidence",
            object_uri="s3://bastion-evidence/evidence/archive.tar.zst",
            stat=stat,
            artifact_subtype="tar_zst",
        )

        assert artifact.bucket == stat.bucket
        assert artifact.object_key == stat.object_key
        assert artifact.sha256_hash == stat.sha256
        assert artifact.size_bytes == stat.size_bytes


def test_service_mark_deleted_and_quarantined() -> None:
    with _session() as db:
        service = StorageArtifactService(StorageArtifactRepository(db))
        artifact = service.register_artifact(_payload())

        assert service.mark_artifact_quarantined(artifact.artifact_id).status == "quarantined"
        assert service.mark_artifact_deleted(artifact.artifact_id).status == "deleted"


def test_service_rejects_sensitive_metadata() -> None:
    with pytest.raises(ValidationError, match="forbidden sensitive material"):
        _payload(metadata_json={"note": "raw API secret"})
