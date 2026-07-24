"""Safe Pydantic schemas for LNURL successAction activation UX."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal
from urllib.parse import parse_qs, urlsplit

from pydantic import BaseModel, Field, field_validator

from app.domain.lnurl.success_actions import (
    LNURLActivationPurpose,
    LNURLActivationStatus,
    LNURL_SUCCESS_DESCRIPTION_MAX_LENGTH,
    LNURL_SUCCESS_MESSAGE_MAX_LENGTH,
    contains_forbidden_success_action_secret,
)

_CONTROL_CHARS = frozenset(chr(code) for code in list(range(0, 32)) + [127])
_FORBIDDEN_COMPLETE_KEYS = frozenset({"seed", "mnemonic", "xprv", "private_key", "password", "access_pass", "session_token"})


def _validate_text(value: str, *, field_name: str, max_length: int) -> str:
    text = value.strip()
    if not text:
        raise ValueError(f"{field_name}_required")
    if len(text) > max_length:
        raise ValueError(f"{field_name}_too_long")
    if any(char in _CONTROL_CHARS for char in text):
        raise ValueError(f"{field_name}_contains_control_character")
    if contains_forbidden_success_action_secret(text):
        raise ValueError(f"{field_name}_contains_secret")
    return text


class LNURLMessageSuccessAction(BaseModel):
    model_config = {"extra": "forbid"}

    tag: Literal["message"] = "message"
    message: str = Field(max_length=LNURL_SUCCESS_MESSAGE_MAX_LENGTH)

    @field_validator("message")
    @classmethod
    def validate_message(cls, message: str) -> str:
        return _validate_text(message, field_name="success_action_message", max_length=LNURL_SUCCESS_MESSAGE_MAX_LENGTH)


class LNURLURLSuccessAction(BaseModel):
    model_config = {"extra": "forbid"}

    tag: Literal["url"] = "url"
    description: str = Field(max_length=LNURL_SUCCESS_DESCRIPTION_MAX_LENGTH)
    url: str

    @field_validator("description")
    @classmethod
    def validate_description(cls, description: str) -> str:
        return _validate_text(description, field_name="success_action_description", max_length=LNURL_SUCCESS_DESCRIPTION_MAX_LENGTH)

    @field_validator("url")
    @classmethod
    def validate_url(cls, url: str) -> str:
        parsed = urlsplit(url)
        if parsed.username or parsed.password:
            raise ValueError("success_action_url_credentials_forbidden")
        if parsed.fragment and contains_forbidden_success_action_secret(parsed.fragment):
            raise ValueError("success_action_url_fragment_contains_secret")
        query = parse_qs(parsed.query)
        if contains_forbidden_success_action_secret(url) or any(contains_forbidden_success_action_secret(key) for key in query):
            raise ValueError("success_action_url_contains_secret")
        return url


LNURLSuccessActionResponse = Annotated[LNURLMessageSuccessAction | LNURLURLSuccessAction, Field(discriminator="tag")]


class LNURLActivationStatusResponse(BaseModel):
    model_config = {"extra": "forbid", "use_enum_values": True}

    activation_id: str
    status: LNURLActivationStatus
    purpose: LNURLActivationPurpose
    payment_status: str
    entitlement_status: str | None = None
    ready: bool
    completed: bool
    expires_at: datetime
    safe_next_url: str | None = None
    receipt_reference: str | None = None
    reason_code: str | None = None


class LNURLActivationCompleteRequest(BaseModel):
    model_config = {"extra": "forbid"}

    activation_reference: str | None = Field(default=None)
    expected_purpose: LNURLActivationPurpose
    device_key_fingerprint: str | None = None
    active_pop_session_context: dict[str, Any] | None = None

    @field_validator("activation_reference", "device_key_fingerprint")
    @classmethod
    def validate_no_secret_scalar(cls, value: str | None) -> str | None:
        if value is not None and contains_forbidden_success_action_secret(value):
            raise ValueError("activation_request_contains_secret")
        return value

    @field_validator("active_pop_session_context")
    @classmethod
    def validate_no_forbidden_context(cls, context: dict[str, Any] | None) -> dict[str, Any] | None:
        if not context:
            return context
        for key, value in context.items():
            lowered_key = str(key).lower()
            if lowered_key in _FORBIDDEN_COMPLETE_KEYS or contains_forbidden_success_action_secret(str(value)):
                raise ValueError("activation_request_contains_forbidden_secret")
        return context
