from __future__ import annotations

from collections.abc import Mapping
from typing import Any

SENSITIVE_KEYS = {
    "access_pass",
    "raw_access_pass",
    "bastion_recovery_phrase",
    "recovery_phrase",
    "session_token",
    "x-bastion-session",
    "x-bastion-signature",
    "authorization",
    "api_key",
    "token",
    "secret",
    "signature",
    "private_key",
}

SECRET_PREFIXES = ("bap_", "bbk_live_", "bbd_live_", "xprv", "yprv", "zprv")


def redact_secret(value: Any) -> str:
    text = str(value)
    for prefix in SECRET_PREFIXES:
        if text.startswith(prefix):
            return f"{prefix}…redacted"
    if len(text) <= 8:
        return "<redacted>"
    return f"{text[:4]}…{text[-4:]}"


def redact_mapping(payload: Mapping[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in payload.items():
        lowered = str(key).lower()
        if lowered in SENSITIVE_KEYS or any(
            part in lowered for part in ("token", "secret", "signature", "private_key", "pass")
        ):
            redacted[str(key)] = "<redacted>"
        elif isinstance(value, Mapping):
            redacted[str(key)] = redact_mapping(value)
        elif isinstance(value, list):
            redacted[str(key)] = [redact_mapping(v) if isinstance(v, Mapping) else v for v in value]
        else:
            redacted[str(key)] = value
    return redacted


def assert_no_unredacted_secret(text: str) -> None:
    lowered = text.lower()
    forbidden = (
        "bap_",
        "bbk_live_",
        "bbd_live_",
        "x-bastion-session",
        "x-bastion-signature",
        "private_key",
        "recovery_phrase",
    )
    if any(part in lowered for part in forbidden):
        raise ValueError("unredacted_secret_detected")
