import json
from hashlib import sha256

from app.storage.evidence.generator import (
    STORAGE_EVIDENCE_FILENAMES,
    generate_object_storage_integrity_evidence,
    generate_outbox_replay_evidence,
    generate_postgres_backup_evidence,
    generate_postgres_restore_evidence,
)
from app.storage.evidence.models import EvidenceStatus, StorageEvidenceType
from app.storage.evidence.writer import write_evidence_json


def test_postgres_backup_evidence_shape_and_writer_checksum(tmp_path) -> None:
    evidence = generate_postgres_backup_evidence(
        backup_command_present=True,
        migration_smoke_present=True,
        pitr_strategy_documented=True,
        last_restore_drill_at="2026-06-21T00:00:00Z",
        environment="test",
        storage_profile="development",
        metadata={"storage_engine": "postgres", "artifact_refs": []},
    )
    result = write_evidence_json(
        evidence, STORAGE_EVIDENCE_FILENAMES[StorageEvidenceType.POSTGRES_BACKUP], tmp_path
    )

    payload = json.loads((tmp_path / "storage_backup_evidence.json").read_text())
    assert payload["evidence_type"] == "postgres_backup"
    assert payload["status"] == "pass"
    assert payload["metadata"]["storage_engine"] == "postgres"
    assert "checks" in payload
    assert "errors" in payload
    assert (
        result.sha256
        == sha256((tmp_path / "storage_backup_evidence.json").read_bytes()).hexdigest()
    )


def test_postgres_restore_evidence_shape() -> None:
    evidence = generate_postgres_restore_evidence(
        restore_command_present=True,
        schema_parity_present=True,
        migration_smoke_present=True,
        pitr_strategy_documented=True,
        last_restore_drill_at="2026-06-21T00:00:00Z",
        metadata={"storage_engine": "postgres", "artifact_refs": ["restore-log"]},
    )

    assert evidence.evidence_type == StorageEvidenceType.POSTGRES_RESTORE
    assert evidence.status == EvidenceStatus.PASS
    assert evidence.metadata["artifact_refs"] == ["restore-log"]


def test_object_storage_integrity_evidence_shape() -> None:
    evidence = generate_object_storage_integrity_evidence(
        configured=True,
        bucket_checked="bastion-evidence",
        object_key="proof/packet.json",
        sha256_expected="a" * 64,
        sha256_actual="a" * 64,
        checksum_match=True,
        size_bytes=64,
        content_type="application/json",
        retention_policy="evidence",
        signature_present=False,
        metadata={"storage_engine": "object_storage"},
    )

    assert evidence.evidence_type == StorageEvidenceType.OBJECT_STORAGE_INTEGRITY
    assert evidence.status == EvidenceStatus.WARN
    assert evidence.metadata["checksum_match"] is True
    assert evidence.metadata["sha256_expected"] == "a" * 64


def test_outbox_replay_evidence_shape() -> None:
    evidence = generate_outbox_replay_evidence(
        outbox_table_present=True,
        pending_events_count=0,
        failed_events_count=0,
        replayed_events_count=3,
        last_replay_at="2026-06-21T00:00:00Z",
        idempotency_check_status="pass",
        projection_targets=["clickhouse", "websocket"],
        metadata={"storage_engine": "postgres", "artifact_refs": []},
    )

    assert evidence.evidence_type == StorageEvidenceType.OUTBOX_REPLAY
    assert evidence.status == EvidenceStatus.PASS
    assert evidence.metadata["projection_targets"] == ["clickhouse", "websocket"]


def test_not_configured_evidence_is_not_silent_pass() -> None:
    evidence = generate_object_storage_integrity_evidence(configured=False)

    assert evidence.status == EvidenceStatus.NOT_CONFIGURED
    assert evidence.status != EvidenceStatus.PASS
