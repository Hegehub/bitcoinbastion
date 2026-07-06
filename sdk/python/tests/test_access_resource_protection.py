from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import pytest

from bitcoin_bastion_sdk import BastionClient
from bitcoin_bastion_sdk.access_auth import BastionAccessAuth
from bitcoin_bastion_sdk.errors import BastionAccessError
from bitcoin_bastion_sdk.signing import InMemoryDeviceSigner


def _auth() -> BastionAccessAuth:
    return BastionAccessAuth(
        session_token="bap_session_secret",
        session_expires_at=datetime.now(UTC) + timedelta(minutes=5),
        signer=InMemoryDeviceSigner(b"secret"),
    )


def test_protected_method_without_auth_raises_sdk_error() -> None:
    client = BastionClient(
        base_url="http://example.com",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={})),
    )
    with pytest.raises(BastionAccessError):
        client.access.me()


def test_public_method_works_without_auth(captured_requests: list[httpx.Request]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(200, json={"data": {"ok": True}, "error": None, "meta": {}})

    client = BastionClient(base_url="http://example.com", transport=httpx.MockTransport(handler))
    assert client.health.public_status() == {"ok": True}
    assert "x-bastion-session" not in captured_requests[0].headers


def test_protected_method_with_access_auth_signs_request(
    captured_requests: list[httpx.Request],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(200, json={"data": {"ok": True}, "error": None, "meta": {}})

    client = BastionClient(
        base_url="http://example.com", access_auth=_auth(), transport=httpx.MockTransport(handler)
    )
    assert client.access.me() == {"ok": True}
    request = captured_requests[0]
    assert request.headers["x-bastion-session"] == "bap_session_secret"
    assert request.headers["x-bastion-signature"].startswith("hmac-sha256:")
