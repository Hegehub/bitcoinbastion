from datetime import datetime, UTC

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db.base import Base
from app.db.models.storage_outbox_event import StorageOutboxEvent
from app.db.repositories.storage_outbox_repository import StorageOutboxRepository
from app.tasks import storage_outbox_tasks


class FakeAnalyticsStore:
    def __init__(self) -> None:
        self.inserted: list[tuple[str, list[dict[str, object]]]] = []

    async def insert_events(self, table: str, events: list[dict[str, object]]):
        self.inserted.append((table, events))
        return type("Result", (), {"inserted_count": len(events)})()


def test_clickhouse_projection_task_projects_and_marks_processed(monkeypatch) -> None:
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    fake_store = FakeAnalyticsStore()
    settings = Settings(
        _env_file=None,
        CLICKHOUSE_ENABLED=True,
        CLICKHOUSE_PROFILE="development",
        CLICKHOUSE_PASSWORD="dev-password",
    )
    with SessionLocal() as db:
        db.add(
            StorageOutboxEvent(
                event_id="outbox-task-1",
                event_type="api.usage.event",
                aggregate_type="usage",
                aggregate_id="usage-1",
                payload_json={"occurred_at": "2026-06-26T00:00:00+00:00"},
                metadata_json={},
                target_stores=["clickhouse"],
                available_at=datetime.now(UTC),
            )
        )
        db.commit()

    monkeypatch.setattr(storage_outbox_tasks, "SessionLocal", SessionLocal)
    monkeypatch.setattr(storage_outbox_tasks, "get_settings", lambda: settings)
    monkeypatch.setattr(storage_outbox_tasks, "build_analytics_store", lambda _: fake_store)

    summary = storage_outbox_tasks.project_clickhouse_events.run(batch_size=10)

    with SessionLocal() as db:
        event = StorageOutboxRepository(db).get_by_event_id("outbox-task-1")
    assert summary["processed"] == 1
    assert summary["inserted"] == 1
    assert fake_store.inserted[0][0] == "api_usage_events"
    assert event is not None
    assert event.status == "processed"


def test_clickhouse_projection_task_dry_run_does_not_insert_or_mark(monkeypatch) -> None:
    engine = create_engine("sqlite://", future=True, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    fake_store = FakeAnalyticsStore()
    settings = Settings(
        _env_file=None,
        CLICKHOUSE_ENABLED=True,
        CLICKHOUSE_PROFILE="development",
        CLICKHOUSE_PASSWORD="dev-password",
    )
    with SessionLocal() as db:
        db.add(
            StorageOutboxEvent(
                event_id="outbox-dry-run-1",
                event_type="api.usage.event",
                aggregate_type="usage",
                aggregate_id="usage-1",
                payload_json={"occurred_at": "2026-06-26T00:00:00+00:00"},
                metadata_json={},
                target_stores=["clickhouse"],
                available_at=datetime.now(UTC),
            )
        )
        db.commit()

    monkeypatch.setattr(storage_outbox_tasks, "SessionLocal", SessionLocal)
    monkeypatch.setattr(storage_outbox_tasks, "get_settings", lambda: settings)
    monkeypatch.setattr(storage_outbox_tasks, "build_analytics_store", lambda _: fake_store)

    summary = storage_outbox_tasks.project_clickhouse_events.run(batch_size=10, dry_run=True)

    with SessionLocal() as db:
        event = StorageOutboxRepository(db).get_by_event_id("outbox-dry-run-1")
    assert summary["processed"] == 1
    assert summary["skipped"] == 1
    assert fake_store.inserted == []
    assert event is not None
    assert event.status == "pending"
