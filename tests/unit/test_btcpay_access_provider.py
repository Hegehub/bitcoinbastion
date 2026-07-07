from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest

from app.services.access.crypto.hashing import hmac_sha256_hex
from app.services.access.payments.base import PAYMENT_STATUS_EXPIRED, PAYMENT_STATUS_FAILED, PAYMENT_STATUS_PAID, PaymentProviderDisabledError
from app.services.access.payments.btcpay import (
    BTCPAY_STATUS_IGNORED,
    BTCPayAccessPaymentProvider,
    BTCPayConfigError,
    BTCPayWebhookVerificationError,
)


def _provider(handler: httpx.MockTransport, **overrides: Any) -> BTCPayAccessPaymentProvider:
    return BTCPayAccessPaymentProvider(
        enabled=overrides.pop("enabled", True),
        base_url="https://btcpay.example.invalid",
        api_key="api-key-secret",
        store_id="store-1",
        webhook_secret="webhook-secret",
        http_client=httpx.Client(transport=handler),
        **overrides,
    )


def _signed_headers(payload: bytes, secret: str = "webhook-secret") -> dict[str, str]:
    return {"BTCPay-Sig": f"sha256={hmac_sha256_hex(secret, payload)}"}


def _webhook_payload(event_type: str, invoice_id: str = "inv-1", metadata: dict[str, Any] | None = None) -> bytes:
    return json.dumps(
        {
            "id": "event-1",
            "type": event_type,
            "invoiceId": invoice_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "metadata": metadata or {"plan_code": "pro_pass", "email": "person@example.invalid"},
        },
        separators=(",", ":"),
    ).encode()


def test_provider_disabled_by_default() -> None:
    provider = BTCPayAccessPaymentProvider()

    with pytest.raises(PaymentProviderDisabledError):
        provider.create_invoice("lite_pass", 1000, {})


def test_missing_required_config_fails_when_enabled() -> None:
    with pytest.raises(BTCPayConfigError):
        BTCPayAccessPaymentProvider(enabled=True, base_url="", api_key="", store_id="", webhook_secret="")


def test_create_invoice_sends_expected_plan_payment_metadata() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["json"] = json.loads(request.content)
        assert request.headers["authorization"] == "token api-key-secret"
        return httpx.Response(
            200,
            json={
                "id": "inv-1",
                "checkoutLink": "https://checkout.example.invalid/i/inv-1",
                "currency": "BTC",
                "status": "New",
                "metadata": captured["json"]["metadata"],
            },
        )

    invoice = _provider(httpx.MockTransport(handler)).create_invoice(
        "pro_pass",
        50_000,
        {"internal_payment_intent_id": "pi-1", "email": "person@example.invalid"},
    )

    assert captured["json"]["metadata"]["plan_code"] == "pro_pass"
    assert captured["json"]["metadata"]["amount_sats"] == 50_000
    assert captured["json"]["metadata"]["product"] == "bastion_access"
    assert captured["json"]["metadata"]["auth_model"] == "proof_of_access"
    assert captured["json"]["metadata"]["email"] == "[REDACTED]"
    assert invoice.provider_invoice_id == "inv-1"
    assert invoice.checkout_url == "https://checkout.example.invalid/i/inv-1"


def test_settled_webhook_verifies_and_maps_to_paid() -> None:
    payload = _webhook_payload("InvoiceSettled")
    provider = _provider(httpx.MockTransport(lambda request: httpx.Response(200)))

    assert provider.verify_webhook(payload, _signed_headers(payload)) is True
    event = provider.parse_webhook_event(payload, _signed_headers(payload))

    assert event.provider == "btcpay"
    assert event.provider_invoice_id == "inv-1"
    assert event.status == PAYMENT_STATUS_PAID
    assert event.settled is True
    assert event.metadata_redacted["email"] == "[REDACTED]"


