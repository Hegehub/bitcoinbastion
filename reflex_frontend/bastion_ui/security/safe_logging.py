from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

REDACTED = "[REDACTED]"
SENSITIVE_KEYWORDS = (
    "seed phrase",
    "mnemonic",
    "private key",
    "xprv",
    "yprv",
    "zprv",
    "wallet.dat",
    "keystore",
    "signing material",
    "authorization header",
    "api key",
    "webhook secret",
    "session token",
    "bearer token",
)
SENSITIVE_KEY_NAMES = {
    "authorization",
    "api_key",
    "apikey",
    "webhook_secret",
    "session_token",
    "token",
    "private_key",
    "mnemonic",
    "seed",
    "seed_phrase",
}
WORD_RE = re.compile(r"\b[a-z]{3,12}\b", re.IGNORECASE)
EXTENDED_KEY_RE = re.compile(r"\b[xyz]prv[1-9A-HJ-NP-Za-km-z]{8,}\b")
BEARER_RE = re.compile(r"\bbearer\s+[A-Za-z0-9._~+/-]+=*", re.IGNORECASE)


def _looks_like_mnemonic(value: str) -> bool:
    words = WORD_RE.findall(value)
    return len(words) in {12, 24} and len(" ".join(words).split()) == len(words)


def redact_sensitive_text(value: str) -> str:
    lowered = value.casefold()
    if any(keyword in lowered for keyword in SENSITIVE_KEYWORDS):
        return REDACTED
    if EXTENDED_KEY_RE.search(value) or BEARER_RE.search(value):
        return REDACTED
    if _looks_like_mnemonic(value):
        return REDACTED
    return value


def redact_payload(payload: Any) -> Any:
    if isinstance(payload, str):
        return redact_sensitive_text(payload)
    if isinstance(payload, Mapping):
        redacted: dict[Any, Any] = {}
        for key, value in payload.items():
            key_text = str(key).casefold().replace("-", "_")
            if key_text in SENSITIVE_KEY_NAMES or any(
                name in key_text for name in SENSITIVE_KEY_NAMES
            ):
                redacted[key] = REDACTED
            else:
                redacted[key] = redact_payload(value)
        return redacted
    if isinstance(payload, Sequence) and not isinstance(payload, bytes | bytearray):
        return [redact_payload(item) for item in payload]
    return payload


def safe_error_message(error: Exception) -> str:
    return redact_sensitive_text(str(error))
