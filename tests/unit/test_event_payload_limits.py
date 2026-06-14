import pytest

from app.services.events.outbox_service import (
    EventOutboxService,
    EventOutboxValidationError,
    MAX_AGGREGATE_ID_LENGTH,
    MAX_EVENT_PAYLOAD_BYTES,
    MAX_EVENT_TYPE_LENGTH,
    MAX_METADATA_JSON_BYTES,
    MAX_STRING_FIELD_LENGTH,
)


def service() -> EventOutboxService:
    return EventOutboxService.__new__(EventOutboxService)


def test_payload_and_metadata_size_limits_fail_safely() -> None:
    svc = service()
    with pytest.raises(EventOutboxValidationError):
        svc._to_limited_json({"blob": "x" * MAX_EVENT_PAYLOAD_BYTES}, 128, "payload")
    with pytest.raises(EventOutboxValidationError):
        svc._to_limited_json({"blob": "x" * MAX_METADATA_JSON_BYTES}, 128, "metadata")


def test_string_event_type_and_aggregate_limits_are_enforced() -> None:
    svc = service()
    with pytest.raises(EventOutboxValidationError):
        svc._validate_event_type("x" * (MAX_EVENT_TYPE_LENGTH + 1))
    with pytest.raises(EventOutboxValidationError):
        svc._validate_optional_length("x" * (MAX_AGGREGATE_ID_LENGTH + 1), "aggregate_id")
    with pytest.raises(EventOutboxValidationError):
        svc._assert_no_additional_forbidden_values("x" * (MAX_STRING_FIELD_LENGTH + 1))
