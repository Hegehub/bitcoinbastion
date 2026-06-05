from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Callable

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.cache import get_redis_client
from app.db.models.operations_control import OperationsEvidence
from app.schemas.health import DependencyHealthOut, IntelligenceHealthOut, OperationsHealthOut, ProviderHealthSnapshotOut
from app.schemas.operations import (
    AlertSummaryOut,
    OperationsDrillOut,
    OperationsMetricsSummaryOut,
    OperationsRunbookOut,
    OperationsStatusOut,
)
from app.services.observability.runtime_status_service import RuntimeStatusService

RUNBOOKS = [
    OperationsRunbookOut(slug="database", title="Database Restore", path="docs/RUNBOOK_DATABASE.md", failure_modes=["database unavailable", "failed migration"]),
    OperationsRunbookOut(slug="workers", title="Worker Restart", path="docs/RUNBOOK_WORKERS.md", failure_modes=["worker stopped", "background queue growth"]),
    OperationsRunbookOut(slug="providers", title="Provider Outage", path="docs/RUNBOOK_PROVIDERS.md", failure_modes=["rss outage", "provider confidence collapse", "btc provider outage"]),
    OperationsRunbookOut(slug="telegram", title="Telegram Outage", path="docs/RUNBOOK_TELEGRAM.md", failure_modes=["telegram publication failures"]),
    OperationsRunbookOut(slug="deployment", title="Failed Deployment", path="docs/RUNBOOK_DEPLOYMENT.md", failure_modes=["failed deployment", "migration mismatch"]),
]


class OperationsControlService:
    def __init__(self) -> None:
        self.runtime = RuntimeStatusService()

    def dependencies(self, db: Session) -> list[DependencyHealthOut]:
        deps = [self._probe("database", lambda: db.execute(text("SELECT 1")))]
        deps.append(self._probe("redis", lambda: get_redis_client().ping()))
        deps.append(self._probe("filesystem", lambda: Path("/tmp").exists()))
        runtime = self.runtime.status(db)
        deps.extend(
            [
                self._from_state("celery", runtime.job_state, runtime.last_success, None),
                self._from_state("background workers", runtime.job_state, runtime.last_success, None),
                self._from_state("telegram", runtime.telegram_state, runtime.telegram_health.last_publish_success, runtime.telegram_health.last_publish_failure),
                self._from_state("rss collectors", self._provider_family_state(runtime.provider_health, "rss"), None, None),
                self._from_state("btc market providers", self._provider_family_state(runtime.provider_health, "bitcoin"), None, None),
                self._from_state("news providers", self._provider_family_state(runtime.provider_health, "rss"), None, None),
            ]
        )
        return deps

    def status(self, db: Session) -> OperationsStatusOut:
        runtime = self.runtime.status(db)
        drills = self.drills(db)
        degraded = runtime.degraded_components
        return OperationsStatusOut(
            platform_status=runtime,
            dependency_status=self.dependencies(db),
            provider_status=runtime.provider_health,
            operations_timeline=drills,
            recovery_drills=drills,
            system_health=runtime.system_state,
            alert_summary=AlertSummaryOut(
                critical=sum(1 for item in degraded if item.severity in {"critical", "offline"}),
                warning=sum(1 for item in degraded if item.severity in {"degraded", "maintenance"}),
                degraded_components=degraded,
            ),
            operational_limitations=[item.recommendation for item in degraded],
        )

    def providers(self, db: Session) -> list[ProviderHealthSnapshotOut]:
        return self.runtime.provider_health(db)

    def drills(self, db: Session) -> list[OperationsDrillOut]:
        try:
            rows = db.execute(select(OperationsEvidence).order_by(OperationsEvidence.started_at.desc()).limit(50)).scalars().all()
        except SQLAlchemyError:
            rows = []
        return [
            OperationsDrillOut(
                drill_id=row.drill_id,
                drill_type=row.drill_type,
                started_at=row.started_at,
                finished_at=row.finished_at,
                success=row.success,
                operator=row.operator,
                notes=row.notes,
                artifact_refs=list(row.artifact_refs or []),
            )
            for row in rows
        ]

    def metrics_summary(self, db: Session) -> OperationsMetricsSummaryOut:
        runtime = self.runtime.status(db)
        degraded = runtime.system_state != "healthy"
        return OperationsMetricsSummaryOut(
            api_availability_status="healthy" if runtime.system_state in {"healthy", "maintenance"} else "degraded",
            background_job_success_status=runtime.job_state,
            provider_availability_status=runtime.provider_state,
            signal_generation_latency_status=runtime.signal_pipeline_state,
            evidence_generation_latency_status=runtime.evidence_pipeline_state,
            replay_latency_status="healthy",
            degraded_state=degraded,
            operational_limitations=[item.recommendation for item in runtime.degraded_components],
        )

    def runbooks(self) -> list[OperationsRunbookOut]:
        return RUNBOOKS

    def intelligence_health(self, db: Session) -> IntelligenceHealthOut:
        runtime = self.runtime.status(db)
        confidences = [p.provider_confidence for p in runtime.provider_health]
        confidence = min(confidences) if confidences else 0.0
        failures = [p.last_failure_at for p in runtime.provider_health if p.last_failure_at]
        return IntelligenceHealthOut(
            status=self.runtime._rollup([runtime.signal_pipeline_state, runtime.evidence_pipeline_state, runtime.provider_state]),
            provider_confidence=confidence,
            degraded_state=bool(runtime.degraded_components),
            last_success=runtime.last_success,
            last_failure=max(failures) if failures else None,
            operational_limitations=[item.recommendation for item in runtime.degraded_components],
        )

    def operations_health(self, db: Session) -> OperationsHealthOut:
        deps = self.dependencies(db)
        failed = [dep for dep in deps if dep.status not in {"healthy", "maintenance"}]
        runtime = self.runtime.status(db)
        return OperationsHealthOut(
            status="critical" if any(dep.status == "critical" for dep in failed) else ("degraded" if failed else "healthy"),
            dependencies=deps,
            degraded_state=bool(failed or runtime.degraded_components),
            last_success=runtime.last_success,
            last_failure=max([dep.last_failure_at for dep in deps if dep.last_failure_at], default=None),
            operational_limitations=[dep.degraded_reason for dep in failed if dep.degraded_reason],
        )

    def _probe(self, name: str, fn: Callable[[], object]) -> DependencyHealthOut:
        start = time.perf_counter()
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - dependency health must expose failures, not hide them.
            return DependencyHealthOut(
                name=name,
                status="critical",
                latency_ms=(time.perf_counter() - start) * 1000,
                provider_confidence=0.0,
                degraded_reason=type(exc).__name__,
            )
        return DependencyHealthOut(name=name, status="healthy", latency_ms=(time.perf_counter() - start) * 1000)

    def _from_state(self, name: str, state: str, last_success: datetime | None, last_failure: datetime | None) -> DependencyHealthOut:
        return DependencyHealthOut(
            name=name,
            status=state,
            last_success_at=last_success,
            last_failure_at=last_failure,
            provider_confidence=1.0 if state == "healthy" else 0.5,
            degraded_reason="" if state == "healthy" else f"{name} state is {state}",
        )

    def _provider_family_state(self, providers: list[ProviderHealthSnapshotOut], family: str) -> str:
        states = [p.health_state for p in providers if family in p.provider_type.lower() or family in p.provider_name.lower()]
        return self.runtime._rollup(states or ["maintenance"])
