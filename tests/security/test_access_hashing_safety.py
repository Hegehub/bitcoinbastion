from __future__ import annotations

import pytest

from app.services.access.crypto import (
    access_pass_lookup_hash,
    audit_event_hash,
    canonical_json,
    request_digest,
    safe_hash_for_log,
    sha256_prefixed,
)


def test_plain_sha256_is_not_used_as_access_pass_lookup_hash() -> None:
    raw_pass = "bbp_example_not_real"

    assert access_pass_lookup_hash("pepper", raw_pass) != sha256_prefixed(raw_pass)


def test_audit_event_hash_rejects_raw_secret_payloads() -> None:
    for key in ("raw_pass", "session_token", "private_key", "recovery_phrase", "bitcoin_seed"):
        with pytest.raises(ValueError):
            audit_event_hash(None, {"event_type": "unsafe", key: "secret"})


def test_safe_hash_for_log_never_returns_raw_value() -> None:
    hashed = safe_hash_for_log("secret-value")

    assert "secret-value" not in hashed
    assert hashed.startswith("sha256:")


def test_request_digest_is_sensitive_to_all_fields() -> None:
    baseline = request_digest("POST", "/v1/metrics", "bodyhash", "2026-07-01T00:00:00Z", "nonce")

    assert baseline != request_digest("GET", "/v1/metrics", "bodyhash", "2026-07-01T00:00:00Z", "nonce")
    assert baseline != request_digest("POST", "/v1/other", "bodyhash", "2026-07-01T00:00:00Z", "nonce")
    assert baseline != request_digest("POST", "/v1/metrics", "different", "2026-07-01T00:00:00Z", "nonce")
    assert baseline != request_digest("POST", "/v1/metrics", "bodyhash", "2026-07-01T00:00:01Z", "nonce")
    assert baseline != request_digest("POST", "/v1/metrics", "bodyhash", "2026-07-01T00:00:00Z", "other")


def test_canonical_json_rejects_nan() -> None:
    with pytest.raises(ValueError):
        canonical_json({"x": float("nan")})
