from typing import Any

from app.events.documentation import event_catalog
from app.events.payloads import BastionEventEnvelope
from app.events.registry import EVENT_REGISTRY, EventMetadata, event_metadata
from app.events.safety import EventPayloadSafetyError, SafetyFlag, assert_event_payload_safe
from app.events.serializer import EventSerializationError, event_payload_hash, serialize_event_json
from app.events.types import (
    ActorType,
    BastionEventType,
    EventDomain,
    EventSeverity,
    EventVisibility,
)


def publish_event(
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
) -> Any:
    from app.events.publisher import publish_event as _publish_event

    return _publish_event(
        event_type,
        payload,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        source=source,
        actor_id=actor_id,
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
        metadata=metadata,
    )

__all__ = [
    "ActorType",
    "BastionEventEnvelope",
    "BastionEventType",
    "EVENT_REGISTRY",
    "EventDomain",
    "EventMetadata",
    "EventPayloadSafetyError",
    "EventSerializationError",
    "event_payload_hash",
    "publish_event",
    "serialize_event_json",
    "EventSeverity",
    "EventVisibility",
    "SafetyFlag",
    "assert_event_payload_safe",
    "event_catalog",
    "event_metadata",
]
