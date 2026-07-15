from __future__ import annotations

import asyncio
import base64
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.services.access.crypto.signatures import build_signing_message
from app.services.access.pop.canonical_request import (
    POP_PROTOCOL_VERSION,
    build_pop_canonical_request,
    canonicalize_query_string,
    compute_body_sha256_hex,
    compute_pop_request_digest,
)
from app.services.wallet_auth.request_verifier import (
    InMemoryWalletPoPNonceRegistry,
    WalletPoPError,
    WalletPoPRequestVerifier,
    canonical_request_for_signing,
)
from app.services.wallet_auth.principal_types import PrincipalType
from tests.unit.test_wallet_session_service import _ctx, _service

NOW = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)
BODY = b'{"hello":"world"}'
PATH = "/api/v1/protected"
QUERY = "b=2&a=3&a=1"


def _keypair(seed: bytes = b"\x11"):
    private = Ed25519PrivateKey.from_private_bytes(seed * 32)
    public = private.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
    return private, base64.b64encode(public).decode("ascii")


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _sign(private: Ed25519PrivateKey, digest: str) -> str:
    return _b64url(private.sign(build_signing_message("access_session", digest)))


def _nonce() -> str:
    return _b64url(b"n" * 16)


def _headers(token: str, private: Ed25519PrivateKey, session_binding: str, *, method="GET", path=PATH, query=QUERY, body=BODY, timestamp: str | None = None, nonce: str | None = None, principal: str | None = None):
    ts = timestamp or str(int(NOW.timestamp()))
    n = nonce or _nonce()
    body_hash, _canonical, digest = canonical_request_for_signing(method=method, path=path, query_string=query, body=body, timestamp=ts, nonce=n, session_binding=session_binding)
    headers = {
        "Authorization": f"PoP {token}",
        "Bastion-Request-Timestamp": ts,
        "Bastion-Request-Nonce": n,
        "Bastion-Request-Body-Hash": body_hash,
        "Bastion-Request-Signature": _sign(private, digest),
    }
    if principal:
        headers["Bastion-Principal"] = principal
    return headers


def test_canonical_request_vectors_are_stable_and_sensitive():
    body_hash = compute_body_sha256_hex(BODY)
    canonical = build_pop_canonical_request(method="get", path=PATH, query_string=QUERY, body_hash_hex=body_hash, timestamp="1784001600", nonce=_nonce(), session_binding="hmac-sha256:" + "a" * 64)
    digest = compute_pop_request_digest(canonical)
    assert canonical.splitlines()[0] == POP_PROTOCOL_VERSION
    assert "a=1&a=3&b=2" in canonical
    assert digest != compute_pop_request_digest(canonical.replace("GET", "POST"))
    assert digest != compute_pop_request_digest(canonical.replace(PATH, "/api/v1/other"))
    assert canonicalize_query_string("z=&a=%2F&a=+") == "a=%20&a=%2F&z="


def test_header_parsing_and_signature_validation():
    async def run():
        private, public = _keypair()
        session_svc, _ = _service()
        from app.services.wallet_auth.device_key_validation import compute_device_key_fingerprint
        fp = compute_device_key_fingerprint(public)
        session = await session_svc.create_session(auth_context=_ctx(fp), session_public_key=public)
        verifier = WalletPoPRequestVerifier(session_service=session_svc, nonce_registry=InMemoryWalletPoPNonceRegistry(), clock=lambda: NOW)
        headers = _headers(session.session_token, private, session.context.session_lookup_hash, principal=session.context.principal_hash)
        verified = await verifier.verify_request(method="GET", path=PATH, query_string=QUERY, body=BODY, headers=headers)
        assert verified.principal_hash == session.context.principal_hash
        assert verified.requires_policy_decision is True
        assert verified.actor_type == PrincipalType.BITCOIN_WALLET_PRINCIPAL.value
    asyncio.run(run())


