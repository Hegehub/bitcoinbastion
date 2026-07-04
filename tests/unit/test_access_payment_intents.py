from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.models.access import AccessPaymentIntent
from app.domain.access.errors import InvalidPlanCodeError
from app.domain.access.plans import PlanCode
from app.services.access.payment_intent_service import PaymentIntentService
from app.services.access.payments.base import (
    InvalidPaymentStateTransitionError,
    PAYMENT_STATUS_EXPIRED,
    PAYMENT_STATUS_INVOICE_CREATED,
    PAYMENT_STATUS_MANUAL_REVIEW_REQUIRED,
    PAYMENT_STATUS_PAID,
    PAYMENT_STATUS_PAID_LATE_REVIEW_REQUIRED,
    PaymentIntentAlreadyFinalizedError,
    PaymentProviderInvoice,
    PaymentProviderInvoiceStatus,
    PaymentProviderWebhookEvent,
)


class FakePaymentProvider:
    provider_name = "fake"

    def create_invoice(self, plan_code: str, amount_sats: int, metadata: dict[str, Any]) -> PaymentProviderInvoice:
        return PaymentProviderInvoice(
            provider=self.provider_name,
            provider_invoice_id="provider-invoice-1",
            checkout_url="https://checkout.example.invalid/tokenized",
            amount_sats=amount_sats,
            currency="sats",
            status=PAYMENT_STATUS_INVOICE_CREATED,
            expires_at=datetime.now(UTC) + timedelta(minutes=15),
            raw_metadata_redacted=metadata,
        )

    def get_invoice_status(self, provider_invoice_id: str) -> PaymentProviderInvoiceStatus:
        return PaymentProviderInvoiceStatus(
            provider=self.provider_name,
            provider_invoice_id=provider_invoice_id,
            status=PAYMENT_STATUS_INVOICE_CREATED,
            settled=False,
            expired=False,
            invalid=False,
            checked_at=datetime.now(UTC),
        )

    def verify_webhook(self, payload: bytes, headers: dict[str, str]) -> bool:
        return True

    def parse_webhook_event(self, payload: bytes, headers: dict[str, str]) -> PaymentProviderWebhookEvent:
        raise NotImplementedError


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    AccessPaymentIntent.__table__.create(bind=engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def service(db_session: Session) -> PaymentIntentService:
    return PaymentIntentService(db_session, {"fake": FakePaymentProvider()})


def settled_event() -> PaymentProviderWebhookEvent:
    return PaymentProviderWebhookEvent(
        provider="fake",
        provider_invoice_id="provider-invoice-1",
        event_type="invoice.settled",
        status="paid",
        settled=True,
        expired=False,
        invalid=False,
        occurred_at=datetime.now(UTC),
        raw_event_hash="sha256:event",
        metadata_redacted={"safe": True},
    )


def invalid_event() -> PaymentProviderWebhookEvent:
    return PaymentProviderWebhookEvent(
        provider="fake",
        provider_invoice_id="provider-invoice-1",
        event_type="invoice.invalid",
        status="invalid",
        settled=False,
        expired=False,
        invalid=True,
        occurred_at=datetime.now(UTC),
        raw_event_hash="sha256:invalid",
        metadata_redacted={},
    )


def test_create_payment_intent_with_valid_plan(service: PaymentIntentService) -> None:
    intent = service.create_payment_intent(PlanCode.PRO, "fake", 50_000, {"purpose": "access"})

    assert intent.id is not None
    assert intent.plan_code == PlanCode.PRO.value
    assert intent.status == PAYMENT_STATUS_INVOICE_CREATED
    assert intent.provider == "fake"
    assert intent.payment_id_hash.startswith("sha256:")
    assert intent.provider_invoice_id_hash.startswith("sha256:")
    assert intent.checkout_url_hash is not None


def test_unknown_plan_rejected(service: PaymentIntentService) -> None:
    with pytest.raises(InvalidPlanCodeError):
        service.create_payment_intent("unknown", "fake", 10_000)


def test_amount_sats_must_be_positive(service: PaymentIntentService) -> None:
    with pytest.raises(ValueError):
        service.create_payment_intent(PlanCode.LITE, "fake", 0)


def test_payment_intent_stores_provider_metadata_redacted(service: PaymentIntentService) -> None:
    intent = service.create_payment_intent(
        PlanCode.LITE,
        "fake",
        1000,
        {"email": "person@example.invalid", "safe_reference": "order-1", "nested": {"api_key": "secret"}},
    )

    assert intent.metadata_json["email"] == "[REDACTED]"
    assert intent.metadata_json["safe_reference"] == "order-1"
    assert intent.metadata_json["nested"]["api_key"] == "[REDACTED]"


def test_payment_intent_does_not_store_raw_secret(service: PaymentIntentService) -> None:
    intent = service.create_payment_intent(PlanCode.LITE, "fake", 1000, {"webhook_secret": "raw-secret"})

    serialized = str(intent.metadata_json) + str(intent.provider_invoice_id_hash) + str(intent.checkout_url_hash)
    assert "raw-secret" not in serialized
    assert "provider-invoice-1" not in serialized
    assert "tokenized" not in serialized


def test_paid_event_marks_intent_paid(service: PaymentIntentService) -> None:
    service.create_payment_intent(PlanCode.LITE, "fake", 1000)

    intent = service.mark_paid_from_verified_event("fake", "provider-invoice-1", settled_event())

    assert intent.status == PAYMENT_STATUS_PAID
    assert intent.paid_at is not None


def test_duplicate_paid_event_is_idempotent(service: PaymentIntentService) -> None:
    service.create_payment_intent(PlanCode.LITE, "fake", 1000)
    first = service.mark_paid_from_verified_event("fake", "provider-invoice-1", settled_event())
    second = service.mark_paid_from_verified_event("fake", "provider-invoice-1", settled_event())

    assert first.id == second.id
    assert second.status == PAYMENT_STATUS_PAID
    assert second.metadata_json["duplicate_event"] is True


def test_expired_event_marks_intent_expired(service: PaymentIntentService) -> None:
    intent = service.create_payment_intent(PlanCode.LITE, "fake", 1000)

    expired = service.expire_payment_intent(intent.id)

    assert expired.status == PAYMENT_STATUS_EXPIRED


def test_paid_after_expired_requires_late_settlement_review(service: PaymentIntentService) -> None:
    intent = service.create_payment_intent(PlanCode.LITE, "fake", 1000)
    service.expire_payment_intent(intent.id)

    reviewed = service.mark_paid_from_verified_event("fake", "provider-invoice-1", settled_event())

    assert reviewed.status == PAYMENT_STATUS_PAID_LATE_REVIEW_REQUIRED
    assert reviewed.metadata_json["late_settlement"] is True
    assert reviewed.metadata_json["settlement_review_required"] is True


def test_invalid_transition_is_rejected(service: PaymentIntentService) -> None:
    intent = service.create_payment_intent(PlanCode.LITE, "fake", 1000)
    service.mark_paid_from_verified_event("fake", "provider-invoice-1", settled_event())

    with pytest.raises(PaymentIntentAlreadyFinalizedError):
        service.expire_payment_intent(intent.id)


def test_unpaid_invoice_cannot_be_treated_as_paid(service: PaymentIntentService) -> None:
    service.create_payment_intent(PlanCode.LITE, "fake", 1000)
    event = settled_event()
    unpaid_event = PaymentProviderWebhookEvent(
        provider=event.provider,
        provider_invoice_id=event.provider_invoice_id,
        event_type=event.event_type,
        status="pending",
        settled=False,
        expired=False,
        invalid=False,
        occurred_at=event.occurred_at,
        raw_event_hash=event.raw_event_hash,
        metadata_redacted={},
    )

    with pytest.raises(InvalidPaymentStateTransitionError):
        service.mark_paid_from_verified_event("fake", "provider-invoice-1", unpaid_event)


def test_invalid_or_cancelled_then_paid_requires_manual_review(service: PaymentIntentService) -> None:
    service.create_payment_intent(PlanCode.LITE, "fake", 1000)
    service.mark_invalid_from_verified_event("fake", "provider-invoice-1", invalid_event())

    reviewed = service.mark_paid_from_verified_event("fake", "provider-invoice-1", settled_event())

    assert reviewed.status == PAYMENT_STATUS_MANUAL_REVIEW_REQUIRED
    assert reviewed.metadata_json["settlement_review_required"] is True


def test_payment_service_does_not_issue_access_certificate(service: PaymentIntentService, db_session: Session) -> None:
    service.create_payment_intent(PlanCode.LITE, "fake", 1000)

    intents = db_session.execute(select(AccessPaymentIntent)).scalars().all()

    assert len(intents) == 1
    assert "AccessCertificate" not in PathLikeSource.PAYMENT_INTENT_SERVICE_SOURCE


class PathLikeSource:
    PAYMENT_INTENT_SERVICE_SOURCE = __import__(
        "pathlib"
    ).Path("app/services/access/payment_intent_service.py").read_text()
