import json
from hashlib import sha256

import pytest

from app.storage.evidence.models import EvidenceStatus, StorageEvidence, StorageEvidenceType
from app.storage.evidence.writer import REDACTED, redact_evidence_value, write_evidence_json


def _evidence() -> StorageEvidence:
    return StorageEvidence(
        evidence_type=StorageEvidenceType.STORAGE_HEALTH,
        status=EvidenceStatus.WARN,
        environment="test",
        storage_profile="development",
        metadata={"safe": "value", "database_password": "do-not-write"},
    )


def test_json_evidence_writing_and_sha256(tmp_path) -> None:
    result = write_evidence_json(_evidence(), "storage_health_evidence.json", tmp_path)
    path = tmp_path / "storage_health_evidence.json"

    assert result.path == str(path)
    assert result.sha256 == sha256(path.read_bytes()).hexdigest()
    assert result.size_bytes == len(path.read_bytes())
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert list(payload.keys()) == sorted(payload.keys())


def test_secret_redaction_redacts_sensitive_keys_and_values() -> None:
    payload = redact_evidence_value(
        {
            "access_key": "abc",
            "nested": {"api_token": "token", "safe": "ok"},
            "value": "contains xprv material",
        }
    )

    assert payload["access_key"] == REDACTED
    assert payload["nested"]["api_token"] == REDACTED
    assert payload["nested"]["safe"] == "ok"
    assert payload["value"] == REDACTED


def test_writer_rejects_path_traversal_filename(tmp_path) -> None:
    with pytest.raises(ValueError):
        write_evidence_json(_evidence(), "../storage_health_evidence.json", tmp_path)


def test_writer_does_not_write_sensitive_values(tmp_path) -> None:
    evidence = StorageEvidence(
        evidence_type=StorageEvidenceType.STORAGE_HEALTH,
        status=EvidenceStatus.FAIL,
        metadata={"secret_key": "super-secret", "note": "safe"},
    )

    write_evidence_json(evidence, "storage_health_evidence.json", tmp_path)
    rendered = (tmp_path / "storage_health_evidence.json").read_text(encoding="utf-8")

    assert "super-secret" not in rendered
    assert REDACTED in rendered
