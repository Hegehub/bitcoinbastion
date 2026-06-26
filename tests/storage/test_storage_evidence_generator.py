from app.storage.evidence.generator import (
    generate_object_storage_integrity_evidence,
    generate_outbox_replay_evidence,
    generate_postgres_backup_evidence,
    generate_redis_degraded_mode_evidence,
    generate_storage_health_evidence,
)
from app.storage.evidence.models import EvidenceStatus, StorageEvidenceType


def test_postgres_backup_evidence_warns_without_restore_drill() -> None:
    evidence = generate_postgres_backup_evidence(
        backup_command_present=True,
        migration_smoke_present=True,
        pitr_strategy_documented=True,
        environment="test",
        storage_profile="development",
    )

    assert evidence.evidence_type == StorageEvidenceType.POSTGRES_BACKUP
    assert evidence.status == EvidenceStatus.WARN
    assert evidence.warnings


def test_object_storage_not_configured_behavior() -> None:
    evidence = generate_object_storage_integrity_evidence(configured=False)

    assert evidence.status == EvidenceStatus.NOT_CONFIGURED
    assert evidence.checks[0].status == EvidenceStatus.NOT_CONFIGURED


def test_object_storage_checksum_mismatch_fails() -> None:
    evidence = generate_object_storage_integrity_evidence(
        configured=True,
        bucket_checked="bastion-evidence",
        object_key="proof/packet.json",
        sha256_expected="a" * 64,
        sha256_actual="b" * 64,
        checksum_match=False,
        signature_present=True,
    )

    assert evidence.status == EvidenceStatus.FAIL


def test_outbox_not_configured_behavior() -> None:
    evidence = generate_outbox_replay_evidence(outbox_table_present=False)

    assert evidence.status == EvidenceStatus.NOT_CONFIGURED
    assert evidence.metadata == {}


def test_outbox_replay_warns_when_failed_events_exist() -> None:
    evidence = generate_outbox_replay_evidence(
        outbox_table_present=True,
        pending_events_count=1,
        failed_events_count=2,
        replayed_events_count=3,
        idempotency_check_status="pass",
        projection_targets=["clickhouse"],
    )

    assert evidence.status == EvidenceStatus.WARN
    assert evidence.metadata["failed_events_count"] == 2


def test_redis_not_treated_as_durable_truth() -> None:
    evidence = generate_redis_degraded_mode_evidence(
        redis_not_source_of_truth=True,
        degraded_mode_documented=True,
        critical_health_without_redis_documented=True,
    )

    assert evidence.evidence_type == StorageEvidenceType.REDIS_DEGRADED_MODE
    assert evidence.status == EvidenceStatus.PASS
    assert any(check.status == EvidenceStatus.SKIPPED for check in evidence.checks)


def test_storage_health_not_configured_when_no_statuses_supplied() -> None:
    evidence = generate_storage_health_evidence(store_statuses=None)

    assert evidence.status == EvidenceStatus.NOT_CONFIGURED
    assert {check.name for check in evidence.checks} == {
        "postgres",
        "redis",
        "object_storage",
        "timescale",
        "clickhouse",
        "qdrant",
        "sqlite",
        "duckdb",
    }


def test_storage_health_warns_for_degraded_optional_statuses() -> None:
    evidence = generate_storage_health_evidence(
        store_statuses={"postgres": "ok", "redis": "ok", "object_storage": "degraded"}
    )

    assert evidence.status == EvidenceStatus.WARN
