"""Storage evidence generators for backup, restore, integrity, outbox, and health."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from app.storage.evidence.models import (
    EvidenceCheckItem,
    EvidenceStatus,
    StorageEvidence,
    StorageEvidenceType,
)

STORAGE_EVIDENCE_FILENAMES = {
    StorageEvidenceType.POSTGRES_BACKUP: "storage_backup_evidence.json",
    StorageEvidenceType.POSTGRES_RESTORE: "storage_restore_evidence.json",
    StorageEvidenceType.REDIS_DEGRADED_MODE: "redis_degraded_mode_evidence.json",
    StorageEvidenceType.OBJECT_STORAGE_INTEGRITY: "object_storage_integrity_evidence.json",
    StorageEvidenceType.OUTBOX_REPLAY: "storage_outbox_replay_evidence.json",
    StorageEvidenceType.STORAGE_HEALTH: "storage_health_evidence.json",
}


def generate_postgres_backup_evidence(
    *,
    backup_command_present: bool,
    migration_smoke_present: bool,
    pitr_strategy_documented: bool,
    environment: str = "unknown",
    storage_profile: str = "unknown",
    last_restore_drill_at: datetime | str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> StorageEvidence:
    checks = [
        _bool_check(
            "backup_command_present", backup_command_present, "Backup command or job is declared."
        ),
        _bool_check(
            "migration_smoke_present",
            migration_smoke_present,
            "Migration smoke evidence hook is declared.",
        ),
        _bool_check(
            "pitr_strategy_documented", pitr_strategy_documented, "PITR strategy is documented."
        ),
    ]
    warnings = [] if last_restore_drill_at else ["last_restore_drill_at is not supplied."]
    status = _status_from_checks(checks, warn_if=bool(warnings))
    return _evidence(
        evidence_type=StorageEvidenceType.POSTGRES_BACKUP,
        status=status,
        environment=environment,
        storage_profile=storage_profile,
        checks=checks,
        warnings=warnings,
        metadata={"last_restore_drill_at": last_restore_drill_at, **dict(metadata or {})},
    )


def generate_postgres_restore_evidence(
    *,
    restore_command_present: bool,
    schema_parity_present: bool,
    migration_smoke_present: bool,
    pitr_strategy_documented: bool,
    environment: str = "unknown",
    storage_profile: str = "unknown",
    last_restore_drill_at: datetime | str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> StorageEvidence:
    checks = [
        _bool_check(
            "restore_command_present",
            restore_command_present,
            "Restore command or drill job is declared.",
        ),
        _bool_check(
            "schema_parity_present",
            schema_parity_present,
            "Schema parity validation hook is declared.",
        ),
        _bool_check(
            "migration_smoke_present",
            migration_smoke_present,
            "Migration smoke validation hook is declared.",
        ),
        _bool_check(
            "pitr_strategy_documented",
            pitr_strategy_documented,
            "PITR restore strategy is documented.",
        ),
    ]
    warnings = [] if last_restore_drill_at else ["last_restore_drill_at is not supplied."]
    status = _status_from_checks(checks, warn_if=bool(warnings))
    return _evidence(
        evidence_type=StorageEvidenceType.POSTGRES_RESTORE,
        status=status,
        environment=environment,
        storage_profile=storage_profile,
        checks=checks,
        warnings=warnings,
        metadata={"last_restore_drill_at": last_restore_drill_at, **dict(metadata or {})},
    )


def generate_redis_degraded_mode_evidence(
    *,
    redis_not_source_of_truth: bool,
    degraded_mode_documented: bool,
    critical_health_without_redis_documented: bool,
    automated_detection_available: bool = False,
    environment: str = "unknown",
    storage_profile: str = "unknown",
    metadata: Mapping[str, Any] | None = None,
) -> StorageEvidence:
    checks = [
        _bool_check(
            "redis_not_source_of_truth",
            redis_not_source_of_truth,
            "Redis is documented as ephemeral, not durable truth.",
        ),
        _bool_check(
            "degraded_mode_documented",
            degraded_mode_documented,
            "Redis outage behavior is documented as degraded mode.",
        ),
        _bool_check(
            "critical_health_without_redis_documented",
            critical_health_without_redis_documented,
            "Critical state is documented outside Redis.",
        ),
    ]
    if not automated_detection_available:
        checks.append(
            EvidenceCheckItem(
                name="automated_source_of_truth_detection",
                status=EvidenceStatus.SKIPPED,
                details={
                    "reason": "Automated Redis source-of-truth detection is not implemented yet."
                },
            )
        )
    status = _status_from_checks(checks)
    return _evidence(
        evidence_type=StorageEvidenceType.REDIS_DEGRADED_MODE,
        status=status,
        environment=environment,
        storage_profile=storage_profile,
        checks=checks,
        metadata=dict(metadata or {}),
    )


def generate_object_storage_integrity_evidence(
    *,
    configured: bool,
    bucket_checked: str | None = None,
    object_key: str | None = None,
    sha256_expected: str | None = None,
    sha256_actual: str | None = None,
    checksum_match: bool | None = None,
    size_bytes: int | None = None,
    content_type: str | None = None,
    retention_policy: str | None = None,
    signature_present: bool | None = None,
    environment: str = "unknown",
    storage_profile: str = "unknown",
    metadata: Mapping[str, Any] | None = None,
) -> StorageEvidence:
    if not configured:
        check = EvidenceCheckItem(
            name="object_storage_configured",
            status=EvidenceStatus.NOT_CONFIGURED,
            details={"reason": "Object Storage is not configured for integrity evidence."},
        )
        return _evidence(
            evidence_type=StorageEvidenceType.OBJECT_STORAGE_INTEGRITY,
            status=EvidenceStatus.NOT_CONFIGURED,
            environment=environment,
            storage_profile=storage_profile,
            checks=[check],
            metadata=dict(metadata or {}),
        )

    checks = [
        _bool_check(
            "checksum_match", bool(checksum_match), "Object checksum comparison completed."
        ),
    ]
    warnings = []
    if signature_present is False:
        warnings.append("signature_present=false; unsigned object integrity evidence is weaker.")
    status = _status_from_checks(checks, warn_if=bool(warnings))
    return _evidence(
        evidence_type=StorageEvidenceType.OBJECT_STORAGE_INTEGRITY,
        status=status,
        environment=environment,
        storage_profile=storage_profile,
        checks=checks,
        warnings=warnings,
        metadata={
            "bucket_checked": bucket_checked,
            "object_key": object_key,
            "sha256_expected": sha256_expected,
            "sha256_actual": sha256_actual,
            "checksum_match": checksum_match,
            "size_bytes": size_bytes,
            "content_type": content_type,
            "retention_policy": retention_policy,
            "signature_present": signature_present,
            **dict(metadata or {}),
        },
    )


def generate_outbox_replay_evidence(
    *,
    outbox_table_present: bool,
    pending_events_count: int | None = None,
    failed_events_count: int | None = None,
    replayed_events_count: int | None = None,
    last_replay_at: datetime | str | None = None,
    idempotency_check_status: str | None = None,
    projection_targets: list[str] | None = None,
    environment: str = "unknown",
    storage_profile: str = "unknown",
    metadata: Mapping[str, Any] | None = None,
) -> StorageEvidence:
    if not outbox_table_present:
        check = EvidenceCheckItem(
            name="outbox_table_present",
            status=EvidenceStatus.NOT_CONFIGURED,
            details={"reason": "storage_outbox_events table is not available."},
        )
        return _evidence(
            evidence_type=StorageEvidenceType.OUTBOX_REPLAY,
            status=EvidenceStatus.NOT_CONFIGURED,
            environment=environment,
            storage_profile=storage_profile,
            checks=[check],
            metadata=dict(metadata or {}),
        )

    failed_count = failed_events_count or 0
    checks = [
        EvidenceCheckItem(
            name="outbox_table_present",
            status=EvidenceStatus.PASS,
            details={"table": "storage_outbox_events"},
        ),
        EvidenceCheckItem(
            name="idempotency_check_status",
            status=(
                EvidenceStatus.PASS if idempotency_check_status == "pass" else EvidenceStatus.WARN
            ),
            details={"idempotency_check_status": idempotency_check_status or "unknown"},
        ),
        EvidenceCheckItem(
            name="failed_events_count",
            status=EvidenceStatus.PASS if failed_count == 0 else EvidenceStatus.WARN,
            details={"failed_events_count": failed_count},
        ),
    ]
    status = _status_from_checks(checks)
    return _evidence(
        evidence_type=StorageEvidenceType.OUTBOX_REPLAY,
        status=status,
        environment=environment,
        storage_profile=storage_profile,
        checks=checks,
        metadata={
            "outbox_table_present": outbox_table_present,
            "pending_events_count": pending_events_count,
            "failed_events_count": failed_events_count,
            "replayed_events_count": replayed_events_count,
            "last_replay_at": last_replay_at,
            "idempotency_check_status": idempotency_check_status,
            "projection_targets": projection_targets or [],
            **dict(metadata or {}),
        },
    )


def generate_storage_health_evidence(
    *,
    store_statuses: Mapping[str, str] | None,
    environment: str = "unknown",
    storage_profile: str = "unknown",
    metadata: Mapping[str, Any] | None = None,
) -> StorageEvidence:
    stores = [
        "postgres",
        "redis",
        "object_storage",
        "timescale",
        "clickhouse",
        "qdrant",
        "sqlite",
        "duckdb",
    ]
    if not store_statuses:
        checks = [
            EvidenceCheckItem(
                name=store,
                status=EvidenceStatus.NOT_CONFIGURED,
                details={"reason": "No storage health status supplied."},
            )
            for store in stores
        ]
        return _evidence(
            evidence_type=StorageEvidenceType.STORAGE_HEALTH,
            status=EvidenceStatus.NOT_CONFIGURED,
            environment=environment,
            storage_profile=storage_profile,
            checks=checks,
            metadata=dict(metadata or {}),
        )

    checks = []
    for store in stores:
        raw_status = str(store_statuses.get(store, "not_configured"))
        checks.append(
            EvidenceCheckItem(
                name=store,
                status=_health_status_to_evidence(raw_status),
                details={"storage_status": raw_status},
            )
        )
    status = _status_from_checks(checks)
    return _evidence(
        evidence_type=StorageEvidenceType.STORAGE_HEALTH,
        status=status,
        environment=environment,
        storage_profile=storage_profile,
        checks=checks,
        metadata=dict(metadata or {}),
    )


def _health_status_to_evidence(status: str) -> EvidenceStatus:
    normalized = status.lower()
    if normalized == "ok":
        return EvidenceStatus.PASS
    if normalized in {"disabled", "not_configured", "not_implemented"}:
        return EvidenceStatus.NOT_CONFIGURED
    if normalized in {"degraded", "unknown"}:
        return EvidenceStatus.WARN
    return EvidenceStatus.FAIL


def _bool_check(name: str, passed: bool, detail: str) -> EvidenceCheckItem:
    return EvidenceCheckItem(
        name=name,
        status=EvidenceStatus.PASS if passed else EvidenceStatus.FAIL,
        details={"result": bool(passed), "description": detail},
    )


def _status_from_checks(
    checks: list[EvidenceCheckItem], *, warn_if: bool = False
) -> EvidenceStatus:
    statuses = {check.status for check in checks}
    if EvidenceStatus.FAIL in statuses:
        return EvidenceStatus.FAIL
    if statuses and statuses == {EvidenceStatus.NOT_CONFIGURED}:
        return EvidenceStatus.NOT_CONFIGURED
    if EvidenceStatus.WARN in statuses or warn_if:
        return EvidenceStatus.WARN
    if EvidenceStatus.NOT_CONFIGURED in statuses:
        return EvidenceStatus.WARN
    if EvidenceStatus.PASS in statuses:
        return EvidenceStatus.PASS
    if EvidenceStatus.SKIPPED in statuses:
        return EvidenceStatus.SKIPPED
    return EvidenceStatus.NOT_CONFIGURED


def _evidence(
    *,
    evidence_type: StorageEvidenceType,
    status: EvidenceStatus,
    environment: str,
    storage_profile: str,
    checks: list[EvidenceCheckItem],
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> StorageEvidence:
    return StorageEvidence(
        evidence_type=evidence_type,
        status=status,
        environment=environment,
        storage_profile=storage_profile,
        checks=checks,
        warnings=warnings or [],
        errors=errors or [],
        metadata=dict(metadata or {}),
    )
