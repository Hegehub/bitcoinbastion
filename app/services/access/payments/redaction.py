"""Payment metadata redaction helpers."""

from __future__ import annotations

from typing import Any

_SENSITIVE_METADATA_PARTS = (
    "api_key",
    "apikey",
    "secret",
    "webhook",
    "email",
    "ip",
    "name",
    "address",
    "raw_pass",
    "access_pass",
    "session",
    "recovery",
    "seed",
    "private_key",
)


def redact_payment_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    return {key: _redact_value(key, value) for key, value in metadata.items()}


def _redact_value(key: str, value: Any) -> Any:
    lowered = key.lower()
    if any(part in lowered for part in _SENSITIVE_METADATA_PARTS):
        return "[REDACTED]"
    if isinstance(value, dict):
        return redact_payment_metadata(value)
    if isinstance(value, list):
        return [_redact_value(key, item) for item in value]
    return value
