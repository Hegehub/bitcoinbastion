from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.operations_control import BackupValidationRecord, RecoveryValidationRecord
from app.schemas.health import BackgroundJobHealthOut, HealthOut
from app.schemas.operations import (
    OperationalHealthOut,
    OperationalProviderStatusOut,
    OperationsMetricsSummaryOut,
)
from app.services.observability.operations_control_service import OperationsControlService

ENGINE_PROVIDERS = [
    ("timeline_builders", "timeline", "healthy"),
    ("impact_engine", "intelligence", "healthy"),
    ("attribution_engine", "intelligence", "healthy"),
    ("similarity_engine", "intelligence", "healthy"),
    ("evidence_engine", "evidence", "healthy"),
    ("replay_engine", "evidence", "healthy"),
    ("signal_engine", "signals", "healthy"),
    ("web_interface", "interface", "healthy"),
    ("api_interface", "interface", "healthy"),
    ("scheduler_layer", "scheduler", "maintenance"),
]


class OperationalHealthService:
    """Aggregates BMTM and Bitcoin Bastion operational health without hiding degraded state."""

    def __init__(self) -> None:
        self.operations = OperationsControlService()

    def health(self, db: Session) -> OperationalHealthOut:
        status = self.operations.status(db)
        providers = self.providers(db)
        last_backup = self._last_backup(db)
        last_restore = self._last_restore(db)
        readiness = self.readiness(db).status
        limitations = list(status.operational_limitations)
        offline_required = [
            p
            for p in providers
            if p.provider_type in {"news", "price"} and p.status not in {"healthy", "recovering"}
        ]
        if offline_required:
            limitations.append(
                "One or more required provider groups are degraded; readiness is degraded until provider recovery is validated."
            )
        return OperationalHealthOut(
            system_status=status.system_health,
            provider_status=providers,
            scheduler_status=status.platform_status.job_state,
            timeline_status=self._engine_status(providers, "timeline"),
            evidence_status=self._engine_status(providers, "evidence"),
            signal_queue_status=status.platform_status.signal_pipeline_state,
            last_backup=last_backup.finished_at if last_backup else None,
            last_restore_test=last_restore.finished_at if last_restore else None,
            last_integrity_scan=(
                last_restore.finished_at
                if last_restore and last_restore.integrity_verified
                else None
            ),
            readiness_status=readiness,
            degraded_state_visible=True,
            backup_verified=bool(
                last_backup and last_backup.success and last_backup.integrity_verified
            ),
            restore_verified=bool(
                last_restore
                and last_restore.success
                and last_restore.deterministic_rebuild_verified
            ),
            integrity_verified=bool(last_restore and last_restore.integrity_verified),
            operator_visible=True,
            operational_limitations=limitations,
        )

    def providers(self, db: Session) -> list[OperationalProviderStatusOut]:
        runtime_providers = self.operations.providers(db)
        providers = [
            OperationalProviderStatusOut(
                provider_name=row.provider_name,
                provider_type=self._normalize_provider_type(row.provider_type),
                status=self._normalize_status(row.health_state),
                last_success_at=row.last_success_at,
                last_failure_at=row.last_failure_at,
                latency_ms=row.avg_latency_ms,
                failure_count=row.failure_count,
                provider_confidence=row.provider_confidence,
                backoff_until=row.backoff_until,
                last_error_sanitized=(
                    "provider degraded"
                    if row.health_state not in {"healthy", "maintenance"}
                    else ""
                ),
            )
            for row in runtime_providers
        ]
        providers.extend(
            OperationalProviderStatusOut(
                provider_name=name,
                provider_type=provider_type,
                status=state,
                provider_confidence=1.0 if state == "healthy" else 0.5,
                last_error_sanitized=(
                    "awaiting scheduler heartbeat" if state == "maintenance" else ""
                ),
            )
            for name, provider_type, state in ENGINE_PROVIDERS
        )
        return providers

    def jobs(self, db: Session) -> list[BackgroundJobHealthOut]:
        return self.operations.runtime.job_health(db)

    def metrics(self, db: Session) -> OperationsMetricsSummaryOut:
        return self.operations.metrics_summary(db)

    def readiness(self, db: Session) -> HealthOut:
        providers = self.providers(db)
        news_ok = any(
            p.provider_type == "news" and p.status in {"healthy", "recovering"} for p in providers
        )
        price_ok = any(
            p.provider_type == "price" and p.status in {"healthy", "recovering"} for p in providers
        )
        timeline_ok = self._engine_status(providers, "timeline") in {"healthy", "recovering"}
        dependencies = self.operations.dependencies(db)
        db_ok = any(dep.name == "database" and dep.status == "healthy" for dep in dependencies)
        scheduler_ok = any(
            p.provider_type == "scheduler" and p.status in {"healthy", "maintenance", "recovering"}
            for p in providers
        )
        ready = news_ok and price_ok and timeline_ok and db_ok and scheduler_ok
        return HealthOut(
            status="ready" if ready else "degraded",
            app="Bitcoin Bastion",
            details={
                "news_provider": "ok" if news_ok else "degraded",
                "price_provider": "ok" if price_ok else "degraded",
                "timeline_engine": "ok" if timeline_ok else "degraded",
                "database": "ok" if db_ok else "degraded",
                "scheduler": "ok" if scheduler_ok else "degraded",
            },
        )

    def liveness(self, db: Session) -> HealthOut:
        return HealthOut(
            status="live", app="Bitcoin Bastion", details=self.operations.runtime.liveness(db)
        )

    def _last_backup(self, db: Session) -> BackupValidationRecord | None:
        try:
            return db.execute(
                select(BackupValidationRecord)
                .order_by(BackupValidationRecord.started_at.desc())
                .limit(1)
            ).scalar_one_or_none()
        except SQLAlchemyError:
            return None

    def _last_restore(self, db: Session) -> RecoveryValidationRecord | None:
        try:
            return db.execute(
                select(RecoveryValidationRecord)
                .order_by(RecoveryValidationRecord.started_at.desc())
                .limit(1)
            ).scalar_one_or_none()
        except SQLAlchemyError:
            return None

    def _engine_status(
        self, providers: list[OperationalProviderStatusOut], provider_type: str
    ) -> str:
        states = [p.status for p in providers if p.provider_type == provider_type]
        if not states:
            return "maintenance"
        for state in ("offline", "degraded", "recovering", "maintenance"):
            if state in states:
                return state
        return "healthy"

    def _normalize_status(self, state: str) -> str:
        return (
            "offline"
            if state == "critical"
            else (
                state
                if state in {"healthy", "degraded", "offline", "maintenance", "recovering"}
                else "degraded"
            )
        )

    def _normalize_provider_type(self, value: str) -> str:
        lowered = value.lower()
        if "bitcoin" in lowered or "price" in lowered:
            return "price"
        if "rss" in lowered or "news" in lowered or "blog" in lowered or "regulatory" in lowered:
            return "news"
        if "telegram" in lowered:
            return "telegram"
        return lowered[:40] or "unknown"
