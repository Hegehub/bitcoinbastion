from __future__ import annotations

import pytest

from app.services.access.crypto import (
    access_pass_commitment,
    access_pass_lookup_hash,
    audit_event_hash,
    body_hash,
    canonical_json,
    certificate_fingerprint,
    constant_time_equal,
    hash_canonical_json,
    hmac_sha256_hex,
    reject_forbidden_secret_keys,
    request_digest,
    secure_nonce_hex,
    secure_token_urlsafe,
    sha256_hex,
)


def test_sha256_hex_is_deterministic_for_str_and_bytes() -> None:
    assert sha256_hex("bastion") == sha256_hex("bastion")
    assert sha256_hex("bastion") == sha256_hex(b"bastion")


def test_hmac_sha256_hex_differs_from_plain_sha256() -> None:
    assert hmac_sha256_hex("pepper", "pass") != sha256_hex("pass")


def test_access_pass_lookup_hash_uses_hmac_prefix() -> None:
    lookup = access_pass_lookup_hash("pepper", "pass")

    assert lookup.startswith("hmac-sha256:")
    assert lookup == access_pass_lookup_hash("pepper", "pass")
    assert lookup != access_pass_lookup_hash("different-pepper", "pass")
    assert lookup != access_pass_lookup_hash("pepper", "different-pass")


def test_access_pass_commitment_uses_sha_prefix_and_differs_from_lookup() -> None:
    commitment = access_pass_commitment("pass")

    assert commitment.startswith("sha256:")
    assert commitment != access_pass_lookup_hash("pepper", "pass")


def test_canonical_json_is_stable() -> None:
    assert canonical_json({"b": 2, "a": 1}) == canonical_json({"a": 1, "b": 2})
    assert canonical_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'


def test_hash_canonical_json_is_stable() -> None:
    assert hash_canonical_json({"b": 2, "a": 1}) == hash_canonical_json({"a": 1, "b": 2})


def test_certificate_fingerprint_is_stable() -> None:
    left = certificate_fingerprint({"plan": "pro_pass", "scopes": ["trace:advanced:read"]})
    right = certificate_fingerprint({"scopes": ["trace:advanced:read"], "plan": "pro_pass"})

    assert left == right
    assert left.startswith("sha256:")


def test_secure_token_urlsafe_generates_distinct_tokens_and_rejects_small_size() -> None:
    assert secure_token_urlsafe() != secure_token_urlsafe()
    with pytest.raises(ValueError):
        secure_token_urlsafe(15)


def test_secure_nonce_hex_generates_distinct_nonces_and_rejects_small_size() -> None:
    assert secure_nonce_hex() != secure_nonce_hex()
    with pytest.raises(ValueError):
        secure_nonce_hex(15)


def test_request_digest_normalizes_method_and_is_sensitive_to_nonce_and_body_hash() -> None:
    digest = request_digest("get", "/v1/metrics", "bodyhash", "2026-07-01T00:00:00Z", "nonce")

    assert digest == request_digest("GET", "/v1/metrics", "bodyhash", "2026-07-01T00:00:00Z", "nonce")
    assert digest != request_digest("GET", "/v1/metrics", "bodyhash", "2026-07-01T00:00:00Z", "different")
    assert digest != request_digest("GET", "/v1/metrics", "different", "2026-07-01T00:00:00Z", "nonce")
    with pytest.raises(ValueError):
        request_digest("", "/v1/metrics", "bodyhash", "2026-07-01T00:00:00Z", "nonce")
    with pytest.raises(ValueError):
        request_digest("GET", "", "bodyhash", "2026-07-01T00:00:00Z", "nonce")
    with pytest.raises(ValueError):
        request_digest("GET", "/v1/metrics", "", "2026-07-01T00:00:00Z", "nonce")
    with pytest.raises(ValueError):
        request_digest("GET", "/v1/metrics", "bodyhash", "", "nonce")
    with pytest.raises(ValueError):
        request_digest("GET", "/v1/metrics", "bodyhash", "2026-07-01T00:00:00Z", "")


def test_body_hash_hashes_none_as_empty_bytes_and_matches_equivalent_bytes_and_string() -> None:
    assert body_hash(None) == sha256_hex(b"")
    assert body_hash("body") == body_hash(b"body")


def test_constant_time_equal_is_strict() -> None:
    assert constant_time_equal("abc", "abc") is True
    assert constant_time_equal("abc", "ABC") is False
    assert constant_time_equal("abc", 123) is False  # type: ignore[arg-type]


def test_audit_event_hash_is_deterministic_and_chain_sensitive() -> None:
    event = {"event_type": "access.session.created", "session_hash": "session_hash_example"}
    event_hash = audit_event_hash("sha256:previous", event)

    assert event_hash == audit_event_hash("sha256:previous", {"session_hash": "session_hash_example", "event_type": "access.session.created"})
    assert event_hash != audit_event_hash("sha256:previous", {"event_type": "access.session.revoked", "session_hash": "session_hash_example"})
    assert event_hash != audit_event_hash("sha256:different", event)


def test_reject_forbidden_secret_keys_blocks_raw_secret_names_but_allows_safe_hash_names() -> None:
    for key in ("raw_pass", "password", "private_key", "recovery_phrase", "bitcoin_seed"):
        with pytest.raises(ValueError):
            reject_forbidden_secret_keys({key: "secret"})

    reject_forbidden_secret_keys(
        {
            "pass_lookup_hash": "hmac-sha256:example",
            "certificate_fingerprint": "sha256:example",
            "device_key_fingerprint": "sha256:example",
        }
    )
