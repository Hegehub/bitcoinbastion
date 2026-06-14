import json
from datetime import timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.event_outbox import EventOutbox, EventOutboxStatus
from app.db.models.time_utils import utcnow
from app.db.repositories.event_outbox_repository import (
    EventOutboxRepository,
    EventOutboxRepositoryError,
)


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine, tables=[EventOutbox.__table__])
    return Session(engine)


def _create(repo: EventOutboxRepository, event_id: str = "event-1") -> EventOutbox:
    return repo.create_event(
        event_id=event_id,
        event_type="signal.published",
        domain="signal",
        aggregate_type="signal",
        aggregate_id="123",
        payload_json=json.dumps({"signal_id": 123}),
        metadata_json=json.dumps({"source": "test"}),
    )


def test_create_get_and_list_by_aggregate() -> None:
    with _session() as db:
        repo = EventOutboxRepository(db)
        item = _create(repo)

        assert repo.get_by_event_id(item.event_id).id == item.id
        assert repo.get(item.id).event_id == item.event_id
        assert repo.list_by_aggregate("signal", "123")[0].event_id == item.event_id


def test_duplicate_event_id_raises_repository_error() -> None:
    with _session() as db:
        repo = EventOutboxRepository(db)
        _create(repo)
        with pytest.raises(EventOutboxRepositoryError):
            _create(repo)


def test_list_pending_returns_only_pending_eligible_events() -> None:
    with _session() as db:
        repo = EventOutboxRepository(db)
        ready = _create(repo, "ready")
        repo.create_event(
            event_id="future",
            event_type="signal.published",
            domain="signal",
            payload_json="{}",
            metadata_json="{}",
            next_attempt_at=utcnow() + timedelta(hours=1),
        )
        locked = _create(repo, "locked")
        repo.mark_locked(locked.event_id, "worker-1")

        assert [item.event_id for item in repo.list_pending()] == [ready.event_id]


def test_status_transition_helpers() -> None:
    with _session() as db:
        repo = EventOutboxRepository(db)
        item = _create(repo)

        locked = repo.mark_locked(item.event_id, "worker-1")
        assert locked.status == EventOutboxStatus.LOCKED.value
        assert locked.locked_at is not None
        assert locked.locked_by == "worker-1"

        failed = repo.mark_failed(item.event_id, "authorization bearer token leaked", utcnow())
        assert failed.status == EventOutboxStatus.FAILED.value
        assert failed.attempts == 1
        assert failed.last_error == "[REDACTED]"

        retry = repo.increment_attempts(item.event_id)
        assert retry.status == EventOutboxStatus.PENDING.value
        assert retry.attempts == 2

        locked_again = repo.mark_locked(item.event_id, "worker-2")
        dispatched = repo.mark_dispatched(locked_again.event_id)
        assert dispatched.status == EventOutboxStatus.DISPATCHED.value
        assert dispatched.dispatched_at is not None
        assert dispatched.locked_by is None


def test_mark_dead_letter_and_cancel() -> None:
    with _session() as db:
        repo = EventOutboxRepository(db)
        dead = _create(repo, "dead")
        cancelled = _create(repo, "cancelled")

        dead_letter = repo.mark_dead_letter(dead.event_id, "private key should not persist")
        assert dead_letter.status == EventOutboxStatus.DEAD_LETTER.value
        assert dead_letter.dead_lettered_at is not None
        assert dead_letter.last_error == "[REDACTED]"

        cancelled_item = repo.cancel(cancelled.event_id, "operator cancelled")
        assert cancelled_item.status == EventOutboxStatus.CANCELLED.value
        assert cancelled_item.last_error == "operator cancelled"
