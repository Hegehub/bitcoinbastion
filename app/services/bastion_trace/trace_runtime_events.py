from datetime import UTC, datetime

_EVENTS: list[dict[str, object]] = []


def create_event(event_type: str, severity: str, operation: str, status: str, message: str, metadata: dict[str, object] | None = None) -> dict[str, object]:
    event = {
        "id": len(_EVENTS) + 1,
        "event_type": event_type,
        "severity": severity,
        "operation": operation,
        "status": status,
        "message": message,
        "metadata_json": metadata or {},
        "created_at": datetime.now(UTC).isoformat(),
    }
    _EVENTS.append(event)
    return event


def list_events() -> list[dict[str, object]]:
    return list(_EVENTS)


def get_event(event_id: int) -> dict[str, object] | None:
    for e in _EVENTS:
        if e["id"] == event_id:
            return e
    return None
