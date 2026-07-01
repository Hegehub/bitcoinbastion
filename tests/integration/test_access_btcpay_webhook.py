from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models.access import AccessPaymentIntent
from app.domain.access.plans import PlanCode
from app.services.access.crypto.hashing import hmac_sha256_hex
from app.services.access.payment_intent_service import PaymentIntentService
from app.services.access.payments.base import PAYMENT_STATUS_PAID, PaymentIntentAlreadyFinalizedError
import pytest
from app.services.access.payments.btcpay import BTCPayAccessPaymentProvider


def test_access_btcpay_webhook_marks_payment_paid_without_issuing_certificate() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "btcpay-invoice-1",
                "checkoutLink": "https://checkout.example.invalid/i/btcpay-invoice-1",
                "currency": "BTC",
                "status": "New",
                "expirationTime": (datetime.now(UTC) + timedelta(minutes=30)).isoformat(),
            },
        )

    provider = BTCPayAccessPaymentProvider(
        enabled=True,
        base_url="https://btcpay.example.invalid",
        api_key="api-key-secret",
        store_id="store-1",
        webhook_secret="webhook-secret",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    engine = create_engine("sqlite:///:memory:")
    AccessPaymentIntent.__table__.create(bind=engine)
    with Session(engine) as session:
        service = PaymentIntentService(session, {"btcpay": provider})
        intent = service.create_payment_intent(PlanCode.PRO, "btcpay", 50_000, {"internal_payment_intent_id": "pi-1"})
        payload = _webhook_payload("InvoiceSettled", "btcpay-invoice-1", {"internal_payment_intent_id": intent.id})
        headers = {"BTCPay-Sig": f"sha256={hmac_sha256_hex('webhook-secret', payload)}"}

        event = provider.parse_webhook_event(payload, headers)
        paid = service.mark_paid_from_verified_event("btcpay", "btcpay-invoice-1", event)

        assert paid.status == PAYMENT_STATUS_PAID
        assert paid.paid_at is not None

        expired_payload = _webhook_payload("InvoiceExpired", "btcpay-invoice-1", {"internal_payment_intent_id": intent.id})
        expired_headers = {"BTCPay-Sig": f"sha256={hmac_sha256_hex('webhook-secret', expired_payload)}"}
        expired_event = provider.parse_webhook_event(expired_payload, expired_headers)
        assert expired_event.expired is True
        with pytest.raises(PaymentIntentAlreadyFinalizedError):
            service.expire_payment_intent(intent.id)

        assert paid.status == PAYMENT_STATUS_PAID
        assert session.query(AccessPaymentIntent).count() == 1


def _webhook_payload(event_type: str, invoice_id: str, metadata: dict[str, Any]) -> bytes:
    return json.dumps(
        {
            "id": "event-1",
            "type": event_type,
            "invoiceId": invoice_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "metadata": metadata,
        },
        separators=(",", ":"),
    ).encode()
