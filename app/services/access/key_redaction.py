"""Redaction helpers for Access child keys and delegated passes."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

_SECRET_PREFIXES = ("bbk_live_", "bbd_live_")
_FORBIDDEN_PARTS = (
    "raw_child_api_key",
    "raw_delegated_pass",
    "child_key_secret",
    "delegated_pass_token",
    "raw_pass",
    "session_token",
    "recovery_phrase",
    "bitcoin_seed",
    "bitcoin_private_key",
    "private_key",
)


def redact_child_key(raw_key: str) -> str:
    if not raw_key:
        return "<redacted-child-key>"
    if raw_key.startswith("bbk_live_"):
        return "bbk_live_…redacted"
    return "<redacted-child-key>"


def redact_delegated_pass(raw_pass: str) -> str:
    if not raw_pass:
        return "<redacted-delegated-pass>"
    if raw_pass.startswith("bbd_live_"):
        return "bbd_live_…redacted"
    return "<redacted-delegated-pass>"


def assert_no_raw_secret_in_payload(payload: Mapping[str, Any]) -> None:
    _walk(payload)


def _walk(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            lowered = str(key).lower()
            if any(part in lowered for part in _FORBIDDEN_PARTS):
                raise ValueError("raw_child_or_delegated_secret_forbidden")
            _walk(item)
    elif isinstance(value, list | tuple):
        for item in value:
            _walk(item)
    elif isinstance(value, str) and any(prefix in value for prefix in _SECRET_PREFIXES):
        raise ValueError("raw_child_or_delegated_secret_forbidden")
