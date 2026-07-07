from __future__ import annotations

from datetime import datetime, timezone
import json
from app.db.models.event_outbox import EventOutbox
from app.events.serializer import serialize_event_json
from app.services.events.websocket_filters import event_type_to_topic

MAX_PAYLOAD_BYTES = 16 * 1024
FORBIDDEN_MATERIAL = (
    "seed phrase",
    "mnemonic",
    "private key",
    "xprv",
    "yprv",
    "zprv",
    "wallet.dat",
    "keystore",
    "12 words",
    "24 words",
    "signing material",
    "webhook secret",
    "authorization",
    "bearer token",
    "api key",
)
_SECRET_KEYS = {
    "authorization",
    "api_key",
    "apikey",
    "api-token",
    "api_token",
    "bearer",
    "bearer_token",
    "private_key",
    "signing_material",
    "webhook_secret",
    "secret",
    "token",
}


def utc_timestamp(value: datetime | None = None) -> str:
    observed = value or datetime.now(timezone.utc)
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=timezone.utc)
    return observed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def system_message(event_type: str, message: str, **extra: object) -> dict[str, object]:
    return {"type": "system", "event_type": event_type, "message": message, **extra}


def heartbeat_message() -> dict[str, object]:
    return {"type": "heartbeat", "event_type": "heartbeat", "timestamp": utc_timestamp()}


def error_message(
    message: str,
    *,
    supported_topics: list[str],
    code: str = "invalid_topic",
    recoverable: bool = True,
) -> dict[str, object]:
    return {
        "type": "error",
        "event_type": "subscription.invalid",
        "code": code,
        "message": message,
        "recoverable": recoverable,
        "supported_topics": supported_topics,
    }


def serialize_outbox_event(event: EventOutbox, *, limit_payload: bool = True) -> dict[str, object]:
    try:
        payload = json.loads(event.payload_json or "{}")
    except json.JSONDecodeError:
        payload = {"unparseable_payload": True}
    try:
        metadata = json.loads(event.metadata_json or "{}")
    except json.JSONDecodeError:
        metadata = {}
    if not isinstance(payload, dict):
        payload = {"value": payload}
    if not isinstance(metadata, dict):
        metadata = {}
    return serialize_event_payload(
        event_id=event.event_id,
        event_type=event.event_type,
        domain=event.domain,
        version=event.event_version,
        occurred_at=event.created_at,
        payload=payload,
        metadata=metadata,
        limit_payload=limit_payload,
    )


def serialize_event_payload(
    *,
    event_id: str,
    event_type: str,
    domain: str,
    version: int,
    occurred_at: datetime | None,
    payload: dict[str, object],
    metadata: dict[str, object] | None = None,
    limit_payload: bool = True,
) -> dict[str, object]:
    topic = event_type_to_topic(event_type)
    sanitized_payload, redacted = _sanitize_value(payload)
    if not isinstance(sanitized_payload, dict):
        sanitized_payload = {"value": sanitized_payload}
    if limit_payload:
        encoded = serialize_event_json(sanitized_payload)
        if len(encoded.encode("utf-8")) > MAX_PAYLOAD_BYTES:
            sanitized_payload = {"truncated": True, "reason": "payload_size_limit"}
            redacted = True
    safe_metadata, metadata_redacted = _sanitize_value(metadata or {})
    if not isinstance(safe_metadata, dict):
        safe_metadata = {}
    redacted = redacted or metadata_redacted
    unknown_event_type = topic == "observability" and event_type.split(".", 1)[0] not in {
        "pipeline",
        "job",
        "system",
        "webhook",
    }
    envelope_metadata = {
        "source": str(safe_metadata.get("source", "bitcoin_bastion")),
        "advisory_only": bool(
            safe_metadata.get("advisory_only", sanitized_payload.get("advisory_only", True))
        ),
        "no_custody": True,
        "degraded": bool(safe_metadata.get("degraded", sanitized_payload.get("degraded", False))),
        "stale": bool(safe_metadata.get("stale", sanitized_payload.get("stale", False))),
        "fallback": bool(safe_metadata.get("fallback", sanitized_payload.get("fallback", False))),
    }
    if redacted:
        envelope_metadata["redacted"] = True
        envelope_metadata["redaction_reason"] = "sensitive_material"
    if unknown_event_type:
        envelope_metadata["unknown_event_type"] = True
    limitations = sanitized_payload.get("limitations", [])
    if not isinstance(limitations, list):
        limitations = [str(limitations)]
    return {
        "type": "event",
        "event_id": event_id,
        "event_type": event_type,
        "domain": domain,
        "topic": topic,
        "version": version,
        "occurred_at": utc_timestamp(occurred_at),
        "published_at": utc_timestamp(),
        "data": sanitized_payload,
        "limitations": limitations,
        "degraded": envelope_metadata["degraded"],
        "stale": envelope_metadata["stale"],
        "payload": sanitized_payload,
        "metadata": envelope_metadata,
    }


def _sanitize_value(value: object, *, key: str | None = None) -> tuple[object, bool]:
    if key is not None and _is_sensitive_text(key):
        return "[REDACTED]", True
    if isinstance(value, str):
        if _is_sensitive_text(value):
            return "[REDACTED]", True
        return value, False
    if isinstance(value, dict):
        redacted = False
        out: dict[str, object] = {}
        for child_key, child_value in value.items():
            safe_value, child_redacted = _sanitize_value(child_value, key=str(child_key))
            out[str(child_key)] = safe_value
            redacted = redacted or child_redacted
        return out, redacted
    if isinstance(value, list):
        redacted = False
        out_list: list[object] = []
        for item in value:
            safe_item, item_redacted = _sanitize_value(item)
            out_list.append(safe_item)
            redacted = redacted or item_redacted
        return out_list, redacted
    return value, False


def _is_sensitive_text(value: str) -> bool:
    normalized = value.casefold().replace("-", "_").strip()
    if normalized in _SECRET_KEYS:
        return True
    lowered = value.casefold()
    return any(term in lowered for term in FORBIDDEN_MATERIAL)
