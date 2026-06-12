from app.db.session import SessionLocal
from app.services.events.event_bus_service import EventBusService, EventPublishResult


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
) -> EventPublishResult:
    with SessionLocal() as db:
        service = EventBusService(db)
        return service.publish_event(
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
