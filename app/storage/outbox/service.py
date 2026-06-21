from datetime import timedelta

from app.db.models.storage_outbox_event import StorageOutboxEvent
from app.db.models.time_utils import utcnow
from app.db.repositories.storage_outbox_repository import StorageOutboxRepository, stale_lock_cutoff
from app.storage.outbox.enums import StorageOutboxEventStatus
from app.storage.outbox.schemas import (
    StorageOutboxEventCreate,
    validate_no_sensitive_outbox_material,
)


class StorageOutboxService:
    def __init__(self, repository: StorageOutboxRepository) -> None:
        self.repository = repository

    def enqueue_event(
        self,
        *,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        payload_json: dict[str, object],
        target_stores: list[str],
        aggregate_version: int | None = None,
        metadata_json: dict[str, object] | None = None,
        priority: int = 100,
        max_retries: int = 10,
        idempotency_key: str | None = None,
    ) -> StorageOutboxEvent:
        payload = StorageOutboxEventCreate(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            aggregate_version=aggregate_version,
            payload_json=payload_json,
            metadata_json=metadata_json or {},
            target_stores=target_stores,
            priority=priority,
            max_retries=max_retries,
            idempotency_key=idempotency_key,
        )
        return self._create_from_payload(payload)

    def enqueue_once(
        self,
        *,
        idempotency_key: str,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        payload_json: dict[str, object],
        target_stores: list[str],
        aggregate_version: int | None = None,
        metadata_json: dict[str, object] | None = None,
        priority: int = 100,
        max_retries: int = 10,
    ) -> StorageOutboxEvent:
        existing = self.repository.get_by_idempotency_key(idempotency_key)
        if existing is not None:
            return existing
        return self.enqueue_event(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            aggregate_version=aggregate_version,
            payload_json=payload_json,
            metadata_json=metadata_json,
            target_stores=target_stores,
            priority=priority,
            max_retries=max_retries,
            idempotency_key=idempotency_key,
        )

    def claim_batch(self, *, worker_id: str, limit: int = 100) -> list[StorageOutboxEvent]:
        validate_no_sensitive_outbox_material(worker_id, "worker_id")
        return self.repository.claim_pending_events(worker_id=worker_id, limit=limit)

    def record_success(self, event_id: str) -> StorageOutboxEvent:
        return self.repository.mark_processed(event_id)

    def record_retryable_failure(
        self,
        event_id: str,
        error: str,
        delay_seconds: int | None = None,
    ) -> StorageOutboxEvent:
        event = self.repository.get_by_event_id(event_id)
        if event is None:
            raise ValueError("storage outbox event not found")
        if event.retry_count >= event.max_retries:
            return self.repository.mark_dead_letter(event_id, error)
        delay = (
            delay_seconds if delay_seconds is not None else self.backoff_seconds(event.retry_count)
        )
        return self.repository.mark_retry(event_id, error, utcnow() + timedelta(seconds=delay))

    def record_permanent_failure(
        self, event_id: str, error: str, *, dead_letter: bool = False
    ) -> StorageOutboxEvent:
        if dead_letter:
            return self.repository.mark_dead_letter(event_id, error)
        return self.repository.mark_failed(event_id, error)

    def release_stale_locks(self, *, older_than_seconds: int = 900) -> int:
        return self.repository.release_stale_locks(
            older_than=stale_lock_cutoff(timedelta(seconds=older_than_seconds))
        )

    def get_status_counts(self) -> dict[str, int]:
        return self.repository.count_by_status()

    def backoff_seconds(self, retry_count: int) -> int:
        return min(3600, (2**retry_count) * 30)

    def _create_from_payload(self, payload: StorageOutboxEventCreate) -> StorageOutboxEvent:
        event = StorageOutboxEvent(
            event_id=payload.event_id,
            event_type=payload.event_type,
            aggregate_type=payload.aggregate_type,
            aggregate_id=payload.aggregate_id,
            aggregate_version=payload.aggregate_version,
            payload_json=payload.payload_json,
            metadata_json=payload.metadata_json,
            target_stores=[str(item) for item in payload.target_stores],
            idempotency_key=payload.idempotency_key,
            status=StorageOutboxEventStatus.PENDING.value,
            priority=payload.priority,
            retry_count=0,
            max_retries=payload.max_retries,
            available_at=payload.available_at or utcnow(),
        )
        return self.repository.create_event(event)
