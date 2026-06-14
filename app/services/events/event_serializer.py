from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.events.safety import assert_event_payload_safe
from app.events.serializer import serialize_event_json

WEBHOOK_SOURCE = "bitcoin_bastion"


def _iso_z(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def build_webhook_event_envelope(
    *,
    event_id: str | int,
    event_type: str,
    data: dict[str, object],
    domain: str | None = None,
    created_at: datetime | None = None,
    payload_version: int = 1,
    limitations: list[str] | None = None,
    source: str = WEBHOOK_SOURCE,
) -> dict[str, Any]:
    assert_event_payload_safe(data)
    effective_limitations = limitations or _limitations_from_data(data)
    envelope = {
        "id": str(event_id),
        "type": event_type,
        "event_type": event_type,
        "version": str(payload_version),
        "payload_version": payload_version,
        "created_at": _iso_z(created_at or datetime.now(timezone.utc)),
        "source": source,
        "domain": domain or event_type.split(".", 1)[0],
        "data": data,
        "limitations": effective_limitations,
        "no_custody": bool(data.get("no_custody", True)),
        "advisory_only": bool(data.get("advisory_only", True)),
    }
    assert_event_payload_safe(envelope)
    return envelope


def serialize_webhook_event_envelope(envelope: dict[str, Any]) -> str:
    assert_event_payload_safe(envelope)
    return serialize_event_json(envelope)


def _limitations_from_data(data: dict[str, object]) -> list[str]:
    value = data.get("limitations")
    if isinstance(value, list):
        return [str(item) for item in value]
    return []
