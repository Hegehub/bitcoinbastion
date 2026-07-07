from __future__ import annotations

import hashlib
import hmac

import pytest

from app.services.access.crypto.exceptions import UnsupportedSignatureSuite
from app.services.access.crypto.hashing import (
    AUDIT_GENESIS_HASH_INPUT,
    audit_event_hash,
    body_hash,
    canonical_json,
    constant_time_equal,
    hmac_sha256_prefixed,
    request_digest,
    sha256_hex,
)
from app.services.access.crypto.signatures import SignatureSuiteRegistry


def test_canonical_json_vector_is_stable() -> None:
    payload = {"z": 1, "a": {"b": True, "a": [3, 2, 1]}}

    assert canonical_json(payload) == '{"a":{"a":[3,2,1],"b":true},"z":1}'
    assert sha256_hex(canonical_json(payload)) == hashlib.sha256(
        b'{"a":{"a":[3,2,1],"b":true},"z":1}'
    ).hexdigest()


def test_hmac_lookup_hash_vector_uses_server_pepper() -> None:
    pepper = "test-pepper"
    raw_pass = "bbp_live_test_only"
    expected = hmac.new(pepper.encode(), raw_pass.encode(), hashlib.sha256).hexdigest()

    assert hmac_sha256_prefixed(pepper, raw_pass) == f"hmac-sha256:{expected}"
    assert hmac_sha256_prefixed("different-pepper", raw_pass) != f"hmac-sha256:{expected}"


def test_body_hash_and_request_digest_vectors() -> None:
    body = b'{"hello":"world"}'
    bh = hashlib.sha256(body).hexdigest()
    digest_input = "\n".join(("POST", "/api/v1/access/me", bh, "2026-07-07T00:00:00Z", "nonce-1"))

    assert body_hash(body) == bh
    assert body_hash(None) == hashlib.sha256(b"").hexdigest()
    assert request_digest("post", "/api/v1/access/me", bh, "2026-07-07T00:00:00Z", "nonce-1") == hashlib.sha256(
        digest_input.encode()
    ).hexdigest()


def test_audit_event_hash_chain_vector_and_secret_rejection() -> None:
    canonical_event = {"event_type": "session_created", "session_hash": "hmac-sha256:session"}
    expected = "sha256:" + hashlib.sha256(
        f"{AUDIT_GENESIS_HASH_INPUT}\n{canonical_json(canonical_event)}".encode()
    ).hexdigest()

    assert audit_event_hash(None, canonical_event) == expected
    with pytest.raises(ValueError):
        audit_event_hash(None, {"event_type": "bad", "raw_access_pass": "bbp_live_secret"})


def test_constant_time_compare_behavior() -> None:
    assert constant_time_equal("sha256:a", "sha256:a") is True
    assert constant_time_equal("sha256:a", "sha256:b") is False
    assert constant_time_equal("sha256:a", b"sha256:a") is False  # type: ignore[arg-type]


def test_unsupported_pq_suites_fail_safely() -> None:
    registry = SignatureSuiteRegistry()

    assert registry.supported_algorithms() == ["ed25519"]
    for alg in ["ml_dsa_65", "ml_dsa_87", "slh_dsa", "ml_kem_768"]:
        with pytest.raises(UnsupportedSignatureSuite):
            registry.get(alg)
