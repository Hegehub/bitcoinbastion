from collections.abc import Mapping
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models.event_outbox import EventOutbox
from app.db.repositories.event_outbox_repository import EventOutboxRepository
from app.events.registry import EVENT_REGISTRY
from app.events.safety import EventPayloadSafetyError, assert_event_payload_safe
from app.events.serializer import EventSerializationError, serialize_event_json
from app.events.types import BastionEventType, EventDomain

MAX_EVENT_PAYLOAD_BYTES = 65_536
MAX_EVENT_METADATA_BYTES = 16_384
MAX_EVENT_TYPE_LENGTH = 128
MAX_AGGREGATE_ID_LENGTH = 128
MAX_STRING_FIELD_LENGTH = 8_192
MAX_PAYLOAD_JSON_BYTES = MAX_EVENT_PAYLOAD_BYTES
MAX_METADATA_JSON_BYTES = MAX_EVENT_METADATA_BYTES
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

_ADDITIONAL_FORBIDDEN_VALUE_TERMS = (
    "authorization",
    "bearer token",
    "api key",
    "api token",
    "database url",
    "provider credential",
    "secret key",
)

_DOMAIN_ALIASES = {
    "signals": EventDomain.SIGNAL.value,
    "provider_health": EventDomain.PROVIDER.value,
    "provider-health": EventDomain.PROVIDER.value,
}


class EventOutboxValidationError(ValueError):
    pass


class EventOutboxService:
    def __init__(self, db: Session) -> None:
        self.repository = EventOutboxRepository(db)

    def record_event(
        self,
        *,
        event_type: str,
        domain: str,
        payload: dict[str, object],
        aggregate_type: str | None = None,
        aggregate_id: str | None = None,
        metadata: dict[str, object] | None = None,
        event_version: int = 1,
        priority: int = 100,
    ) -> EventOutbox:
        normalized_event_type = self._validate_event_type(event_type)
        normalized_domain = self._validate_domain(normalized_event_type, domain)
        self._validate_optional_length(aggregate_type, "aggregate_type")
        self._validate_optional_length(aggregate_id, "aggregate_id")
        safe_payload = dict(payload)
        self._assert_payload_safe(safe_payload)
        safe_metadata = self._sanitize_metadata(metadata or {})
        payload_json = self._to_limited_json(safe_payload, MAX_PAYLOAD_JSON_BYTES, "payload")
        metadata_json = self._to_limited_json(safe_metadata, MAX_METADATA_JSON_BYTES, "metadata")
        return self.repository.create_event(
            event_id=str(uuid4()),
            event_type=normalized_event_type,
            event_version=event_version,
            domain=normalized_domain,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload_json=payload_json,
            metadata_json=metadata_json,
            priority=priority,
        )

    def get_by_event_id(self, event_id: str) -> EventOutbox | None:
        return self.repository.get_by_event_id(event_id)

    def list_pending(self, limit: int = 100) -> list[EventOutbox]:
        return self.repository.list_pending(limit=limit)

    def _validate_optional_length(self, value: str | None, label: str) -> None:
        if value is not None and len(value) > MAX_AGGREGATE_ID_LENGTH:
            raise EventOutboxValidationError(f"{label} exceeds length limit")

    def _validate_event_type(self, event_type: str) -> str:
        if len(event_type) > MAX_EVENT_TYPE_LENGTH:
            raise EventOutboxValidationError("event_type exceeds length limit")
        try:
            parsed = BastionEventType(event_type)
        except ValueError as exc:
            raise EventOutboxValidationError("event_type is not registered") from exc
        if parsed not in EVENT_REGISTRY:
            raise EventOutboxValidationError("event_type is missing registry metadata")
        return parsed.value

    def _validate_domain(self, event_type: str, domain: str) -> str:
        normalized_domain = _DOMAIN_ALIASES.get(domain, domain)
        try:
            parsed_domain = EventDomain(normalized_domain)
        except ValueError as exc:
            raise EventOutboxValidationError("domain is not registered") from exc
        metadata = EVENT_REGISTRY[BastionEventType(event_type)]
        if metadata.domain != parsed_domain:
            raise EventOutboxValidationError("domain does not match event_type registry metadata")
        return parsed_domain.value

    def _assert_payload_safe(self, payload: Mapping[str, object]) -> None:
        try:
            assert_event_payload_safe(payload)
        except EventPayloadSafetyError as exc:
            raise EventOutboxValidationError(str(exc)) from exc
        self._assert_no_additional_forbidden_values(payload)

    def _assert_no_additional_forbidden_values(self, value: object) -> None:
        if isinstance(value, str):
            if len(value) > MAX_STRING_FIELD_LENGTH:
                raise EventOutboxValidationError("event payload string field exceeds length limit")
            lowered = value.casefold()
            for term in _ADDITIONAL_FORBIDDEN_VALUE_TERMS:
                if term in lowered:
                    raise EventOutboxValidationError("event payload contains secret-like material")
            return
        if isinstance(value, Mapping):
            for key, child in value.items():
                self._assert_no_additional_forbidden_values(str(key))
                self._assert_no_additional_forbidden_values(child)
            return
        if isinstance(value, (list, tuple, set, frozenset)):
            for child in value:
                self._assert_no_additional_forbidden_values(child)

    def _sanitize_metadata(self, metadata: Mapping[str, object]) -> dict[str, object]:
        return {
            str(key): self._sanitize_metadata_value(str(key), value)
            for key, value in metadata.items()
        }

    def _sanitize_metadata_value(self, key: str, value: object) -> object:
        normalized_key = key.casefold().replace("-", "_")
        if normalized_key in _SECRET_METADATA_KEYS:
            return REDACTED
        if isinstance(value, Mapping):
            return {str(k): self._sanitize_metadata_value(str(k), v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._sanitize_metadata_value(key, item) for item in value]
        if isinstance(value, tuple):
            return [self._sanitize_metadata_value(key, item) for item in value]
        if isinstance(value, str):
            if len(value) > MAX_STRING_FIELD_LENGTH:
                raise EventOutboxValidationError("event payload string field exceeds length limit")
            lowered = value.casefold()
            if any(term in lowered for term in _ADDITIONAL_FORBIDDEN_VALUE_TERMS):
                return REDACTED
        return value

    def _to_limited_json(self, data: Mapping[str, object], max_bytes: int, label: str) -> str:
        try:
            encoded = serialize_event_json(data)
        except EventSerializationError as exc:
            raise EventOutboxValidationError(str(exc)) from exc
        if len(encoded.encode("utf-8")) > max_bytes:
            raise EventOutboxValidationError(f"event {label} exceeds size limit")
        return encoded
