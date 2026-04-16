from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.signal import Signal
from app.db.repositories.delivery_repository import DeliveryRepository
from app.db.repositories.signal_repository import SignalRepository
from app.services.delivery.publish_service import SignalPublishService


def _build_signal(title: str, score: float) -> Signal:
    return Signal(
        signal_type="news",
        severity="high",
        score=score,
        confidence=0.85,
        title=title,
        summary="Signal summary",
    )


def test_publish_service_marks_unpublished_signals_as_published() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        signal_repo = SignalRepository(db)
        signal_repo.add(_build_signal("First", 0.9))
        signal_repo.add(_build_signal("Second", 0.8))

        published = SignalPublishService(
            signals=signal_repo,
            deliveries=DeliveryRepository(db),
        ).publish_pending(limit=10)

        remaining = signal_repo.unpublished(limit=10)

    assert published == 2
    assert remaining == []


def test_publish_service_suppresses_duplicates_for_same_destination() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        signal_repo = SignalRepository(db)
        signal = signal_repo.add(_build_signal("Duplicate candidate", 0.9))
        delivery_repo = DeliveryRepository(db)

        service = SignalPublishService(signals=signal_repo, deliveries=delivery_repo)
        first_count = service.publish_pending(limit=10)

        # Force unpublished flag back to emulate a rerun race/rollback scenario.
        signal.is_published = False
        db.commit()

        second_count = service.publish_pending(limit=10)

    assert first_count == 1
    assert second_count == 0
