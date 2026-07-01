"""Issuer key loading helpers for Bastion Proof-of-Access Auth."""

from __future__ import annotations

import os

from app.services.access.crypto.exceptions import MissingIssuerKey, UnsafeKeyMaterialError

_UNSAFE_PLACEHOLDER_VALUES = {
    "changeme",
    "change_me",
    "secret",
    "test",
    "dev",
    "password",
    "private_key",
    "replace_me",
    "replaceme",
}
_UNSAFE_KEY_FRAGMENTS = (
    "bitcoin_seed",
    "wallet_seed",
    "recovery_phrase",
    "mnemonic",
    "xprv",
    "yprv",
    "zprv",
)


def load_issuer_private_key_from_env(env_var: str = "ACCESS_ISSUER_PRIVATE_KEY") -> str:
    """Load issuer private-key material from an environment variable."""

    value = os.getenv(env_var)
    if value is None or value.strip() == "":
        raise MissingIssuerKey(f"Required issuer private key environment variable is missing: {env_var}")
    validate_key_material_is_not_placeholder(value)
    return value


def load_issuer_key_id_from_env(env_var: str = "ACCESS_ISSUER_KEY_ID") -> str:
    """Load stable non-secret issuer key id from an environment variable."""

    value = os.getenv(env_var)
    if value is None or value.strip() == "":
        raise MissingIssuerKey(f"Required issuer key id environment variable is missing: {env_var}")
    return value.strip()


def validate_issuer_key_config(private_key: str, key_id: str) -> None:
    """Validate required issuer private key and key id without exposing secret values."""

    if not private_key or private_key.strip() == "":
        raise MissingIssuerKey("Issuer private key is required")
    if not key_id or key_id.strip() == "":
        raise MissingIssuerKey("Issuer key id is required")
    validate_key_material_is_not_placeholder(private_key)


def validate_key_material_is_not_placeholder(key_material: str | bytes) -> None:
    """Reject placeholders and obvious non-Access wallet/recovery material."""

    if isinstance(key_material, bytes):
        lowered = key_material.decode("utf-8", errors="ignore").strip().lower()
    else:
        lowered = key_material.strip().lower()
    if lowered in _UNSAFE_PLACEHOLDER_VALUES:
        raise UnsafeKeyMaterialError("Unsafe placeholder key material is not allowed")
    if any(fragment in lowered for fragment in _UNSAFE_KEY_FRAGMENTS):
        raise UnsafeKeyMaterialError("Unsafe non-issuer key material is not allowed")
