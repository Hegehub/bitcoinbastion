from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.operations_reliability import OperationsIncident, OperationsIncidentTransition
from app.db.repositories.job_run_repository import JobRunRepository
from app.schemas.operations_reliability import (
    IncidentDetailOut,
    IncidentOut,
    IncidentSeverity,
    IncidentStatus,
    IncidentTransitionOut,
    IncidentTransitionType,
    OperationsSLOOut,
    SLOComparison,
    SLOStatus,
    SLOUnit,
)
from app.services.observability.runtime_status_service import RuntimeStatusService


@dataclass(frozen=True)
class IncidentObservation:
    detector_id: str
    kind: str
    target: str
    qualifying: bool
    severity: IncidentSeverity
    summary: str
    source: str
    limitations: str
    observed_at: datetime

    @property
    def correlation_key(self) -> str:
        return f"{self.detector_id}:{self.kind}:{self.target}"


class OperationsIncidentService:
    """Backend-owned OPEN/RESOLVED incident policy over typed runtime observations."""

    DETECTOR_ID = "runtime-component-availability-v1"

    def observations(self, db: Session) -> list[IncidentObservation]:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        status = RuntimeStatusService().status(db)
        return [
            IncidentObservation(
                detector_id=self.DETECTOR_ID,
                kind="COMPONENT_AVAILABILITY",
                target=item.affected_component,
                qualifying=item.severity in {"degraded", "critical", "offline"},
                severity=(
                    IncidentSeverity.CRITICAL
                    if item.severity in {"critical", "offline"}
                    else IncidentSeverity.MAJOR
                ),
                summary=f"{item.affected_component} reported {item.severity}",
                source="runtime-status",
                limitations=item.recommendation,
                observed_at=now,
            )
            for item in status.degraded_components
        ]

    def reconcile(self, db: Session, observations: list[IncidentObservation] | None = None) -> None:
        observations = self.observations(db) if observations is None else observations
        active = {o.correlation_key: o for o in observations if o.qualifying}
        open_rows = (
            db.execute(
                select(OperationsIncident).where(
                    OperationsIncident.status == IncidentStatus.OPEN.value
                )
            )
            .scalars()
            .all()
        )
        open_by_key = {row.correlation_key: row for row in open_rows}
        for key, observation in active.items():
            row = open_by_key.get(key)
            if row is None:
                self._open(db, observation)
            else:
                row.updated_at = observation.observed_at
                row.summary = observation.summary
                row.limitations = observation.limitations
                self._transition(db, row, IncidentTransitionType.UPDATED, observation)
        for key, row in open_by_key.items():
            if key not in active:
                now = datetime.now(timezone.utc).replace(tzinfo=None)
                clear = IncidentObservation(
                    row.detector_id,
                    row.kind,
                    row.affected_target,
                    False,
                    IncidentSeverity(row.severity),
                    f"{row.affected_target} clear condition observed",
                    row.source,
                    row.limitations,
                    now,
                )
                row.status = IncidentStatus.RESOLVED.value
                row.resolved_at = now
                row.updated_at = now
                row.active_correlation_key = None
                self._transition(db, row, IncidentTransitionType.RESOLVED, clear)
        db.commit()

    def _open(self, db: Session, observation: IncidentObservation) -> None:
        row = OperationsIncident(
            incident_id=str(uuid4()),
            correlation_key=observation.correlation_key,
            active_correlation_key=observation.correlation_key,
            detector_id=observation.detector_id,
            kind=observation.kind,
            status=IncidentStatus.OPEN.value,
            severity=observation.severity.value,
            affected_target=observation.target,
            summary=observation.summary,
            source=observation.source,
            limitations=observation.limitations,
            opened_at=observation.observed_at,
            updated_at=observation.observed_at,
        )
        try:
            db.add(row)
            db.flush()
            self._transition(db, row, IncidentTransitionType.OPENED, observation)
        except IntegrityError:
            db.rollback()  # database unique constraint wins a concurrent detector race

    @staticmethod
    def _transition(
        db: Session,
        row: OperationsIncident,
        transition: IncidentTransitionType,
        observation: IncidentObservation,
    ) -> None:
        db.add(
            OperationsIncidentTransition(
                incident_id=row.incident_id,
                transition=transition.value,
                status=row.status,
                severity=row.severity,
                observed_at=observation.observed_at,
                source=observation.source,
                summary=observation.summary,
            )
        )

    def list(self, db: Session) -> list[IncidentOut]:
        self.reconcile(db)
        rows = (
            db.execute(select(OperationsIncident).order_by(OperationsIncident.opened_at.desc()))
            .scalars()
            .all()
        )
        return [IncidentOut.model_validate(row) for row in rows]

    def detail(self, db: Session, incident_id: str) -> IncidentDetailOut | None:
        row = db.execute(
            select(OperationsIncident).where(OperationsIncident.incident_id == incident_id)
        ).scalar_one_or_none()
        if row is None:
            return None
        history = (
            db.execute(
                select(OperationsIncidentTransition)
                .where(OperationsIncidentTransition.incident_id == incident_id)
                .order_by(OperationsIncidentTransition.observed_at)
            )
            .scalars()
            .all()
        )
        return IncidentDetailOut(
            **IncidentOut.model_validate(row).model_dump(),
            history=[IncidentTransitionOut.model_validate(item) for item in history],
        )


@dataclass(frozen=True)
class OperationsSLOPolicy:
    slo_id: str = "operations-job-success-24h"
    title: str = "Operational job success"
    service: str = "background-jobs"
    indicator_id: str = "operations.job_success_ratio"
    target: Decimal = Decimal("0.99")
    unit: SLOUnit = SLOUnit.RATIO
    comparison: SLOComparison = SLOComparison.AT_LEAST
    window: timedelta = timedelta(hours=24)
    minimum_samples: int = 1


class OperationsSLOService:
    """Independent Operations SLI registry and backend evaluator (not Recovery SLO)."""

    def __init__(self, policies: tuple[OperationsSLOPolicy, ...] | None = None) -> None:
        self.policies = policies if policies is not None else (OperationsSLOPolicy(),)

    def list(self, db: Session) -> list[OperationsSLOOut]:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        repo = JobRunRepository(db)
        started = repo.started_count_last_24h()
        failed = repo.failed_count_last_24h()
        output: list[OperationsSLOOut] = []
        for policy in self.policies:
            current = (
                None
                if started < policy.minimum_samples
                else Decimal(started - failed) / Decimal(started)
            )
            status = (
                SLOStatus.INSUFFICIENT_DATA if current is None else self.evaluate(policy, current)
            )
            output.append(
                OperationsSLOOut(
                    slo_id=policy.slo_id,
                    title=policy.title,
                    service=policy.service,
                    indicator_id=policy.indicator_id,
                    target=policy.target,
                    current=current,
                    unit=policy.unit,
                    comparison=policy.comparison,
                    window_seconds=int(policy.window.total_seconds()),
                    status=status,
                    sample_count=started,
                    observed_at=now,
                    source="job-runs",
                    limitations="Current evaluation uses completed job runs in the configured 24-hour window.",
                )
            )
        return output

    @staticmethod
    def evaluate(policy: OperationsSLOPolicy, current: Decimal) -> SLOStatus:
        if policy.comparison == SLOComparison.AT_LEAST:
            return SLOStatus.WITHIN_TARGET if current >= policy.target else SLOStatus.BREACHED
        return SLOStatus.WITHIN_TARGET if current <= policy.target else SLOStatus.BREACHED