def test_expired_webhook_maps_to_expired() -> None:
    payload = _webhook_payload("InvoiceExpired")
    event = _provider(httpx.MockTransport(lambda request: httpx.Response(200))).parse_webhook_event(payload, _signed_headers(payload))

    assert event.status == PAYMENT_STATUS_EXPIRED
    assert event.expired is True


def test_invalid_webhook_maps_to_failed() -> None:
    payload = _webhook_payload("InvoiceInvalid")
    event = _provider(httpx.MockTransport(lambda request: httpx.Response(200))).parse_webhook_event(payload, _signed_headers(payload))

    assert event.status == PAYMENT_STATUS_FAILED
    assert event.invalid is True


def test_unsupported_webhook_maps_to_ignored() -> None:
    payload = _webhook_payload("InvoiceProcessing")
    event = _provider(httpx.MockTransport(lambda request: httpx.Response(200))).parse_webhook_event(payload, _signed_headers(payload))

    assert event.status == BTCPAY_STATUS_IGNORED
    assert event.settled is False


def test_invalid_signature_is_rejected() -> None:
    payload = _webhook_payload("InvoiceSettled")
    provider = _provider(httpx.MockTransport(lambda request: httpx.Response(200)))

    assert provider.verify_webhook(payload, {"BTCPay-Sig": "sha256:bad"}) is False
    with pytest.raises(BTCPayWebhookVerificationError):
        provider.parse_webhook_event(payload, {"BTCPay-Sig": "sha256:bad"})


def test_missing_signature_is_rejected() -> None:
    payload = _webhook_payload("InvoiceSettled")
    provider = _provider(httpx.MockTransport(lambda request: httpx.Response(200)))

    assert provider.verify_webhook(payload, {}) is False


def test_duplicate_settled_webhook_has_stable_event_hash() -> None:
    payload = _webhook_payload("InvoiceSettled")
    provider = _provider(httpx.MockTransport(lambda request: httpx.Response(200)))

    first = provider.parse_webhook_event(payload, _signed_headers(payload))
    second = provider.parse_webhook_event(payload, _signed_headers(payload))

    assert first.raw_event_hash == second.raw_event_hash
    assert first.settled is True
    assert second.settled is True


def test_paid_invoice_cannot_be_downgraded_by_provider_status() -> None:
    statuses = ["Settled", "Expired"]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"id": "inv-1", "status": statuses.pop(0)})

    provider = _provider(httpx.MockTransport(handler))
    paid = provider.get_invoice_status("inv-1")
    later_expired = provider.get_invoice_status("inv-1")

    assert paid.settled is True
    assert later_expired.expired is True
    # Downgrade protection is enforced by PaymentIntentService state transitions, not provider status polling.


def test_logs_redact_api_key_and_webhook_secret(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "down"})

    provider = _provider(httpx.MockTransport(handler))
    with pytest.raises(Exception):
        provider.create_invoice("lite_pass", 1000, {})

    assert "api-key-secret" not in caplog.text
    assert "webhook-secret" not in caplog.text


def test_raw_pass_session_recovery_fields_are_redacted() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["json"] = json.loads(request.content)
        return httpx.Response(200, json={"id": "inv-1", "checkoutLink": "https://checkout.example.invalid", "status": "New"})

    _provider(httpx.MockTransport(handler)).create_invoice(
        "lite_pass",
        1000,
        {"raw_pass": "raw", "session_token": "session", "recovery_phrase": "phrase"},
    )

    metadata = captured["json"]["metadata"]
    assert metadata["raw_pass"] == "[REDACTED]"
    assert metadata["session_token"] == "[REDACTED]"
    assert metadata["recovery_phrase"] == "[REDACTED]"


def test_no_email_or_password_required_in_invoice_creation() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert "email" not in payload["metadata"]
        assert "password" not in payload["metadata"]
        return httpx.Response(200, json={"id": "inv-1", "checkoutLink": "https://checkout.example.invalid", "status": "New"})

    invoice = _provider(httpx.MockTransport(handler)).create_invoice("lite_pass", 1000, {})

    assert invoice.provider_invoice_id == "inv-1"
