"""Redis boundary helpers for ephemeral runtime state.

This module intentionally does not create Redis clients or change runtime behavior.
It defines policy constants and small validators so future Redis usage stays within
Bitcoin Bastion's storage architecture: Redis is fast ephemeral infrastructure, not
canonical or durable truth.
"""

from __future__ import annotations

import re

from app.storage.errors import StorageConfigurationError, StorageSafetyError

RATE_LIMIT = "rate"
CHALLENGE = "challenge"
SESSION_HOT = "session_hot"
NONCE = "nonce"
API_RESPONSE_CACHE = "cache"
PROVIDER_POLLING = "provider"
LOCK = "lock"
IDEMPOTENCY = "idempotency"
WEBSOCKET_FANOUT = "fanout"
EVENT_FANOUT = "event_fanout"
CELERY_COORDINATION = "celery"
DEGRADED_COORDINATION = "degraded"

ALLOWED_REDIS_PURPOSES = frozenset(
    {
        RATE_LIMIT,
        CHALLENGE,
        SESSION_HOT,
        NONCE,
        API_RESPONSE_CACHE,
        PROVIDER_POLLING,
        LOCK,
        IDEMPOTENCY,
        WEBSOCKET_FANOUT,
        EVENT_FANOUT,
        CELERY_COORDINATION,
        DEGRADED_COORDINATION,
    }
)

FORBIDDEN_REDIS_PURPOSES = frozenset(
    {
        "access_certificates",
        "subscription_entitlements",
        "access_payment_intents",
        "access_revocations",
        "access_audit_events",
        "recovery_quorums",
        "recovery_attempts",
        "treasury_policies",
        "psbt_workflows",
        "business_roles",
        "proof_packet_metadata",
        "storage_artifacts",
        "issuer_keys",
        "device_keys",
        "private_keys",
        "seed_phrases",
        "wallet_files",
        "xprv",
        "yprv",
        "zprv",
    }
)

DEFAULT_REDIS_TTLS = {
    RATE_LIMIT: 24 * 60 * 60,
    CHALLENGE: 10 * 60,
    SESSION_HOT: 60 * 60,
    NONCE: 2 * 60 * 60,
    API_RESPONSE_CACHE: 5 * 60,
    PROVIDER_POLLING: 24 * 60 * 60,
    LOCK: 60,
    IDEMPOTENCY: 48 * 60 * 60,
    WEBSOCKET_FANOUT: 5 * 60,
    EVENT_FANOUT: 5 * 60,
    CELERY_COORDINATION: 60 * 60,
    DEGRADED_COORDINATION: 15 * 60,
}

REDIS_KEY_PREFIXES = {
    RATE_LIMIT: "rate",
    CHALLENGE: "challenge",
    SESSION_HOT: "session_hot",
    NONCE: "nonce",
    API_RESPONSE_CACHE: "cache",
    PROVIDER_POLLING: "provider",
    LOCK: "lock",
    IDEMPOTENCY: "idempotency",
    WEBSOCKET_FANOUT: "fanout",
    EVENT_FANOUT: "event_fanout",
    CELERY_COORDINATION: "celery",
    DEGRADED_COORDINATION: "degraded",
}

TTL_REQUIRED_PURPOSES = frozenset(
    {
        RATE_LIMIT,
        CHALLENGE,
        SESSION_HOT,
        NONCE,
        LOCK,
        IDEMPOTENCY,
        PROVIDER_POLLING,
        API_RESPONSE_CACHE,
        WEBSOCKET_FANOUT,
        EVENT_FANOUT,
        DEGRADED_COORDINATION,
    }
)

_FORBIDDEN_SENSITIVE_EXAMPLES = (
    "seed phrase",
    "seed_phrase",
    "private key",
    "private_key",
    "wallet.dat",
    "wallet file",
    "wallet_file",
    "xprv",
    "yprv",
    "zprv",
    "mnemonic",
    "raw access pass",
    "access pass token",
    "api key",
    "api_key",
    "raw secret",
)
_SAFE_KEY_PART_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")


def _normalize(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def _contains_forbidden_material(value: str) -> bool:
    normalized = _normalize(value).replace(":", " ")
    return any(term in normalized for term in _FORBIDDEN_SENSITIVE_EXAMPLES)


def validate_redis_purpose(purpose: str) -> None:
    """Validate that a Redis purpose is ephemeral and approved.

    Raises safe-to-log storage exceptions. The caller remains responsible for
    hashing/HMAC-hashing privacy-sensitive identifiers before building keys.
    """

    if not purpose or not purpose.strip():
        raise StorageConfigurationError("Redis purpose must not be empty.")

    normalized = _normalize(purpose)
    if _contains_forbidden_material(normalized) or normalized in FORBIDDEN_REDIS_PURPOSES:
        raise StorageSafetyError(
            f"Redis purpose '{normalized}' is forbidden because Redis is not durable truth."
        )
    if normalized not in ALLOWED_REDIS_PURPOSES:
        raise StorageConfigurationError(f"Redis purpose '{normalized}' is not allowed.")


def require_ttl_for_redis_key(purpose: str, ttl_seconds: int | None) -> None:
    """Require finite positive TTLs for short-lived Redis purposes."""

    validate_redis_purpose(purpose)
    normalized = _normalize(purpose)
    if normalized in TTL_REQUIRED_PURPOSES:
        if ttl_seconds is None:
            raise StorageConfigurationError(f"Redis purpose '{normalized}' requires a TTL.")
        if ttl_seconds <= 0:
            raise StorageConfigurationError(
                f"Redis purpose '{normalized}' requires a positive TTL."
            )


def build_redis_key(env: str, purpose: str, *safe_parts: str) -> str:
    """Build a namespaced Redis key from already-safe/hardened components.

    Key format: ``bb:{env}:{purpose-prefix}:{safe_part}...``.
    The helper rejects empty parts, path separators, whitespace, and obvious
    secret-bearing strings. It does not hash raw identifiers for callers.
    """

    if not env or not env.strip():
        raise StorageConfigurationError("Redis key environment must not be empty.")
    validate_redis_purpose(purpose)
    normalized_purpose = _normalize(purpose)
    normalized_env = _normalize(env)

    parts = ["bb", normalized_env, REDIS_KEY_PREFIXES[normalized_purpose]]
    for part in safe_parts:
        if not part or not part.strip():
            raise StorageConfigurationError("Redis key parts must not be empty.")
        if _contains_forbidden_material(part):
            raise StorageSafetyError("Redis key part contains forbidden sensitive material.")
        if "/" in part or "\\" in part or not _SAFE_KEY_PART_RE.fullmatch(part):
            raise StorageConfigurationError(
                "Redis key parts must be pre-hashed or otherwise safe token strings."
            )
        parts.append(part)
    return ":".join(parts)
