from collections.abc import Mapping
from datetime import UTC, datetime
from uuid import uuid4

from app.events.serializer import event_payload_hash, normalize_event_value

REDACTED = "[REDACTED]"
_SECRET_METADATA_KEYS = {
    "authorization",
    "auth_header",
    "bearer",
    "bearer_token",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "apikey",
    "api_token",
    "jwt_secret",
    "database_url",
    "provider_credential",
    "secret_key",
    "private_key",
    "password",
}
_SECRET_VALUE_TERMS = (
    "authorization",
    "bearer token",
    "api key",
    "api token",
    "database url",
    "provider credential",
    "secret key",
)


def normalize_source(value: str | None) -> str:
    return (value or "event_bus").strip()[:120] or "event_bus"


def normalize_optional_string(value: str | int | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def sanitize_metadata_value(key: str, value: object) -> object:
    normalized_key = key.casefold().replace("-", "_")
    if normalized_key in _SECRET_METADATA_KEYS:
        return REDACTED
    if isinstance(value, Mapping):
        return {str(k): sanitize_metadata_value(str(k), v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [sanitize_metadata_value(key, item) for item in value]
    if isinstance(value, str):
        lowered = value.casefold()
        if any(term in lowered for term in _SECRET_VALUE_TERMS):
            return REDACTED
    return normalize_event_value(value)


def sanitize_metadata(metadata: Mapping[str, object] | None) -> dict[str, object]:
    return {
        str(key): sanitize_metadata_value(str(key), value)
        for key, value in (metadata or {}).items()
    }


def build_event_metadata(
    *,
    event_type: str,
    event_version: int,
    payload: Mapping[str, object],
    aggregate_type: str | None,
    aggregate_id: str | int | None,
    source: str | None,
    actor_id: str | int | None,
    correlation_id: str | None,
    idempotency_key: str | None,
    metadata: Mapping[str, object] | None,
) -> dict[str, object]:
    normalized = sanitize_metadata(metadata)
    normalized.update(
        {
            "event_type": event_type,
            "event_version": event_version,
            "aggregate_type": aggregate_type,
            "aggregate_id": normalize_optional_string(aggregate_id),
            "source": normalize_source(source),
            "actor_id": normalize_optional_string(actor_id),
            "correlation_id": correlation_id or str(uuid4()),
            "idempotency_key": idempotency_key,
            "created_at": datetime.now(UTC).isoformat(),
            "payload_hash": event_payload_hash(payload),
        }
    )
    return normalized
