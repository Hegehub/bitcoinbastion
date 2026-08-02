from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx

from bitcoin_bastion_sdk import BastionClient
from bitcoin_bastion_sdk.access import BastionPoPSession, InMemoryDeviceSigner
from bitcoin_bastion_sdk.access.request_signing import canonical_json_bytes, canonical_target, hash_body, request_digest


def session() -> BastionPoPSession:
    signer = InMemoryDeviceSigner(b"d" * 32)
    return BastionPoPSession(token="sess_raw_secret", principal="wpr_safe", device_fingerprint=signer.fingerprint, expires_at=datetime.now(UTC) + timedelta(minutes=5), signer=signer)


def test_contract_vector_matches_backend_canonicalization() -> None:
    fixture = json.loads((Path(__file__).parents[3] / "artifacts" / "wallet_auth_sdk_contract.json").read_text())["test_vector"]
    body = canonical_json_bytes({"plan": "pro_pass", "scopes": ["market:intelligence:read"]})
    target = canonical_target(fixture["path"], [tuple(item) for item in fixture["query"]])
    assert body.decode() == fixture["canonical_body"]
    assert hash_body(body) == fixture["body_sha256"]
    assert request_digest(fixture["method"], target, hash_body(body), fixture["timestamp"], fixture["nonce"]).hex() == fixture["digest_hex"]


def test_transport_uses_canonical_headers_and_fresh_nonce_per_request() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"data": {"ok": True}, "error": None, "meta": {}})

    client = BastionClient(base_url="http://example.com", pop_session=session(), transport=httpx.MockTransport(handler))
    client.auth.wallet.get_principal()
    client.auth.wallet.get_principal()
    assert all(request.headers["authorization"] == "PoP sess_raw_secret" for request in requests)
    assert requests[0].headers["bastion-request-nonce"] != requests[1].headers["bastion-request-nonce"]
    assert "x-bastion-session" not in requests[0].headers
    assert "sess_raw_secret" not in repr(client._transport.pop_session)
