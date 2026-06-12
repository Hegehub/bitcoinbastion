from __future__ import annotations

import hashlib
import hmac

import httpx

from bitcoin_bastion_sdk import BastionClient
from bitcoin_bastion_sdk.webhooks import verify_signature


def make_client(captured: list[httpx.Request]) -> BastionClient:
    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={"data": {"path": request.url.path}, "error": None, "meta": {}})

    return BastionClient(base_url="http://example.com", transport=httpx.MockTransport(handler))


def test_create_webhook_calls_correct_endpoint() -> None:
    captured: list[httpx.Request] = []
    make_client(captured).webhooks.create(url="https://example.com/hook", events=["signal.published"])
    assert captured[0].method == "POST"
    assert captured[0].url.path == "/api/v1/webhooks"


def test_list_webhooks_calls_correct_endpoint() -> None:
    captured: list[httpx.Request] = []
    make_client(captured).webhooks.list()
    assert captured[0].url.path == "/api/v1/webhooks"


def test_webhook_test_calls_correct_endpoint() -> None:
    captured: list[httpx.Request] = []
    make_client(captured).webhooks.test(7)
    assert captured[0].url.path == "/api/v1/webhooks/7/test"


def test_deliveries_call_correct_endpoint() -> None:
    captured: list[httpx.Request] = []
    make_client(captured).webhooks.deliveries(7)
    assert captured[0].url.path == "/api/v1/webhooks/7/deliveries"


def test_signature_verification_succeeds_for_valid_payload() -> None:
    payload = b'{"ok":true}'
    secret = "whsec_test_secret"
    timestamp = 1234567890
    digest = hmac.new(secret.encode(), f"{timestamp}.".encode() + payload, hashlib.sha256).hexdigest()
    assert verify_signature(payload=payload, secret=secret, timestamp=timestamp, signature=f"v1={digest}", now=timestamp)


def test_signature_verification_fails_for_invalid_signature() -> None:
    assert not verify_signature(payload=b"{}", secret="whsec_test_secret", timestamp=1, signature="v1=bad", now=1)
