from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.signal import Signal
from app.db.repositories.delivery_repository import DeliveryRepository
from app.db.repositories.job_run_repository import JobRunRepository
from app.db.repositories.signal_repository import SignalRepository
from app.services.observability.operations_service import OperationsSnapshotService


def test_operations_snapshot_includes_job_and_delivery_stats() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        runs = JobRunRepository(db)
        started = runs.start("delivery.publish")
        runs.finish(started, status="failed", error_message="network timeout")

        signal = SignalRepository(db).add(
            Signal(
                signal_type="news",
                severity="high",
                score=0.9,
                confidence=0.9,
                title="Delivery test signal",
                summary="summary",
            )
        )
        DeliveryRepository(db).record_sent(
            signal_id=signal.id,
            destination="dry-run",
            payload_snapshot={"title": signal.title},
        )

        snapshot = OperationsSnapshotService().snapshot(db=db)

    assert snapshot.jobs.started_24h >= 1
    assert snapshot.jobs.failed_24h >= 1
    assert snapshot.deliveries.sent_24h >= 1
    assert any(item.provider == "delivery" for item in snapshot.providers)