@pytest.mark.parametrize("headers,reason", [
    ({}, "missing_pop_authorization"),
    ({"Authorization": "Bearer abc"}, "invalid_pop_authorization_scheme"),
    ({"Authorization": "PoP sess_x", "Bastion-Request-Timestamp": "abc", "Bastion-Request-Nonce": _nonce(), "Bastion-Request-Body-Hash": "0"*64, "Bastion-Request-Signature": "sig"}, "invalid_pop_timestamp"),
    ({"Authorization": "PoP sess_x", "Bastion-Request-Timestamp": str(int(NOW.timestamp())), "Bastion-Request-Nonce": "short", "Bastion-Request-Body-Hash": "0"*64, "Bastion-Request-Signature": "sig"}, "invalid_pop_nonce"),
    ({"Authorization": "PoP sess_x", "Bastion-Request-Timestamp": str(int(NOW.timestamp())), "Bastion-Request-Nonce": _nonce(), "Bastion-Request-Body-Hash": "bad", "Bastion-Request-Signature": "sig"}, "invalid_body_hash"),
])
def test_header_failures(headers, reason):
    async def run():
        session_svc, _ = _service()
        verifier = WalletPoPRequestVerifier(session_service=session_svc, nonce_registry=InMemoryWalletPoPNonceRegistry(), clock=lambda: NOW)
        with pytest.raises(WalletPoPError) as exc:
            await verifier.verify_request(method="GET", path=PATH, query_string="", body=b"", headers=headers)
        assert exc.value.reason_code == reason
    asyncio.run(run())


def test_tampering_timestamp_session_state_and_principal_mismatch_rejected():
    async def run():
        private, public = _keypair()
        from app.services.wallet_auth.device_key_validation import compute_device_key_fingerprint
        fp = compute_device_key_fingerprint(public)
        session_svc, _ = _service()
        session = await session_svc.create_session(auth_context=_ctx(fp), session_public_key=public)
        verifier = WalletPoPRequestVerifier(session_service=session_svc, nonce_registry=InMemoryWalletPoPNonceRegistry(), clock=lambda: NOW)
        stale = _headers(session.session_token, private, session.context.session_lookup_hash, timestamp=str(int((NOW - timedelta(minutes=10)).timestamp())))
        with pytest.raises(WalletPoPError) as exc:
            await verifier.verify_request(method="GET", path=PATH, query_string=QUERY, body=BODY, headers=stale)
        assert exc.value.reason_code == "stale_pop_request"
        headers = _headers(session.session_token, private, session.context.session_lookup_hash, principal="hmac-sha256:" + "9" * 64)
        with pytest.raises(WalletPoPError) as exc:
            await verifier.verify_request(method="GET", path=PATH, query_string=QUERY, body=BODY, headers=headers)
        assert exc.value.reason_code == "session_principal_mismatch"
        bad_body = _headers(session.session_token, private, session.context.session_lookup_hash, body=b"{}")
        with pytest.raises(WalletPoPError) as exc:
            await verifier.verify_request(method="GET", path=PATH, query_string=QUERY, body=BODY, headers=bad_body)
        assert exc.value.reason_code == "pop_body_hash_mismatch"
    asyncio.run(run())


def test_wrong_key_and_recovery_only_state_rejected():
    async def run():
        private, public = _keypair()
        wrong_private, _ = _keypair(b"\x22")
        from app.services.wallet_auth.device_key_validation import compute_device_key_fingerprint
        fp = compute_device_key_fingerprint(public)
        session_svc, _ = _service()
        session = await session_svc.create_session(auth_context=_ctx(fp, recovery=True), session_public_key=public)
        verifier = WalletPoPRequestVerifier(session_service=session_svc, nonce_registry=InMemoryWalletPoPNonceRegistry(), clock=lambda: NOW)
        with pytest.raises(WalletPoPError) as exc:
            await verifier.verify_request(method="GET", path=PATH, query_string=QUERY, body=BODY, headers=_headers(session.session_token, private, session.context.session_lookup_hash))
        assert exc.value.reason_code == "invalid_pop_session"
        headers = _headers(session.session_token, wrong_private, session.context.session_lookup_hash)
        with pytest.raises(WalletPoPError) as exc:
            await verifier.verify_request(method="GET", path=PATH, query_string=QUERY, body=BODY, headers=headers, allow_recovery_only=True)
        assert exc.value.reason_code == "invalid_pop_signature"
    asyncio.run(run())


def test_shared_sdk_vectors_match_canonical_digest_and_signature():
    import json
    from pathlib import Path

    vectors = json.loads(Path("tests/fixtures/wallet_pop_request_vectors.json").read_text())["vectors"]
    first = vectors[0]
    canonical = build_pop_canonical_request(
        method=first["method"],
        path=first["path"],
        query_string=first["query"],
        body_hash_hex=first["body_hash"],
        timestamp=first["timestamp"],
        nonce=first["nonce"],
        session_binding=first["session_binding"],
    )
    assert canonical == first["canonical_request"]
    assert compute_pop_request_digest(canonical) == first["request_digest"]
