import json

import pytest
from pydantic import ValidationError

from app.schemas.storage_artifact import StorageArtifactCreate
from app.storage.evidence.models import EvidenceStatus, StorageEvidence, StorageEvidenceType
from app.storage.evidence.writer import REDACTED, redact_evidence_value, write_evidence_json
from app.storage.object_store.client import validate_metadata
from app.storage.object_store.errors import ObjectStoreSecurityError
from app.storage.outbox.schemas import StorageOutboxEventCreate
from app.storage.redis_boundaries import build_redis_key, validate_redis_purpose
from app.storage.errors import StorageSafetyError

FORBIDDEN_PATTERNS = [
    "seed phrase",
    "mnemonic",
    "private key",
    "wallet.dat",
    "xprv",
    "yprv",
    "zprv",
]


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
    }
    payload.update(overrides)
    return payload


def test_evidence_redacts_sensitive_looking_strings(tmp_path) -> None:
    evidence = StorageEvidence(
        evidence_type=StorageEvidenceType.STORAGE_HEALTH,
        status=EvidenceStatus.FAIL,
        metadata={
            "safe": "ok",
            "api_token": "token-value",
            "operator_note": "contains private key material",
        },
    )
    write_evidence_json(evidence, "storage_health_evidence.json", tmp_path)
    rendered = (tmp_path / "storage_health_evidence.json").read_text(encoding="utf-8")

    assert "token-value" not in rendered
    assert "private key" not in rendered
    assert REDACTED in rendered


@pytest.mark.parametrize("value", FORBIDDEN_PATTERNS)
def test_redaction_helper_masks_forbidden_values(value: str) -> None:
    assert redact_evidence_value({"note": value})["note"] == REDACTED


def test_object_metadata_rejects_raw_secrets() -> None:
    with pytest.raises(ObjectStoreSecurityError):
        validate_metadata({"operator_note": "contains seed phrase material"})


def test_storage_artifact_schema_rejects_sensitive_metadata() -> None:
    with pytest.raises(ValidationError):
        StorageArtifactCreate(**_artifact_payload(metadata_json={"note": "wallet.dat backup"}))


def test_outbox_schema_rejects_sensitive_payloads() -> None:
    with pytest.raises(ValidationError):
        StorageOutboxEventCreate(
            event_type="storage.secret.detected",
            aggregate_type="storage_test",
            aggregate_id="agg_1",
            payload_json={"note": "raw secret value"},
            target_stores=["audit"],
        )


def test_redis_boundaries_reject_durable_truth_and_sensitive_key_parts() -> None:
    with pytest.raises(StorageSafetyError):
        validate_redis_purpose("access_certificates")
    with pytest.raises(StorageSafetyError):
        build_redis_key("test", "cache", "xprv_material")


def test_evidence_output_json_contains_no_raw_secret_values(tmp_path) -> None:
    evidence = StorageEvidence(
        evidence_type=StorageEvidenceType.OBJECT_STORAGE_INTEGRITY,
        status=EvidenceStatus.FAIL,
        metadata={"secret_key": "object-store-secret", "safe": "checksum_failed"},
    )
    write_evidence_json(evidence, "object_storage_integrity_evidence.json", tmp_path)

    payload = json.loads((tmp_path / "object_storage_integrity_evidence.json").read_text())
    assert payload["metadata"]["secret_key"] == REDACTED
    assert payload["metadata"]["safe"] == "checksum_failed"
