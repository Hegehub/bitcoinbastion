import logging
from collections.abc import Mapping

from sqlalchemy.orm import Session

from app.services.events.event_bus_service import (
    EventBusPublishError,
    EventBusService,
    EventPublishResult,
)

logger = logging.getLogger(__name__)


def publish_domain_event(
    db: Session | object,
    event_type: str,
    payload: dict[str, object],
    *,
    aggregate_type: str | None = None,
    aggregate_id: str | int | None = None,
    source: str | None = None,
    actor_id: str | int | None = None,
    correlation_id: str | None = None,
    idempotency_key: str | None = None,
    metadata: Mapping[str, object] | None = None,
) -> EventPublishResult | None:
    """Best-effort internal domain event publication.

    Domain operations must not call external delivery directly. This helper writes
    to the durable outbox when the current database has the outbox schema
    available, and logs a bounded warning if event publication is unavailable in
    lightweight tests or fallback repositories.
    """
    if not isinstance(db, Session):
        logger.debug(
            "domain_event_skipped_no_session event_type=%s aggregate_type=%s aggregate_id=%s",
            event_type,
            aggregate_type,
            aggregate_id,
        )
        return None
    try:
        return EventBusService(db).publish_event(
            event_type,
            payload,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            source=source,
            actor_id=actor_id,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            metadata=dict(metadata or {}),
        )
    except EventBusPublishError as exc:
        logger.warning(
            "domain_event_rejected event_type=%s aggregate_type=%s aggregate_id=%s reason=%s",
            event_type,
            aggregate_type,
            aggregate_id,
            str(exc),
        )
        return None
    except Exception as exc:  # pragma: no cover - defensive for optional outbox schema tests
        logger.warning(
            "domain_event_unavailable event_type=%s aggregate_type=%s aggregate_id=%s reason=%s",
            event_type,
            aggregate_type,
            aggregate_id,
            type(exc).__name__,
        )
        try:
            db.rollback()
        except Exception:
            pass
        return None
