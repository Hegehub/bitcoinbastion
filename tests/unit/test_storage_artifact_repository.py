from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.storage_artifact import StorageArtifact
from app.db.repositories.storage_artifact_repository import StorageArtifactRepository


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine, tables=[StorageArtifact.__table__])
    return Session(engine)


def _artifact(artifact_id: str = "art_repo", domain: str = "evidence") -> StorageArtifact:
    return StorageArtifact(
        artifact_id=artifact_id,
        artifact_type="proof_packet",
        artifact_subtype="json",
        domain=domain,
        object_uri=f"s3://bastion-evidence/proof/{artifact_id}.json",
        bucket="bastion-evidence",
        object_key=f"proof/{artifact_id}.json",
        sha256_hash="b" * 64,
        size_bytes=256,
        content_type="application/json",
        metadata_json={"schema_version": 1},
        access_policy_json={"roles": ["admin"]},
    )


def test_repository_create_get_and_list() -> None:
    with _session() as db:
        repo = StorageArtifactRepository(db)
        artifact = repo.create(_artifact())

        assert repo.get_by_id(artifact.id).artifact_id == artifact.artifact_id
        assert repo.get_by_artifact_id(artifact.artifact_id).id == artifact.id
        assert repo.get_by_sha256_hash(artifact.sha256_hash)[0].id == artifact.id
        assert repo.get_by_bucket_key(artifact.bucket, artifact.object_key).id == artifact.id
        assert repo.list_by_domain("evidence")[0].id == artifact.id
        assert repo.list_by_type("proof_packet")[0].id == artifact.id


def test_repository_mark_deleted_and_quarantined() -> None:
    with _session() as db:
        repo = StorageArtifactRepository(db)
        artifact = repo.create(_artifact())

        quarantined = repo.mark_quarantined(artifact.artifact_id)
        assert quarantined.status == "quarantined"

        deleted = repo.mark_deleted(artifact.artifact_id)
        assert deleted.status == "deleted"
        assert deleted.deleted_at is not None
