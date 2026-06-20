from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.storage_outbox_event import StorageOutboxEvent
from app.db.models.time_utils import utcnow
from app.storage.outbox.enums import StorageOutboxEventStatus
from app.storage.outbox.errors import StorageOutboxRepositoryError

_SECRET_ERROR_TOKENS = (
    "authorization",
    "bearer",
    "api key",
    "secret",
    "seed phrase",
    "mnemonic",
    "private key",
    "xprv",
    "yprv",
    "zprv",
    "wallet.dat",
)


def sanitize_storage_outbox_error(error: str | None) -> str:
    if not error:
        return ""
    lowered = error.casefold()
    if any(token in lowered for token in _SECRET_ERROR_TOKENS):
        return "[REDACTED]"
    return error[:1000]


class StorageOutboxRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_event(self, event: StorageOutboxEvent, *, commit: bool = True) -> StorageOutboxEvent:
        if event.idempotency_key:
            existing = self.get_by_idempotency_key(event.idempotency_key)
            if existing is not None:
                return existing
        self.db.add(event)
        if not commit:
            try:
                self.db.flush()
            except IntegrityError as exc:
                self.db.rollback()
                if event.idempotency_key:
                    existing = self.get_by_idempotency_key(event.idempotency_key)
                    if existing is not None:
                        return existing
                raise StorageOutboxRepositoryError("storage outbox event already exists") from exc
            except SQLAlchemyError as exc:
                self.db.rollback()
                raise StorageOutboxRepositoryError("could not stage storage outbox event") from exc
            return event
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            if event.idempotency_key:
                existing = self.get_by_idempotency_key(event.idempotency_key)
                if existing is not None:
                    return existing
            raise StorageOutboxRepositoryError("storage outbox event already exists") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise StorageOutboxRepositoryError("could not create storage outbox event") from exc
        self.db.refresh(event)
        return event

    def get_by_event_id(self, event_id: str) -> StorageOutboxEvent | None:
        stmt = select(StorageOutboxEvent).where(StorageOutboxEvent.event_id == event_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_idempotency_key(self, idempotency_key: str) -> StorageOutboxEvent | None:
        stmt = select(StorageOutboxEvent).where(
            StorageOutboxEvent.idempotency_key == idempotency_key
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def claim_pending_events(self, *, worker_id: str, limit: int = 100) -> list[StorageOutboxEvent]:
        now = utcnow()
        stmt = (
            select(StorageOutboxEvent)
            .where(
                StorageOutboxEvent.status.in_(
                    [StorageOutboxEventStatus.PENDING.value, StorageOutboxEventStatus.RETRY.value]
                )
            )
            .where(StorageOutboxEvent.available_at <= now)
            .order_by(
                StorageOutboxEvent.priority.asc(),
                StorageOutboxEvent.created_at.asc(),
                StorageOutboxEvent.id.asc(),
            )
            .limit(limit)
        )
        events = list(self.db.execute(stmt).scalars())
        for event in events:
            event.status = StorageOutboxEventStatus.PROCESSING.value
            event.locked_by = worker_id
            event.locked_at = now
            event.updated_at = now
        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise StorageOutboxRepositoryError("could not claim storage outbox events") from exc
        for event in events:
            self.db.refresh(event)
        return events

    def mark_processed(self, event_id: str) -> StorageOutboxEvent:
        event = self._require_event(event_id)
        now = utcnow()
        event.status = StorageOutboxEventStatus.PROCESSED.value
        event.processed_at = now
        event.locked_by = None
        event.locked_at = None
        event.last_error = None
        event.updated_at = now
        return self._save(event)

    def mark_retry(self, event_id: str, error: str, available_at: datetime) -> StorageOutboxEvent:
        event = self._require_event(event_id)
        event.retry_count += 1
        if event.retry_count > event.max_retries:
            event.status = StorageOutboxEventStatus.DEAD_LETTER.value
        else:
            event.status = StorageOutboxEventStatus.RETRY.value
            event.available_at = available_at
        event.last_error = sanitize_storage_outbox_error(error)
        event.locked_by = None
        event.locked_at = None
        event.updated_at = utcnow()
        return self._save(event)

    def mark_failed(self, event_id: str, error: str) -> StorageOutboxEvent:
        event = self._require_event(event_id)
        event.status = StorageOutboxEventStatus.FAILED.value
        event.last_error = sanitize_storage_outbox_error(error)
        event.locked_by = None
        event.locked_at = None
        event.updated_at = utcnow()
        return self._save(event)

    def mark_dead_letter(self, event_id: str, error: str) -> StorageOutboxEvent:
        event = self._require_event(event_id)
        event.status = StorageOutboxEventStatus.DEAD_LETTER.value
        event.last_error = sanitize_storage_outbox_error(error)
        event.locked_by = None
        event.locked_at = None
        event.updated_at = utcnow()
        return self._save(event)

    def release_stale_locks(self, *, older_than: datetime) -> int:
        stmt = (
            select(StorageOutboxEvent)
            .where(StorageOutboxEvent.status == StorageOutboxEventStatus.PROCESSING.value)
            .where(StorageOutboxEvent.locked_at.is_not(None))
            .where(StorageOutboxEvent.locked_at < older_than)
            .order_by(StorageOutboxEvent.locked_at.asc())
        )
        events = list(self.db.execute(stmt).scalars())
        now = utcnow()
        for event in events:
            event.status = StorageOutboxEventStatus.RETRY.value
            event.locked_by = None
            event.locked_at = None
            event.available_at = now
            event.last_error = sanitize_storage_outbox_error("released stale storage outbox lock")
            event.updated_at = now
        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise StorageOutboxRepositoryError(
                "could not release stale storage outbox locks"
            ) from exc
        return len(events)

    def count_by_status(self) -> dict[str, int]:
        stmt = select(StorageOutboxEvent.status, func.count(StorageOutboxEvent.id)).group_by(
            StorageOutboxEvent.status
        )
        return {status: count for status, count in self.db.execute(stmt).all()}

    def _require_event(self, event_id: str) -> StorageOutboxEvent:
        event = self.get_by_event_id(event_id)
        if event is None:
            raise StorageOutboxRepositoryError("storage outbox event not found")
        return event

    def _save(self, event: StorageOutboxEvent) -> StorageOutboxEvent:
        try:
            self.db.add(event)
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise StorageOutboxRepositoryError("could not update storage outbox event") from exc
        self.db.refresh(event)
        return event


def stale_lock_cutoff(age: timedelta) -> datetime:
    return utcnow() - age
