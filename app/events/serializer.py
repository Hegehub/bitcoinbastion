import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

JsonPrimitive = str | int | float | bool | None
JsonValue = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]


class EventSerializationError(ValueError):
    pass


def normalize_event_value(value: object) -> JsonValue:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): normalize_event_value(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [normalize_event_value(item) for item in value]
    raise EventSerializationError(f"Unsupported event payload value type: {type(value).__name__}")


def serialize_event_json(data: Mapping[str, object]) -> str:
    normalized = normalize_event_value(data)
    if not isinstance(normalized, dict):
        raise EventSerializationError("event data must serialize to a JSON object")
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def event_payload_hash(data: Mapping[str, object]) -> str:
    serialized = serialize_event_json(data)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
