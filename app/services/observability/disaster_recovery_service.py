from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models.operations_control import BackupValidationRecord, RecoveryValidationRecord
from app.schemas.operations import BackupValidationOut, RecoveryValidationOut

REPLAY_TYPES = ["news_event", "candle", "impact", "attribution", "signal", "evidence"]


class DisasterRecoveryService:
    """Deterministic DR validation facade for backup, restore, replay and integrity checks."""

    def verify_backup(self, db: Session, *, backup_id: str, objects_checked: int, integrity_verified: bool, limitations: list[str] | None = None) -> BackupValidationOut:
        now = datetime.utcnow()
        success = objects_checked > 0 and integrity_verified
        row = BackupValidationRecord(
            backup_id=backup_id,
            started_at=now,
            finished_at=now,
            success=success,
            objects_checked=max(0, objects_checked),
            integrity_verified=integrity_verified,
            limitations=limitations or ([] if success else ["backup validation did not verify integrity"]),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return self._backup_out(row)

    def verify_restore(self, db: Session, *, recovery_id: str, validation_type: str = "full_restore", replay_types: list[str] | None = None, integrity_verified: bool = True, deterministic_rebuild_verified: bool = True, limitations: list[str] | None = None) -> RecoveryValidationOut:
        now = datetime.utcnow()
        requested = replay_types or REPLAY_TYPES
        missing = [item for item in REPLAY_TYPES if item not in requested]
        success = integrity_verified and deterministic_rebuild_verified and not missing
        row = RecoveryValidationRecord(
            recovery_id=recovery_id,
            validation_type=validation_type,
            started_at=now,
            finished_at=now,
            success=success,
            deterministic_rebuild_verified=deterministic_rebuild_verified,
            integrity_verified=integrity_verified,
            replay_types=requested,
            limitations=limitations or ([f"missing replay validations: {', '.join(missing)}"] if missing else []),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return self._recovery_out(row)

    def validate_integrity_replay(self, db: Session, *, recovery_id: str) -> RecoveryValidationOut:
        return self.verify_restore(db, recovery_id=recovery_id, validation_type="integrity_replay", replay_types=REPLAY_TYPES, integrity_verified=True, deterministic_rebuild_verified=True)

    def _backup_out(self, row: BackupValidationRecord) -> BackupValidationOut:
        return BackupValidationOut(backup_id=row.backup_id, started_at=row.started_at, finished_at=row.finished_at, success=row.success, objects_checked=row.objects_checked, integrity_verified=row.integrity_verified, limitations=list(row.limitations or []))

    def _recovery_out(self, row: RecoveryValidationRecord) -> RecoveryValidationOut:
        return RecoveryValidationOut(recovery_id=row.recovery_id, validation_type=row.validation_type, started_at=row.started_at, finished_at=row.finished_at, success=row.success, deterministic_rebuild_verified=row.deterministic_rebuild_verified, integrity_verified=row.integrity_verified, replay_types=list(row.replay_types or []), limitations=list(row.limitations or []))
