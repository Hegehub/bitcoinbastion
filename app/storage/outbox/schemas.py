from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

from app.storage.outbox.enums import StorageOutboxEventStatus, StorageOutboxTargetStore

_FORBIDDEN_OUTBOX_TERMS = (
    "seed phrase",
    "bitcoin private key",
    "private key",
    "wallet file",
    "wallet.dat",
    "xprv",
    "yprv",
    "zprv",
    "raw secret",
    "raw access token",
    "bearer access pass",
)


def validate_no_sensitive_outbox_material(value: Any, field_name: str) -> Any:
    text = str(value).casefold()
    if any(term in text for term in _FORBIDDEN_OUTBOX_TERMS):
        raise ValueError(f"{field_name} contains forbidden sensitive material")
    return value


class StorageOutboxEventCreate(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=80)
    event_type: str = Field(min_length=1, max_length=160)
    aggregate_type: str = Field(min_length=1, max_length=120)
    aggregate_id: str = Field(min_length=1, max_length=160)
    aggregate_version: int | None = Field(default=None, ge=0)
    payload_json: dict[str, Any] = Field(default_factory=dict)
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    target_stores: list[StorageOutboxTargetStore | str] = Field(min_length=1)
    idempotency_key: str | None = Field(default=None, max_length=200)
    priority: int = Field(default=100, ge=0)
    max_retries: int = Field(default=10, ge=0)
    available_at: datetime | None = None

    @field_validator("event_type", "aggregate_type", "aggregate_id", "idempotency_key")
    @classmethod
    def strip_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be empty")
        validate_no_sensitive_outbox_material(stripped, "storage outbox field")
        return stripped

    @field_validator("target_stores")
    @classmethod
    def normalize_target_stores(cls, value: list[StorageOutboxTargetStore | str]) -> list[str]:
        normalized = [
            item.value if isinstance(item, StorageOutboxTargetStore) else str(item).strip()
            for item in value
        ]
        if not normalized or any(not item for item in normalized):
            raise ValueError("target_stores must contain non-empty values")
        return normalized

    @model_validator(mode="after")
    def reject_sensitive_payloads(self) -> "StorageOutboxEventCreate":
        validate_no_sensitive_outbox_material(self.payload_json, "payload_json")
        validate_no_sensitive_outbox_material(self.metadata_json, "metadata_json")
        return self


class StorageOutboxEventClaim(BaseModel):
    worker_id: str = Field(min_length=1, max_length=160)
    limit: int = Field(default=100, ge=1, le=1000)


class StorageOutboxEventRead(BaseModel):
    id: int
    event_id: str
    event_type: str
    aggregate_type: str
    aggregate_id: str
    aggregate_version: int | None = None
    payload_json: dict[str, Any]
    metadata_json: dict[str, Any]
    target_stores: list[str]
    idempotency_key: str | None = None
    status: StorageOutboxEventStatus | str
    priority: int
    retry_count: int
    max_retries: int
    locked_by: str | None = None
    locked_at: datetime | None = None
    available_at: datetime
    last_error: str | None = None
    processed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StorageOutboxEventResult(BaseModel):
    event_id: str
    status: StorageOutboxEventStatus | str
    retry_count: int
    message: str | None = None
