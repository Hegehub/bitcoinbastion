from __future__ import annotations

import httpx
import pytest

from bitcoin_bastion_sdk import BastionClient
from bitcoin_bastion_sdk.auth import LegacyAuthDisabledError


def test_default_sdk_client_does_not_send_authorization_bearer(
    captured_requests: list[httpx.Request],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(200, json={"data": {"ok": True}, "error": None, "meta": {}})

    client = BastionClient(base_url="http://example.com", transport=httpx.MockTransport(handler))
    client.health.public_status()
    assert "authorization" not in captured_requests[0].headers


def test_legacy_bearer_requires_explicit_opt_in(captured_requests: list[httpx.Request]) -> None:
    with pytest.raises(LegacyAuthDisabledError):
        BastionClient(base_url="http://example.com", api_key="legacy")
    assert captured_requests == []


def test_legacy_bearer_opt_in_emits_deprecation_warning(
    captured_requests: list[httpx.Request],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(200, json={"data": {"ok": True}, "error": None, "meta": {}})

    with pytest.warns(DeprecationWarning):
        client = BastionClient(
            base_url="http://example.com",
            api_key="legacy",
            allow_legacy_bearer_auth=True,
            transport=httpx.MockTransport(handler),
        )
    client.health.public_status()
    assert captured_requests[0].headers["authorization"] == "Bearer legacy"
