from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

REDACTED = "[REDACTED]"
SENSITIVE_KEY_PARTS = (
    "authorization",
    "api_key",
    "apikey",
    "webhook_secret",
    "secret",
    "session_token",
    "bearer",
    "token",
    "private_key",
    "seed",
    "mnemonic",
    "xprv",
    "yprv",
    "zprv",
    "wallet.dat",
    "keystore",
    "signing_material",
)
SENSITIVE_PATTERNS = (
    re.compile(
        r"\b(seed phrase|mnemonic|private key|wallet\.dat|keystore|signing material)\b", re.I
    ),
    re.compile(r"\b(xprv|yprv|zprv)\S+\b", re.I),
    re.compile(
        r"\b(api key|webhook secret|session token|bearer token|authorization header)\b", re.I
    ),
)
WORD_RE = re.compile(r"\b[a-z]{3,12}\b", re.I)


def _looks_like_mnemonic(value: str) -> bool:
    words = WORD_RE.findall(value)
    return len(words) in {12, 24}


def redact_sensitive_text(value: str) -> str:
    if not value:
        return value
    if _looks_like_mnemonic(value):
        return REDACTED
    redacted = value
    for pattern in SENSITIVE_PATTERNS:
        redacted = pattern.sub(REDACTED, redacted)
    return redacted


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(part in normalized for part in SENSITIVE_KEY_PARTS)


def redact_payload(payload: Any) -> Any:
    if isinstance(payload, str):
        return redact_sensitive_text(payload)
    if isinstance(payload, Mapping):
        return {
            key: REDACTED if _is_sensitive_key(str(key)) else redact_payload(value)
            for key, value in payload.items()
        }
    if isinstance(payload, Sequence) and not isinstance(payload, bytes | bytearray):
        return [redact_payload(item) for item in payload]
    return payload


def safe_error_message(error: Exception) -> str:
    public_message = getattr(error, "public_message", None)
    if isinstance(public_message, str) and public_message:
        return redact_sensitive_text(public_message)
    return redact_sensitive_text(str(error))
