"""Access Payment Intent lifecycle service.

This service creates and updates payment intents only. It does not issue Access
Certificates, Subscription Entitlements, sessions, or bearer-style credentials.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.access import AccessPaymentIntent
from app.domain.access.plans import PlanCode, normalize_plan_code
from app.services.access.crypto.hashing import hash_canonical_json_prefixed, sha256_prefixed
from app.services.access.payments.base import (
    PAYMENT_STATUS_CANCELLED,
    PAYMENT_STATUS_EXPIRED,
    PAYMENT_STATUS_FAILED,
    PAYMENT_STATUS_INVALID,
    PAYMENT_STATUS_INVOICE_CREATED,
    PAYMENT_STATUS_MANUAL_REVIEW_REQUIRED,
    PAYMENT_STATUS_PAID,
    PAYMENT_STATUS_PAID_LATE_REVIEW_REQUIRED,
    PaymentIntentAlreadyFinalizedError,
    PaymentIntentNotFoundError,
    PaymentProvider,
    PaymentProviderNotConfiguredError,
    InvalidPaymentStateTransitionError,
    PaymentProviderWebhookEvent,
)

from app.services.access.payments.redaction import redact_payment_metadata


@dataclass(frozen=True, slots=True)
class AccessPaymentIntentStatus:
    payment_intent_id: int
    status: str
    provider: str | None
    paid: bool
    expired: bool
    invalid: bool
    review_required: bool


class PaymentIntentService:
    def __init__(self, db: Session, providers: dict[str, PaymentProvider]) -> None:
        self.db = db
        self.providers = providers

    def create_payment_intent(
        self,
        plan_code: PlanCode | str,
        payment_method: str,
        amount_sats: int,
        metadata: dict[str, Any] | None = None,
    ) -> AccessPaymentIntent:
        plan = normalize_plan_code(plan_code)
        if amount_sats <= 0:
            raise ValueError("amount_sats must be positive")
        provider = self._provider_for(payment_method)
        redacted_metadata = redact_payment_metadata(metadata or {})
        invoice = provider.create_invoice(plan.value, amount_sats, redacted_metadata)
        now = datetime.now(UTC)
        intent = AccessPaymentIntent(
            payment_method=payment_method,
            provider=invoice.provider,
            provider_invoice_id_hash=sha256_prefixed(invoice.provider_invoice_id),
            invoice_hash=hash_canonical_json_prefixed(
                {
                    "provider": invoice.provider,
                    "provider_invoice_id": invoice.provider_invoice_id,
                    "amount_sats": invoice.amount_sats,
                }
            ),
            amount_sats=amount_sats,
            plan_code=plan.value,
            status=PAYMENT_STATUS_INVOICE_CREATED,
            checkout_url_hash=sha256_prefixed(invoice.checkout_url) if invoice.checkout_url else None,
            metadata_json=redact_payment_metadata(invoice.raw_metadata_redacted),
            created_at=now,
            updated_at=now,
            expires_at=invoice.expires_at,
        )
        self.db.add(intent)
        self.db.flush()
        intent.payment_id_hash = sha256_prefixed(f"access_payment_intent:{intent.id}")
        self.db.flush()
        return intent

    def get_payment_intent(self, payment_intent_id: UUID | int) -> AccessPaymentIntent | None:
        if isinstance(payment_intent_id, UUID):
            return None
        return self.db.get(AccessPaymentIntent, int(payment_intent_id))

    def get_payment_status(self, payment_intent_id: UUID | int) -> AccessPaymentIntentStatus:
        intent = self.get_payment_intent(payment_intent_id)
        if intent is None:
            raise PaymentIntentNotFoundError("Payment intent not found")
        return AccessPaymentIntentStatus(
            payment_intent_id=intent.id,
            status=intent.status,
            provider=intent.provider,
            paid=intent.status == PAYMENT_STATUS_PAID,
            expired=intent.status == PAYMENT_STATUS_EXPIRED,
            invalid=intent.status == PAYMENT_STATUS_INVALID,
            review_required=intent.status in {PAYMENT_STATUS_PAID_LATE_REVIEW_REQUIRED, PAYMENT_STATUS_MANUAL_REVIEW_REQUIRED},
        )

    def mark_paid_from_verified_event(
        self,
        provider: str,
        provider_invoice_id: str,
        event: PaymentProviderWebhookEvent,
    ) -> AccessPaymentIntent:
        if not event.settled:
            raise InvalidPaymentStateTransitionError("Verified event is not settled")
        intent = self._get_by_provider_invoice(provider, provider_invoice_id)
        if intent.status == PAYMENT_STATUS_PAID:
            self._merge_metadata(intent, {"duplicate_event": True, "last_event_hash": event.raw_event_hash})
            self.db.flush()
            return intent
        if intent.status == PAYMENT_STATUS_EXPIRED:
            return self._transition(
                intent,
                PAYMENT_STATUS_PAID_LATE_REVIEW_REQUIRED,
                event,
                {"late_settlement": True, "settlement_review_required": True},
                paid_at=None,
            )
        if intent.status in {PAYMENT_STATUS_INVALID, PAYMENT_STATUS_CANCELLED, PAYMENT_STATUS_FAILED}:
            return self._transition(
                intent,
                PAYMENT_STATUS_MANUAL_REVIEW_REQUIRED,
                event,
                {"settlement_review_required": True},
                paid_at=None,
            )
        if intent.status != PAYMENT_STATUS_INVOICE_CREATED:
            raise InvalidPaymentStateTransitionError("Payment intent cannot be marked paid from current state")
        return self._transition(intent, PAYMENT_STATUS_PAID, event, {"settled": True}, paid_at=event.occurred_at)

    def expire_payment_intent(self, payment_intent_id: UUID | int) -> AccessPaymentIntent:
        intent = self.get_payment_intent(payment_intent_id)
        if intent is None:
            raise PaymentIntentNotFoundError("Payment intent not found")
        if intent.status == PAYMENT_STATUS_PAID:
            raise PaymentIntentAlreadyFinalizedError("Paid payment intent cannot expire")
        if intent.status in {PAYMENT_STATUS_INVALID, PAYMENT_STATUS_CANCELLED}:
            raise InvalidPaymentStateTransitionError("Payment intent cannot expire from current state")
        intent.status = PAYMENT_STATUS_EXPIRED
        intent.updated_at = datetime.now(UTC)
        self._merge_metadata(intent, {"expired": True})
        self.db.flush()
        return intent

    def mark_invalid_from_verified_event(
        self,
        provider: str,
        provider_invoice_id: str,
        event: PaymentProviderWebhookEvent,
    ) -> AccessPaymentIntent:
        if not event.invalid:
            raise InvalidPaymentStateTransitionError("Verified event is not invalid")
        intent = self._get_by_provider_invoice(provider, provider_invoice_id)
        if intent.status == PAYMENT_STATUS_PAID:
            raise PaymentIntentAlreadyFinalizedError("Paid payment intent cannot be marked invalid")
        return self._transition(intent, PAYMENT_STATUS_INVALID, event, {"invalid": True}, paid_at=None)

    def cancel_payment_intent(self, payment_intent_id: UUID | int, reason: str) -> AccessPaymentIntent:
        intent = self.get_payment_intent(payment_intent_id)
        if intent is None:
            raise PaymentIntentNotFoundError("Payment intent not found")
        if intent.status == PAYMENT_STATUS_PAID:
            raise PaymentIntentAlreadyFinalizedError("Paid payment intent cannot be cancelled")
        intent.status = PAYMENT_STATUS_CANCELLED
        intent.updated_at = datetime.now(UTC)
        self._merge_metadata(intent, {"cancelled": True, "cancel_reason": reason[:120]})
        self.db.flush()
        return intent

    def _provider_for(self, payment_method: str) -> PaymentProvider:
        provider = self.providers.get(payment_method)
        if provider is None:
            raise PaymentProviderNotConfiguredError("Payment provider is not configured")
        return provider

    def _get_by_provider_invoice(self, provider: str, provider_invoice_id: str) -> AccessPaymentIntent:
        provider_invoice_hash = sha256_prefixed(provider_invoice_id)
        statement = select(AccessPaymentIntent).where(
            AccessPaymentIntent.provider == provider,
            AccessPaymentIntent.provider_invoice_id_hash == provider_invoice_hash,
        )
        intent = self.db.execute(statement).scalar_one_or_none()
        if intent is None:
            raise PaymentIntentNotFoundError("Payment intent not found")
        return intent

    def _transition(
        self,
        intent: AccessPaymentIntent,
        status: str,
        event: PaymentProviderWebhookEvent,
        metadata: dict[str, Any],
        paid_at: datetime | None,
    ) -> AccessPaymentIntent:
        intent.status = status
        intent.updated_at = datetime.now(UTC)
        intent.paid_at = paid_at
        self._merge_metadata(
            intent,
            {
                **metadata,
                "last_event_hash": event.raw_event_hash,
                "provider_event_type": event.event_type,
                "provider_status": event.status,
            },
        )
        self.db.flush()
        return intent

    def _merge_metadata(self, intent: AccessPaymentIntent, metadata: dict[str, Any]) -> None:
        current = dict(intent.metadata_json or {})
        current.update(redact_payment_metadata(metadata))
        intent.metadata_json = current
