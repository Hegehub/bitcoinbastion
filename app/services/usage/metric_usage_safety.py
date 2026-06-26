from __future__ import annotations

from typing import Any

FORBIDDEN_USAGE_TERMS = (
    "seed",
    "seed_phrase",
    "mnemonic",
    "private_key",
    "private key",
    "xprv",
    "yprv",
    "zprv",
    "wallet_file",
    "wallet.dat",
    "password",
    "raw_token",
    "api_key",
    "access_token",
    "session_token",
    "authorization",
    "bearer",
    "secret",
)

PRIVACY_HASH_FIELDS = (
    "pass_lookup_hash",
    "workspace_id_hash",
    "api_key_hash",
    "session_id_hash",
)


def normalize_label(value: str | None, field_name: str, *, max_length: int = 120) -> str | None:
    if value is None:
        return None
    cleaned = value.strip().lower().replace(" ", "_")
    if not cleaned:
        return None
    if len(cleaned) > max_length:
        raise ValueError(f"{field_name} must be {max_length} characters or fewer")
    if any(term in cleaned for term in FORBIDDEN_USAGE_TERMS):
        raise ValueError(f"{field_name} contains sensitive material")
    return cleaned


def require_label(value: str | None, field_name: str, *, max_length: int = 120) -> str:
    cleaned = normalize_label(value, field_name, max_length=max_length)
    if cleaned is None:
        raise ValueError(f"{field_name} is required")
    return cleaned


def validate_safe_hash(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    lowered = cleaned.lower()
    if any(term in lowered for term in FORBIDDEN_USAGE_TERMS):
        raise ValueError(f"{field_name} contains sensitive material")
    if "@" in cleaned or "://" in cleaned:
        raise ValueError(f"{field_name} must be a privacy-safe hash or fingerprint")
    if len(cleaned) > 128:
        raise ValueError(f"{field_name} must be 128 characters or fewer")
    return cleaned


def validate_usage_metadata(value: Any, path: str = "metadata_json") -> None:
    if value is None:
        return
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key).lower()
            if any(term in key_text for term in FORBIDDEN_USAGE_TERMS):
                raise ValueError(f"{path}.{key} contains sensitive usage metadata")
            validate_usage_metadata(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            validate_usage_metadata(item, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if any(term in lowered for term in FORBIDDEN_USAGE_TERMS):
            raise ValueError(f"{path} contains sensitive usage metadata")
