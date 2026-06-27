import asyncio
from datetime import datetime, UTC

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db.base import Base
from app.db.models.storage_outbox_event import StorageOutboxEvent
from app.db.repositories.storage_outbox_repository import StorageOutboxRepository
from app.storage.analytics_store.errors import AnalyticsStoreInsertError
from app.storage.projections.clickhouse_projector import ClickHouseOutboxProjector


class FailingAnalyticsStore:
    async def insert_events(self, table: str, events: list[dict[str, object]]):
        raise AnalyticsStoreInsertError("ClickHouse insert failed: api key secret")


class RecordingAnalyticsStore:
    def __init__(self) -> None:
        self.inserted: list[tuple[str, list[dict[str, object]]]] = []

    async def insert_events(self, table: str, events: list[dict[str, object]]):
        self.inserted.append((table, events))
        return type("Result", (), {"inserted_count": len(events)})()


def make_db() -> Session:
    engine = create_engine("sqlite://", future=True, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Session(engine)


def add_event(
    db: Session, *, payload: dict[str, object], event_type: str = "api.usage.event"
) -> str:
    event = StorageOutboxEvent(
        event_id=f"event-{len(db.info)}",
        event_type=event_type,
        aggregate_type="usage",
        aggregate_id="usage-1",
        payload_json=payload,
        metadata_json={},
        target_stores=["clickhouse"],
        available_at=datetime.now(UTC),
    )
    db.info[event.event_id] = True
    db.add(event)
    db.commit()
    return event.event_id


def settings() -> Settings:
    return Settings(
        _env_file=None,
        CLICKHOUSE_ENABLED=True,
        CLICKHOUSE_PROFILE="development",
        CLICKHOUSE_PASSWORD="dev-password",
    )


def test_transient_clickhouse_failure_marks_retry_without_secret_leak() -> None:
    with make_db() as db:
        event_id = add_event(db, payload={"occurred_at": "2026-06-26T00:00:00+00:00"})
        projector = ClickHouseOutboxProjector(
            settings=settings(),
            outbox_repository=StorageOutboxRepository(db),
            analytics_store=FailingAnalyticsStore(),
        )
        summary = asyncio.run(projector.project_batch())
        event = StorageOutboxRepository(db).get_by_event_id(event_id)

    assert summary.failed_retryable == 1
    assert event is not None
    assert event.status == "retry"
    assert event.retry_count == 1
    assert event.last_error == "[REDACTED]"


def test_invalid_payload_marks_failed_terminal() -> None:
    with make_db() as db:
        event_id = add_event(db, payload={"private_key": "do-not-store"})
        projector = ClickHouseOutboxProjector(
            settings=settings(),
            outbox_repository=StorageOutboxRepository(db),
            analytics_store=RecordingAnalyticsStore(),
        )
        summary = asyncio.run(projector.project_batch())
        event = StorageOutboxRepository(db).get_by_event_id(event_id)

    assert summary.failed_terminal == 1
    assert event is not None
    assert event.status == "failed"
    assert event.last_error == "[REDACTED]"


def test_unsupported_event_marks_failed_terminal() -> None:
    with make_db() as db:
        event_id = add_event(db, payload={"safe": True}, event_type="unknown.event")
        projector = ClickHouseOutboxProjector(
            settings=settings(),
            outbox_repository=StorageOutboxRepository(db),
            analytics_store=RecordingAnalyticsStore(),
        )
        summary = asyncio.run(projector.project_batch())
        event = StorageOutboxRepository(db).get_by_event_id(event_id)

    assert summary.failed_terminal == 1
    assert event is not None
    assert event.status == "failed"
