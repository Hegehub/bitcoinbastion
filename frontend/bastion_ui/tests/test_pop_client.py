from datetime import UTC, datetime, timedelta

import pytest

from bastion_ui.auth_models import PopSessionMetadata
from bastion_ui.pop_client import PopApiClient, canonical_body, canonical_query, signing_digest


class Signer:
    def __init__(self) -> None:
        self.digests: list[bytes] = []

    def sign(self, digest: bytes) -> str:
        self.digests.append(digest)
        return digest.hex()


def test_canonical_vector_and_fresh_nonce() -> None:
    body = canonical_body({"plan": "pro_pass", "scopes": ["market:intelligence:read"]})
    assert body.decode() == '{"plan":"pro_pass","scopes":["market:intelligence:read"]}'
    assert canonical_query({"z": "two words", "a": "1"}) == "a=1&z=two%20words"
    assert (
        signing_digest(
            "POST",
            "/api/v1/wallet-auth/me",
            {"z": "two words", "a": "1"},
            body,
            "2026-08-02T12:00:00Z",
            "00112233445566778899aabbccddeeff",
        ).hex()
        == "072fa3fe6de9283ece17a9b52f8613b7f86e04804347a01a334c52a2ce0f0527"
    )


def test_expired_session_requires_reauthentication() -> None:
    client = PopApiClient(
        "https://example.test",
        PopSessionMetadata(
            "sess_secret", "principal", (datetime.now(UTC) - timedelta(seconds=1)).isoformat(), ()
        ),
        Signer(),
    )
    with pytest.raises(RuntimeError, match="session_expired"):
        client.request("GET", "/api/v1/wallet-auth/me")
