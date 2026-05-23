from app.schemas.bastion_trace import BusinessTraceEvent, BusinessTraceEventType


def emit_placeholder(event_type: BusinessTraceEventType, payload: dict[str, object]) -> BusinessTraceEvent:
    return BusinessTraceEvent(event_type=event_type, payload=payload, delivered=False)
