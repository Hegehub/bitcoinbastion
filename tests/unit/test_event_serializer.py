from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest

from app.events.serializer import EventSerializationError, event_payload_hash, serialize_event_json


def test_payload_is_serialized_deterministically() -> None:
    left = {"b": 2, "a": {"d": 4, "c": 3}}
    right = {"a": {"c": 3, "d": 4}, "b": 2}

    assert serialize_event_json(left) == serialize_event_json(right)
    assert serialize_event_json(left) == '{"a":{"c":3,"d":4},"b":2}'


def test_payload_hash_is_stable_for_same_payload() -> None:
    first = event_payload_hash({"signal_id": 123, "confidence": Decimal("0.72")})
    second = event_payload_hash({"confidence": Decimal("0.72"), "signal_id": 123})

    assert first == second


def test_serializer_handles_datetime_uuid_and_decimal() -> None:
    serialized = serialize_event_json(
        {
            "occurred_at": datetime(2026, 6, 7, 12, 0, tzinfo=UTC),
            "uuid": UUID("00000000-0000-0000-0000-000000000001"),
            "amount": Decimal("1.23"),
        }
    )

    assert "2026-06-07T12:00:00+00:00" in serialized
    assert "00000000-0000-0000-0000-000000000001" in serialized
    assert '"1.23"' in serialized


def test_serializer_fails_on_unsupported_objects() -> None:
    with pytest.raises(EventSerializationError):
        serialize_event_json({"unsupported": object()})
