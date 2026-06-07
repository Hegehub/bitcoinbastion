from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

from app.events.safety import SafetyFlag, assert_event_payload_safe
from app.events.types import ActorType, BastionEventType, EventDomain, EventSeverity, EventVisibility


class BastionEventEnvelope(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: BastionEventType
    event_version: int = 1
    domain: EventDomain
    source_module: str
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    aggregate_type: str | None = None
    aggregate_id: str | None = None
    correlation_id: str | None = None
    causation_id: str | None = None
    actor_type: ActorType = ActorType.UNKNOWN
    actor_id: str | None = None
    visibility: EventVisibility = EventVisibility.INTERNAL
    severity: EventSeverity = EventSeverity.INFO
    payload: dict[str, object] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    safety_flags: list[SafetyFlag] = Field(default_factory=list)

    @field_validator("occurred_at")
    @classmethod
    def occurred_at_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("occurred_at must be timezone-aware")
        return value

    @field_validator("event_version")
    @classmethod
    def event_version_must_be_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("event_version must be positive")
        return value

    @model_validator(mode="after")
    def validate_event_contract(self) -> "BastionEventEnvelope":
        assert_event_payload_safe(self.payload)
        if self.event_type.value.startswith("news.event."):
            expected_domain = EventDomain.EVENT
        else:
            domain_name = self.event_type.value.split(".", 1)[0]
            try:
                expected_domain = EventDomain(domain_name)
            except ValueError:
                expected_domain = self.domain
        if self.domain != expected_domain:
            raise ValueError("domain must match event_type")
        return self

    def public_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
