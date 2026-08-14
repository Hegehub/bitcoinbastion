from datetime import datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.services.observability.operations_reliability_service import (
    IncidentObservation,
    OperationsIncidentService,
    OperationsSLOPolicy,
    OperationsSLOService,
)
from app.schemas.operations_reliability import IncidentSeverity, SLOComparison, SLOStatus


def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def observation(active: bool, at: datetime) -> IncidentObservation:
    return IncidentObservation(
        "provider-availability-v1",
        "PROVIDER_AVAILABILITY",
        "rss",
        active,
        IncidentSeverity.MAJOR,
        "RSS degraded" if active else "RSS healthy",
        "provider-health",
        "",
        at,
    )


def test_incident_deterministic_open_update_resolve_and_recurrence() -> None:
    db = session()
    service = OperationsIncidentService()
    t1 = datetime(2026, 1, 1, 0, 0)
    service.reconcile(db, [])
    assert service.detail(db, "missing") is None
    service.reconcile(db, [observation(True, t1)])
    first = (
        db.execute(
            __import__("sqlalchemy").select(
                __import__(
                    "app.db.models.operations_reliability", fromlist=["OperationsIncident"]
                ).OperationsIncident
            )
        )
        .scalars()
        .all()
    )
    assert len(first) == 1 and first[0].status == "OPEN"
    first_id = first[0].incident_id
    service.reconcile(db, [observation(True, datetime(2026, 1, 1, 0, 1))])
    assert len(db.execute(__import__("sqlalchemy").select(type(first[0]))).scalars().all()) == 1
    service.reconcile(db, [])
    assert service.detail(db, first_id).status.value == "RESOLVED"
    service.reconcile(db, [observation(True, datetime(2026, 1, 1, 0, 2))])
    rows = db.execute(__import__("sqlalchemy").select(type(first[0]))).scalars().all()
    assert len(rows) == 2 and rows[-1].incident_id != first_id
    assert [x.transition.value for x in service.detail(db, first_id).history] == [
        "OPENED",
        "UPDATED",
        "RESOLVED",
    ]


def test_slo_backend_comparators_precision_and_zero_policy() -> None:
    minimum = OperationsSLOPolicy(target=Decimal("0.999"))
    assert OperationsSLOService.evaluate(minimum, Decimal("0.999")) == SLOStatus.WITHIN_TARGET
    assert OperationsSLOService.evaluate(minimum, Decimal("0.998999")) == SLOStatus.BREACHED
    maximum = OperationsSLOPolicy(target=Decimal("0.100"), comparison=SLOComparison.AT_MOST)
    assert OperationsSLOService.evaluate(maximum, Decimal("0.100")) == SLOStatus.WITHIN_TARGET
    assert OperationsSLOService.evaluate(maximum, Decimal("0.101")) == SLOStatus.BREACHED
    assert OperationsSLOService(()).list(session()) == []


def test_operations_slo_schema_is_separate_from_recovery_schema() -> None:
    from app.schemas.observability import RecoverySLOOut
    from app.schemas.operations_reliability import OperationsSLOOut

    assert OperationsSLOOut is not RecoverySLOOut
    assert "recovery_slo" not in OperationsSLOOut.model_fields
    assert "target" in OperationsSLOOut.model_fields
