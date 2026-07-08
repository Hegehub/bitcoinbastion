from __future__ import annotations

from datetime import UTC, datetime, timedelta

from bitcoin_bastion_sdk.access_auth import BastionAccessAuth, body_hash, request_digest
from bitcoin_bastion_sdk.signing import InMemoryDeviceSigner


def _auth() -> BastionAccessAuth:
    return BastionAccessAuth(
        session_token="bap_session_secret",
        session_expires_at=datetime.now(UTC) + timedelta(minutes=5),
        signer=InMemoryDeviceSigner(b"secret"),
    )


def test_body_hash_changes_when_body_changes() -> None:
    assert body_hash({"a": 1}) != body_hash({"a": 2})


def test_signature_changes_when_nonce_changes() -> None:
    auth = _auth()
    first = auth.sign_headers("POST", "/metrics/query", json_body={"a": 1}, nonce="n1")
    second = auth.sign_headers("POST", "/metrics/query", json_body={"a": 1}, nonce="n2")
    assert first["X-Bastion-Signature"] != second["X-Bastion-Signature"]


def test_replayed_nonce_is_not_generated_by_sdk() -> None:
    auth = _auth()
    nonces = {auth.sign_headers("GET", "/access/me")["X-Bastion-Nonce"] for _ in range(20)}
    assert len(nonces) == 20


def test_request_digest_is_stable_for_identical_canonical_input() -> None:
    digest = body_hash({"b": 2, "a": 1})
    assert digest == body_hash({"a": 1, "b": 2})
    assert request_digest(
        "post", "/path", digest, "2026-07-05T00:00:00Z", "nonce"
    ) == request_digest("POST", "/path", digest, "2026-07-05T00:00:00Z", "nonce")


def test_get_with_empty_body_uses_empty_body_hash() -> None:
    headers = _auth().sign_headers("GET", "/access/me", nonce="n")
    assert headers["X-Bastion-Body-Hash"] == body_hash(None)
