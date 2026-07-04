"""Low-level hashing primitives for Bastion Proof-of-Access Auth.

SHA-256 is used for commitments, fingerprints, request digests, audit hashes,
and other stable digests. HMAC-SHA256 with a server-side pepper is used for
lookup hashes such as Access Pass lookup values. Raw Access Pass values must
never be stored. These helpers are reusable primitives, not a complete
authentication system.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from collections.abc import Mapping
from typing import Any

AUDIT_GENESIS_HASH_INPUT = "bastion-access-audit-genesis"
_SHA256_PREFIX = "sha256"
_HMAC_SHA256_PREFIX = "hmac-sha256"
_FORBIDDEN_SECRET_KEY_PARTS = (
    "password",
    "raw_pass",
    "access_pass",
    "session_token",
    "private_key",
    "seed",
    "recovery_phrase",
    "mnemonic",
    "bitcoin_seed",
    "wallet_seed",
)
_SAFE_SECRET_KEY_NAMES = {
    "pass_lookup_hash",
    "pass_commitment",
    "certificate_fingerprint",
    "device_key_fingerprint",
    "session_hash",
    "nonce_hash",
}


def normalize_bytes(value: bytes | str) -> bytes:
    """Return bytes for byte/string input without silently coercing other types."""

    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8")
    raise TypeError("value must be bytes or str")


def sha256_hex(value: bytes | str) -> str:
    """Return a lowercase SHA-256 hex digest."""

    return hashlib.sha256(normalize_bytes(value)).hexdigest()


def sha256_prefixed(value: bytes | str) -> str:
    """Return a prefixed SHA-256 digest."""

    return f"{_SHA256_PREFIX}:{sha256_hex(value)}"


def hmac_sha256_hex(key: bytes | str, value: bytes | str) -> str:
    """Return a lowercase HMAC-SHA256 hex digest."""

    key_bytes = normalize_bytes(key)
    if not key_bytes:
        raise ValueError("HMAC key must not be empty")
    return hmac.new(key_bytes, normalize_bytes(value), hashlib.sha256).hexdigest()


def hmac_sha256_prefixed(key: bytes | str, value: bytes | str) -> str:
    """Return a prefixed HMAC-SHA256 digest."""

    return f"{_HMAC_SHA256_PREFIX}:{hmac_sha256_hex(key, value)}"


def constant_time_equal(left: str, right: str) -> bool:
    """Strict constant-time string comparison for sensitive digest values."""

    if not isinstance(left, str) or not isinstance(right, str):
        return False
    return hmac.compare_digest(left, right)


def canonical_json(data: Any) -> str:
    """Return deterministic JSON for already JSON-safe values."""

    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def hash_canonical_json(data: Any) -> str:
    """Return SHA-256 hex digest of canonical JSON."""

    return sha256_hex(canonical_json(data))


def hash_canonical_json_prefixed(data: Any) -> str:
    """Return prefixed SHA-256 digest of canonical JSON."""

    return f"{_SHA256_PREFIX}:{hash_canonical_json(data)}"


def secure_token_urlsafe(num_bytes: int = 32) -> str:
    """Generate a cryptographically secure URL-safe token."""

    if num_bytes < 16:
        raise ValueError("num_bytes must be at least 16")
    return secrets.token_urlsafe(num_bytes)


def secure_nonce_hex(num_bytes: int = 16) -> str:
    """Generate a cryptographically secure nonce as lowercase hex."""

    if num_bytes < 16:
        raise ValueError("num_bytes must be at least 16")
    return secrets.token_hex(num_bytes)


def body_hash(body: bytes | str | None) -> str:
    """Return the request body SHA-256 hex digest used for signing."""

    if body is None:
        return sha256_hex(b"")
    return sha256_hex(body)


def access_pass_lookup_hash(server_pepper: str, raw_pass: str) -> str:
    """Return the HMAC-SHA256 lookup hash for an Access Pass."""

    if not server_pepper:
        raise ValueError("server_pepper must not be empty")
    if not raw_pass:
        raise ValueError("raw_pass must not be empty")
    return hmac_sha256_prefixed(server_pepper, raw_pass)


def access_pass_commitment(raw_pass: str) -> str:
    """Return a SHA-256 Access Pass commitment, not a lookup key."""

    if not raw_pass:
        raise ValueError("raw_pass must not be empty")
    return sha256_prefixed(raw_pass)


def certificate_fingerprint(certificate_payload: Mapping[str, Any]) -> str:
    """Return deterministic certificate fingerprint over canonical JSON."""

    return hash_canonical_json_prefixed(certificate_payload)


def request_digest(method: str, path: str, body_hash_hex: str, timestamp: str, nonce: str) -> str:
    """Return request digest for later Proof-of-Possession request signing."""

    _reject_empty_fields(
        method=method,
        path=path,
        body_hash_hex=body_hash_hex,
        timestamp=timestamp,
        nonce=nonce,
    )
    digest_input = "\n".join((method.upper(), path, body_hash_hex, timestamp, nonce))
    return sha256_hex(digest_input)


def audit_event_hash(previous_event_hash: str | None, canonical_event: Mapping[str, Any]) -> str:
    """Return the tamper-evident audit hash for a canonical Access event."""

    reject_forbidden_secret_keys(canonical_event)
    previous = previous_event_hash if previous_event_hash is not None else AUDIT_GENESIS_HASH_INPUT
    return sha256_prefixed(f"{previous}\n{canonical_json(canonical_event)}")


def reject_forbidden_secret_keys(data: Any) -> None:
    """Reject obviously unsafe raw secret keys in nested audit/log payloads."""

    if isinstance(data, Mapping):
        for key, value in data.items():
            key_text = str(key)
            lowered = key_text.lower()
            if lowered not in _SAFE_SECRET_KEY_NAMES and any(
                forbidden in lowered for forbidden in _FORBIDDEN_SECRET_KEY_PARTS
            ):
                raise ValueError(f"Forbidden secret key in Access payload: {key_text}")
            reject_forbidden_secret_keys(value)
    elif isinstance(data, list | tuple):
        for item in data:
            reject_forbidden_secret_keys(item)


def safe_hash_for_log(value: bytes | str, prefix: str = _SHA256_PREFIX) -> str:
    """Return a safe logging fingerprint without exposing the raw value."""

    if prefix != _SHA256_PREFIX:
        raise ValueError("unsupported log hash prefix")
    return sha256_prefixed(value)


def _reject_empty_fields(**fields: str) -> None:
    for name, value in fields.items():
        if not isinstance(value, str):
            raise TypeError(f"{name} must be a string")
        if value == "":
            raise ValueError(f"{name} must not be empty")
