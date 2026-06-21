import pytest
from pydantic import ValidationError

from app.schemas.storage_artifact import StorageArtifactCreate


def _artifact_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "artifact_type": "proof_packet",
        "domain": "evidence",
        "object_uri": "s3://bastion-evidence/proof/packet.json",
        "bucket": "bastion-evidence",
        "object_key": "proof/packet.json",
        "sha256_hash": "a" * 64,
        "size_bytes": 128,
        "content_type": "application/json",
        "created_by_hash": "actor_hash_123",
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize("field", ["artifact_type", "object_uri", "sha256_hash", "content_type"])
def test_required_artifact_fields_are_validated(field: str) -> None:
    payload = _artifact_payload()
    payload.pop(field)

    if field == "artifact_type":
        artifact = StorageArtifactCreate(**payload)
        assert artifact.artifact_type == "generic"
    else:
        with pytest.raises(ValidationError):
            StorageArtifactCreate(**payload)


def test_sha256_hash_must_be_lowercase_hex() -> None:
    with pytest.raises(ValidationError, match="sha256_hash"):
        StorageArtifactCreate(**_artifact_payload(sha256_hash="A" * 64))


def test_size_bytes_must_be_non_negative() -> None:
    with pytest.raises(ValidationError):
        StorageArtifactCreate(**_artifact_payload(size_bytes=-1))


def test_retention_policy_is_explicit_and_defaults_safely() -> None:
    artifact = StorageArtifactCreate(**_artifact_payload())

    assert artifact.retention_policy == "standard"
    assert artifact.access_policy_json == {}
    assert "public" not in artifact.access_policy_json


def test_created_by_hash_uses_fingerprint_style_identifier() -> None:
    artifact = StorageArtifactCreate(**_artifact_payload(created_by_hash="sha256_actor_abc123"))

    assert artifact.created_by_hash == "sha256_actor_abc123"
    assert "@" not in artifact.created_by_hash


def test_artifact_metadata_rejects_sensitive_material() -> None:
    with pytest.raises(ValidationError, match="forbidden sensitive material"):
        StorageArtifactCreate(
            **_artifact_payload(metadata_json={"operator_note": "contains xprv material"})
        )
