from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.access import AccessCheckoutSession, AccessPaymentIntent
from app.schemas.access_checkout import CheckoutStatus, EligibilityReason
from app.services.access.crypto.hashing import sha256_prefixed
from app.services.access.offer_catalog import AccessOffer, get_offer
from app.services.access.payment_intent_service import PaymentIntentService
from app.services.access.payments.base import PAYMENT_STATUS_PAID


class AccessCheckoutService:
    def __init__(self, db: Session, payment_service: PaymentIntentService) -> None:
        self.db = db
        self.payment_service = payment_service

    def create(self, offer_id: str, payment_method: str, idempotency_key: str) -> AccessCheckoutSession:
        key_hash = sha256_prefixed(idempotency_key)
        existing = self.db.execute(select(AccessCheckoutSession).where(AccessCheckoutSession.idempotency_key_hash == key_hash)).scalar_one_or_none()
        if existing:
            if existing.offer_id != offer_id:
                raise ValueError("idempotency_conflict")
            return self.refresh(existing)
        offer = get_offer(offer_id)
        if offer.availability != "active":
            raise ValueError("offer_inactive")
        now = datetime.now(UTC)
        checkout = self._snapshot(offer, key_hash, now)
        self.db.add(checkout)
        self.db.flush()
        payment = self.payment_service.create_payment_intent(
            offer.plan_code, payment_method, offer.amount_sats, {"checkout_id": checkout.id}
        )
        payment.checkout_id = checkout.id
        checkout.payment_intent_id = payment.id
        self.db.flush()
        return checkout

    def get(self, checkout_id: str) -> AccessCheckoutSession:
        checkout = self.db.get(AccessCheckoutSession, checkout_id)
        if checkout is None:
            raise ValueError("checkout_not_found")
        return self.refresh(checkout)

    def refresh(self, checkout: AccessCheckoutSession) -> AccessCheckoutSession:
        now = datetime.now(UTC).replace(tzinfo=None)
        if checkout.status in {
            CheckoutStatus.CANCELLED.value,
            CheckoutStatus.FAILED.value,
            CheckoutStatus.ISSUED.value,
        }:
            checkout.eligibility_reason = EligibilityReason.TERMINAL_STATE.value
            return checkout
        expires_at = checkout.expires_at.replace(tzinfo=None) if checkout.expires_at.tzinfo else checkout.expires_at
        if expires_at <= now:
            checkout.status = CheckoutStatus.EXPIRED.value
            checkout.eligibility_reason = EligibilityReason.CHECKOUT_EXPIRED.value
            return checkout
        payment = self.db.get(AccessPaymentIntent, checkout.payment_intent_id)
        if payment and payment.status == PAYMENT_STATUS_PAID:
            checkout.status = CheckoutStatus.ELIGIBLE.value
            checkout.eligibility_reason = EligibilityReason.PAYMENT_SETTLED.value
        return checkout

    @staticmethod
    def is_issuance_eligible(checkout: AccessCheckoutSession) -> bool:
        return checkout.status == CheckoutStatus.ELIGIBLE.value

    @staticmethod
    def _snapshot(offer: AccessOffer, key_hash: str, now: datetime) -> AccessCheckoutSession:
        return AccessCheckoutSession(
            id=f"access_checkout:{uuid4()}", idempotency_key_hash=key_hash,
            offer_id=offer.offer_id, offer_revision_id=offer.revision_id,
            plan_code=offer.plan_code.value, capability=offer.capability,
            scopes_json=list(offer.scopes), amount_sats=offer.amount_sats,
            price_unit=offer.price_unit, duration_days=offer.duration_days,
            terms_version=offer.terms_version, status=CheckoutStatus.AWAITING_PAYMENT.value,
            eligibility_reason=EligibilityReason.PAYMENT_PENDING.value,
            created_at=now, updated_at=now, expires_at=now + timedelta(minutes=30),
        )
