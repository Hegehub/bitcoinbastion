from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class WebhookEndpointCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    target_url: str = Field(min_length=8, max_length=2048)
    description: str | None = Field(default=None, max_length=2000)
    event_types: list[str] = Field(min_length=1)
    metadata: dict[str, object] | None = None

    @field_validator("event_types")
    @classmethod
    def event_types_non_empty_strings(cls, value: list[str]) -> list[str]:
        normalized = [item.strip() for item in value]
        if not normalized or any(not item for item in normalized):
            raise ValueError("event_types must contain non-empty event type names")
        return normalized


class WebhookEndpointUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    target_url: str | None = Field(default=None, min_length=8, max_length=2048)
    description: str | None = Field(default=None, max_length=2000)
    enabled: bool | None = None
    event_types: list[str] | None = None
    metadata: dict[str, object] | None = None

    @field_validator("event_types")
    @classmethod
    def optional_event_types_non_empty_strings(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        normalized = [item.strip() for item in value]
        if any(not item for item in normalized):
            raise ValueError("event_types must contain non-empty event type names")
        return normalized


class WebhookSubscriptionCreate(BaseModel):
    event_type: str = Field(min_length=1, max_length=160)


class WebhookSubscriptionOut(BaseModel):
    id: int
    webhook_endpoint_id: int
    event_type: str
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WebhookEndpointOut(BaseModel):
    id: int
    name: str
    target_url: str
    description: str | None = None
    enabled: bool
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime
    last_delivery_at: datetime | None = None
    failure_count: int
    status: str
    secret_ref: str
    secret_available: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    subscriptions: list[WebhookSubscriptionOut] = Field(default_factory=list)


class WebhookDeliveryOut(BaseModel):
    id: int
    delivery_id: str
    event_type: str
    status: str
    attempt_count: int
    attempt_number: int = 1
    response_status_code: int | None = None
    error_message: str | None = None
    duration_ms: int | None = None
    request_body_hash: str | None = None
    created_at: datetime
    next_attempt_at: datetime | None = None
    next_retry_at: datetime | None = None
    delivered_at: datetime | None = None

    model_config = {"from_attributes": True}


class WebhookTestRequest(BaseModel):
    event_type: str | None = Field(default=None, max_length=160)
    payload: dict[str, object] | None = None


class WebhookTestResponse(BaseModel):
    delivery_id: str
    status: str
    event_type: str
    network_delivery_attempted: bool = False
    headers: dict[str, str] = Field(default_factory=dict)
    request_body_hash: str | None = None
