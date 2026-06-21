import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.storage_artifact import StorageArtifact
from app.schemas.storage_artifact import StorageArtifactCreate


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine, tables=[StorageArtifact.__table__])
    return Session(engine)


def _payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "artifact_type": "proof_packet",
        "artifact_subtype": "json",
        "domain": "evidence",
        "object_uri": "s3://bastion-evidence/proof/packet.json",
        "bucket": "bastion-evidence",
        "object_key": "proof/packet.json",
        "sha256_hash": "a" * 64,
        "size_bytes": 128,
        "content_type": "application/json",
        "metadata_json": {"schema_version": 1},
        "access_policy_json": {"roles": ["admin"]},
    }
    payload.update(overrides)
    return payload


def test_storage_artifact_model_creation() -> None:
    with _session() as db:
        artifact = StorageArtifact(artifact_id="art_test", **_payload())
        db.add(artifact)
        db.commit()
        db.refresh(artifact)

        assert artifact.id is not None
        assert artifact.artifact_id == "art_test"
        assert artifact.sha256_hash == "a" * 64
        assert artifact.status == "available"
        assert artifact.access_policy_json == {"roles": ["admin"]}


def test_sha256_hash_validation() -> None:
    with pytest.raises(ValidationError, match="sha256_hash"):
        StorageArtifactCreate(**_payload(sha256_hash="not-a-hash"))

    with pytest.raises(ValidationError, match="sha256_hash"):
        StorageArtifactCreate(**_payload(sha256_hash="A" * 64))


def test_size_bytes_validation() -> None:
    with pytest.raises(ValidationError, match="size_bytes"):
        StorageArtifactCreate(**_payload(size_bytes=-1))


def test_sensitive_metadata_is_rejected() -> None:
    with pytest.raises(ValidationError, match="forbidden sensitive material"):
        StorageArtifactCreate(**_payload(metadata_json={"note": "private key export"}))
