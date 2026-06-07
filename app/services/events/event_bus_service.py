import logging
from collections.abc import Mapping
from typing import cast

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.models.event_outbox import EventOutboxStatus
from app.db.repositories.event_outbox_repository import EventOutboxRepository
from app.events.metadata import _SECRET_VALUE_TERMS, build_event_metadata, normalize_optional_string, normalize_source
from app.events.registry import EVENT_REGISTRY
from app.events.safety import EventPayloadSafetyError, assert_event_payload_safe
from app.events.serializer import EventSerializationError, event_payload_hash, normalize_event_value
from app.events.types import BastionEventType
from app.services.events.outbox_service import EventOutboxService, EventOutboxValidationError

logger = logging.getLogger(__name__)


class EventPublishStatus:
    PUBLISHED_TO_OUTBOX = "published_to_outbox"
    DUPLICATE_IGNORED = "duplicate_ignored"
    REJECTED = "rejected"


class EventPublishResult(BaseModel):
    event_id: int | str
    event_type: str
    status: str
    outbox_status: str
    idempotency_key: str | None = None


class EventBusPublishError(ValueError):
    pass


class EventBusService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.outbox_service = EventOutboxService(db)
        self.repository = EventOutboxRepository(db)

    def publish_event(
        self,
        event_type: str,
        payload: dict[str, object],
        *,
        aggregate_type: str | None = None,
        aggregate_id: str | int | None = None,
        source: str | None = None,
        actor_id: str | int | None = None,
        correlation_id: str | None = None,
        idempotency_key: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> EventPublishResult:
        parsed_event_type = self._validate_event_type(event_type)
        normalized_payload = self._normalize_and_validate_payload(payload)
        normalized_aggregate_type = self._validate_safe_string(aggregate_type, "aggregate_type")
        normalized_source = self._validate_safe_string(normalize_source(source), "source")
        normalized_aggregate_id = normalize_optional_string(aggregate_id)
        normalized_actor_id = normalize_optional_string(actor_id)
        normalized_idempotency_key = self._validate_safe_string(
            idempotency_key, "idempotency_key"
        )
        event_version = 1

        if normalized_idempotency_key:
            existing = self.repository.get_by_idempotency_key(
                parsed_event_type.value, normalized_idempotency_key
            )
            if existing is not None:
                self._log_publish(
                    event_type=parsed_event_type.value,
                    event_id=existing.event_id,
                    aggregate_type=normalized_aggregate_type,
                    aggregate_id=normalized_aggregate_id,
                    source=normalized_source,
                    status=EventPublishStatus.DUPLICATE_IGNORED,
                )
                return EventPublishResult(
                    event_id=existing.event_id,
                    event_type=existing.event_type,
                    status=EventPublishStatus.DUPLICATE_IGNORED,
                    outbox_status=existing.status,
                    idempotency_key=normalized_idempotency_key,
                )

        event_metadata = build_event_metadata(
            event_type=parsed_event_type.value,
            event_version=event_version,
            payload=normalized_payload,
            aggregate_type=normalized_aggregate_type,
            aggregate_id=normalized_aggregate_id,
            source=normalized_source,
            actor_id=normalized_actor_id,
            correlation_id=correlation_id,
            idempotency_key=normalized_idempotency_key,
            metadata=metadata,
        )
        self._assert_metadata_safe(event_metadata)
        domain = EVENT_REGISTRY[parsed_event_type].domain.value
        try:
            outbox_event = self.outbox_service.record_event(
                event_type=parsed_event_type.value,
                domain=domain,
                payload=normalized_payload,
                aggregate_type=normalized_aggregate_type,
                aggregate_id=normalized_aggregate_id,
                metadata=event_metadata,
                event_version=event_version,
            )
        except EventOutboxValidationError as exc:
            raise EventBusPublishError(str(exc)) from exc

        self._log_publish(
            event_type=outbox_event.event_type,
            event_id=outbox_event.event_id,
            aggregate_type=outbox_event.aggregate_type,
            aggregate_id=outbox_event.aggregate_id,
            source=normalized_source,
            status=EventPublishStatus.PUBLISHED_TO_OUTBOX,
        )
        return EventPublishResult(
            event_id=outbox_event.event_id,
            event_type=outbox_event.event_type,
            status=EventPublishStatus.PUBLISHED_TO_OUTBOX,
            outbox_status=EventOutboxStatus.PENDING.value,
            idempotency_key=normalized_idempotency_key,
        )

    def _validate_event_type(self, event_type: str) -> BastionEventType:
        try:
            parsed = BastionEventType(event_type)
        except ValueError as exc:
            raise EventBusPublishError("event_type is not registered") from exc
        if parsed not in EVENT_REGISTRY:
            raise EventBusPublishError("event_type is missing registry metadata")
        return parsed

    def _normalize_and_validate_payload(self, payload: Mapping[str, object]) -> dict[str, object]:
        try:
            assert_event_payload_safe(payload)
            normalized = normalize_event_value(payload)
        except (EventPayloadSafetyError, EventSerializationError) as exc:
            raise EventBusPublishError(str(exc)) from exc
        if not isinstance(normalized, dict):
            raise EventBusPublishError("event payload must be a JSON object")
        return cast(dict[str, object], normalized)

    def _assert_metadata_safe(self, metadata: Mapping[str, object]) -> None:
        try:
            assert_event_payload_safe(metadata)
        except EventPayloadSafetyError as exc:
            raise EventBusPublishError(str(exc)) from exc

    def _validate_safe_string(self, value: str | None, label: str) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        if not normalized:
            return None
        try:
            assert_event_payload_safe({label: normalized})
        except EventPayloadSafetyError as exc:
            raise EventBusPublishError(f"{label} contains unsafe material") from exc
        lowered = normalized.casefold()
        if any(term in lowered for term in _SECRET_VALUE_TERMS):
            raise EventBusPublishError(f"{label} contains unsafe material")
        return normalized

    def _log_publish(
        self,
        *,
        event_type: str,
        event_id: str,
        aggregate_type: str | None,
        aggregate_id: str | None,
        source: str | None,
        status: str,
    ) -> None:
        logger.info(
            "event_bus_publish event_type=%s event_id=%s aggregate_type=%s "
            "aggregate_id=%s source=%s status=%s",
            event_type,
            event_id,
            aggregate_type,
            aggregate_id,
            source,
            status,
        )


def stable_payload_hash(payload: Mapping[str, object]) -> str:
    return event_payload_hash(payload)
