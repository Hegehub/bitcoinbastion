from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

SENSITIVE_KEYS = {
    "access_pass",
    "bastion_access_pass",
    "recovery_phrase",
    "session_token",
    "private_key",
    "signature",
    "authorization",
    "x-bastion-session",
    "x-bastion-signature",
    "bastion-request-signature",
    "k1",
    "lnurl_signature",
    "device_private_key",
    "recovery_material",
    "preimage",
    "payerdata",
    "lnurl_linking_key",
    "principal_hash",
}

BITCOIN_SEED_WARNING = (
    "Bastion will never ask for your Bitcoin wallet seed or private key. "
    "Use a Bastion Access Pass only."
)

_WORD_RE = re.compile(r"^[a-z]+(?:\s+[a-z]+){11}(?:\s+[a-z]+){0,12}$", re.IGNORECASE)
_XPRV_RE = re.compile(r"\b[xyz]prv[1-9A-HJ-NP-Za-km-z]+", re.IGNORECASE)
_WIF_RE = re.compile(r"\b[KL5][1-9A-HJ-NP-Za-km-z]{40,}\b")


def redact_long_secret(value: str, prefix: str = "secret") -> str:
    if len(value) <= 8:
        return f"{prefix}_<redacted>"
    return f"{prefix}_{value[:4]}...{value[-4:]}"


def redact_access_pass(value: str) -> str:
    return redact_long_secret(value, "bbp")


def redact_session_token(value: str) -> str:
    return redact_long_secret(value, "sess")


def redact_recovery_phrase(_value: str) -> str:
    return "Bastion Recovery Seed <redacted>"


def redact_signature(value: str) -> str:
    return redact_long_secret(value, "sig")


def looks_like_forbidden_wallet_material(value: str) -> bool:
    text = value.strip()
    if not text:
        return False
    return bool(_XPRV_RE.search(text) or _WIF_RE.search(text) or _WORD_RE.match(text))


def redact_sensitive_object(value: Any) -> Any:
    if isinstance(value, Mapping):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key).lower()
            if any(sensitive in key_text for sensitive in SENSITIVE_KEYS):
                redacted[str(key)] = "<redacted>"
            else:
                redacted[str(key)] = redact_sensitive_object(item)
        return redacted
    if isinstance(value, str):
        if value.startswith("bbp_") or value.startswith("bbk_") or value.startswith("bbd_"):
            return redact_access_pass(value)
        if value.startswith("sess_"):
            return redact_session_token(value)
        if looks_like_forbidden_wallet_material(value):
            return "<rejected-wallet-material>"
        return value
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return [redact_sensitive_object(item) for item in value]
    return value
