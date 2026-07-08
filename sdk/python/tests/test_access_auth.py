from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, cast

import pytest

from bitcoin_bastion_sdk.access_auth import AccessSession, BastionAccessAuth, import_access_pass
from bitcoin_bastion_sdk.errors import BastionAccessSessionExpired, BastionAccessSignatureError
from bitcoin_bastion_sdk.signing import InMemoryDeviceSigner


def _auth() -> BastionAccessAuth:
    return BastionAccessAuth(
        session_token="bap_session_secret",
        session_expires_at=datetime.now(UTC) + timedelta(minutes=5),
        signer=InMemoryDeviceSigner(b"secret"),
    )


def test_access_auth_injects_required_headers() -> None:
    headers = _auth().sign_headers("POST", "/access/me", json_body={"a": 1}, nonce="nonce")
    assert set(headers) == {
        "X-Bastion-Session",
        "X-Bastion-Timestamp",
        "X-Bastion-Nonce",
        "X-Bastion-Body-Hash",
        "X-Bastion-Signature",
    }
    assert headers["X-Bastion-Session"] == "bap_session_secret"
    assert headers["X-Bastion-Nonce"] == "nonce"
    assert headers["X-Bastion-Signature"].startswith("hmac-sha256:")


def test_timestamp_and_nonce_are_generated() -> None:
    headers = _auth().sign_headers("GET", "/access/me")
    assert headers["X-Bastion-Timestamp"].endswith("Z")
    assert len(headers["X-Bastion-Nonce"]) >= 32


def test_session_token_is_redacted_in_repr() -> None:
    session = AccessSession(
        session_token="bap_session_secret",
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
        scopes=["market:intelligence:read"],
        plan_code="pro_pass",
    )
    auth = BastionAccessAuth.from_session(session, signer=InMemoryDeviceSigner(b"secret"))
    assert "bap_session_secret" not in repr(session)
    assert "bap_session_secret" not in repr(auth)


def test_missing_signer_fails_safely() -> None:
    auth = BastionAccessAuth(
        session_token="bap_session_secret",
        session_expires_at=datetime.now(UTC) + timedelta(minutes=5),
        signer=cast(Any, None),
    )
    with pytest.raises(BastionAccessSignatureError):
        auth.sign_headers("GET", "/access/me")


def test_expired_session_fails_safely() -> None:
    auth = BastionAccessAuth(
        session_token="bap_session_secret",
        session_expires_at=datetime.now(UTC) - timedelta(seconds=1),
        signer=InMemoryDeviceSigner(b"secret"),
    )
    with pytest.raises(BastionAccessSessionExpired):
        auth.sign_headers("GET", "/access/me")


def test_import_access_pass_redacts_repr() -> None:
    material = import_access_pass("bap_raw_pass_secret")
    assert material.raw_access_pass == "bap_raw_pass_secret"
    assert "bap_raw_pass_secret" not in repr(material)


def test_challenge_origin_mismatch_fails_safely() -> None:
    from bitcoin_bastion_sdk.access_auth import AccessChallenge

    challenge = AccessChallenge(
        challenge_id="chal_1",
        challenge_payload="payload",
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
        requested_scopes=["market:intelligence:read"],
        origin="https://expected.example",
    )
    with pytest.raises(BastionAccessSignatureError):
        _auth().sign_challenge(challenge, origin="https://evil.example")


def test_expired_challenge_fails_safely() -> None:
    from bitcoin_bastion_sdk.access_auth import AccessChallenge

    challenge = AccessChallenge(
        challenge_id="chal_1",
        challenge_payload="payload",
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
        requested_scopes=["market:intelligence:read"],
        origin="https://app.bitcoinbastion.local",
    )
    with pytest.raises(Exception, match="expired"):
        _auth().sign_challenge(challenge)
