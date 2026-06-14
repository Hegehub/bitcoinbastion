import json
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.event_outbox import EventOutbox, EventOutboxStatus
from app.db.models.time_utils import utcnow

_REDACTED = "[REDACTED]"
_SECRET_ERROR_TOKENS = (
    "authorization",
    "bearer token",
    "api key",
    "secret key",
    "seed phrase",
    "mnemonic",
    "private key",
    "xprv",
    "yprv",
    "zprv",
    "wallet.dat",
    "keystore",
    "signing material",
)


class EventOutboxRepositoryError(RuntimeError):
    pass


def sanitize_error(error: str | None) -> str:
    if not error:
        return ""
    sanitized = error
    lowered = sanitized.casefold()
    for token in _SECRET_ERROR_TOKENS:
        if token in lowered:
            sanitized = _REDACTED
            break
    return sanitized[:1000]


class EventOutboxRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_event(
        self,
        *,
        event_id: str,
        event_type: str,
        domain: str,
        payload_json: str,
        metadata_json: str = "{}",
        event_version: int = 1,
        aggregate_type: str | None = None,
        aggregate_id: str | None = None,
        priority: int = 100,
        max_attempts: int = 5,
        next_attempt_at: datetime | None = None,
    ) -> EventOutbox:
        item = EventOutbox(
            event_id=event_id,
            event_type=event_type,
            event_version=event_version,
            domain=domain,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload_json=payload_json,
            metadata_json=metadata_json,
            status=EventOutboxStatus.PENDING.value,
            priority=priority,
            attempts=0,
            max_attempts=max_attempts,
            next_attempt_at=next_attempt_at,
        )
        self.db.add(item)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise EventOutboxRepositoryError("event_id already exists") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise EventOutboxRepositoryError("could not create outbox event") from exc
        self.db.refresh(item)
        return item

    def get_by_event_id(self, event_id: str) -> EventOutbox | None:
        stmt = select(EventOutbox).where(EventOutbox.event_id == event_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get(self, event_id_or_pk: str | int) -> EventOutbox | None:
        if isinstance(event_id_or_pk, int):
            return self.db.get(EventOutbox, event_id_or_pk)
        return self.get_by_event_id(event_id_or_pk)

    def get_by_idempotency_key(self, event_type: str, idempotency_key: str) -> EventOutbox | None:
        stmt = (
            select(EventOutbox)
            .where(EventOutbox.event_type == event_type)
            .where(EventOutbox.status != EventOutboxStatus.CANCELLED.value)
            .order_by(EventOutbox.created_at.asc())
        )
        for item in self.db.execute(stmt).scalars():
            try:
                metadata = json.loads(item.metadata_json or "{}")
            except json.JSONDecodeError:
                continue
            if metadata.get("idempotency_key") == idempotency_key:
                return item
        return None

    def list_pending(self, limit: int = 100) -> list[EventOutbox]:
        now = utcnow()
        stmt = (
            select(EventOutbox)
            .where(EventOutbox.status == EventOutboxStatus.PENDING.value)
            .where(
                (EventOutbox.next_attempt_at.is_(None)) | (EventOutbox.next_attempt_at <= now)
            )
            .order_by(EventOutbox.priority.asc(), EventOutbox.created_at.asc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars())

    def list_by_status(
        self, status: str, limit: int = 100, offset: int = 0
    ) -> list[EventOutbox]:
        stmt = (
            select(EventOutbox)
            .where(EventOutbox.status == status)
            .order_by(EventOutbox.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars())

    def list_by_aggregate(self, aggregate_type: str, aggregate_id: str) -> list[EventOutbox]:
        stmt = (
            select(EventOutbox)
            .where(EventOutbox.aggregate_type == aggregate_type)
            .where(EventOutbox.aggregate_id == aggregate_id)
            .order_by(EventOutbox.created_at.asc())
        )
        return list(self.db.execute(stmt).scalars())

    def mark_locked(self, event_id: str, locked_by: str) -> EventOutbox:
        item = self._require_event(event_id)
        if item.status != EventOutboxStatus.PENDING.value:
            raise EventOutboxRepositoryError("only pending events can be locked")
        item.status = EventOutboxStatus.LOCKED.value
        item.locked_by = locked_by[:120]
        item.locked_at = utcnow()
        item.updated_at = utcnow()
        return self._save(item)

    def mark_dispatched(self, event_id: str) -> EventOutbox:
        item = self._require_event(event_id)
        if item.status not in {EventOutboxStatus.LOCKED.value, EventOutboxStatus.PENDING.value}:
            raise EventOutboxRepositoryError("event cannot be marked dispatched from current status")
        item.status = EventOutboxStatus.DISPATCHED.value
        item.dispatched_at = utcnow()
        item.locked_by = None
        item.locked_at = None
        item.updated_at = utcnow()
        return self._save(item)

    def mark_retry(
        self, event_id: str, error: str, next_attempt_at: datetime | None
    ) -> EventOutbox:
        item = self._require_event(event_id)
        if item.status not in {EventOutboxStatus.LOCKED.value, EventOutboxStatus.PENDING.value}:
            raise EventOutboxRepositoryError("event cannot be scheduled for retry from current status")
        item.status = EventOutboxStatus.PENDING.value
        item.attempts += 1
        item.last_error = sanitize_error(error)
        item.next_attempt_at = next_attempt_at
        item.locked_by = None
        item.locked_at = None
        item.updated_at = utcnow()
        return self._save(item)

    def mark_failed(
        self, event_id: str, error: str, next_attempt_at: datetime | None
    ) -> EventOutbox:
        item = self._require_event(event_id)
        if item.status not in {EventOutboxStatus.LOCKED.value, EventOutboxStatus.PENDING.value}:
            raise EventOutboxRepositoryError("event cannot be marked failed from current status")
        item.status = EventOutboxStatus.FAILED.value
        item.attempts += 1
        item.last_error = sanitize_error(error)
        item.next_attempt_at = next_attempt_at
        item.locked_by = None
        item.locked_at = None
        item.updated_at = utcnow()
        return self._save(item)

    def mark_dead_letter(self, event_id: str, error: str) -> EventOutbox:
        item = self._require_event(event_id)
        item.status = EventOutboxStatus.DEAD_LETTER.value
        item.last_error = sanitize_error(error)
        item.dead_lettered_at = utcnow()
        item.locked_by = None
        item.locked_at = None
        item.updated_at = utcnow()
        return self._save(item)

    def increment_attempts(self, event_id: str) -> EventOutbox:
        item = self._require_event(event_id)
        item.attempts += 1
        item.updated_at = utcnow()
        if item.status == EventOutboxStatus.FAILED.value and item.attempts < item.max_attempts:
            item.status = EventOutboxStatus.PENDING.value
        return self._save(item)

    def cancel(self, event_id: str, reason: str | None = None) -> EventOutbox:
        item = self._require_event(event_id)
        if item.status in {
            EventOutboxStatus.DISPATCHED.value,
            EventOutboxStatus.DEAD_LETTER.value,
        }:
            raise EventOutboxRepositoryError("completed events cannot be cancelled")
        item.status = EventOutboxStatus.CANCELLED.value
        item.last_error = sanitize_error(reason) if reason else item.last_error
        item.locked_by = None
        item.locked_at = None
        item.updated_at = utcnow()
        return self._save(item)

    def _require_event(self, event_id: str) -> EventOutbox:
        item = self.get_by_event_id(event_id)
        if item is None:
            raise EventOutboxRepositoryError("outbox event not found")
        return item

    def _save(self, item: EventOutbox) -> EventOutbox:
        self.db.add(item)
        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise EventOutboxRepositoryError("could not update outbox event") from exc
        self.db.refresh(item)
        return item
