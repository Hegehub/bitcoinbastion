from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models.access import AccessCheckoutSession, AccessPaymentIntent
from app.services.access.checkout_service import AccessCheckoutService
from app.services.access.offer_catalog import get_offer, list_offers
from app.services.access.payment_intent_service import PaymentIntentService
from app.services.access.payments.manual import ManualGrantProvider


def _service():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    payments = PaymentIntentService(db, {"manual": ManualGrantProvider(allow_manual_grants=True, environment="test")})
    return db, AccessCheckoutService(db, payments)


def test_offer_identity_revision_and_exact_terms_are_stable():
    offers = list_offers()
    assert offers
    offer = get_offer("access-plus_pass")
    assert offer == get_offer(offer.offer_id)
    assert offer.revision_id.startswith("access-plus_pass:")
    assert offer.amount_sats == 50_000 and offer.price_unit == "sats"
    assert offer.duration_days == 30 and offer.terms_version == "access-terms-v1"
    assert offer.scopes and offer.availability == "active"


def test_checkout_freezes_offer_terms_and_binds_exact_payment():
    db, service = _service()
    offer = get_offer("access-plus_pass")
    checkout = service.create(offer.offer_id, "manual", "checkout-intent-0001")
    db.commit()
    payment = db.get(AccessPaymentIntent, checkout.payment_intent_id)
    assert checkout.offer_revision_id == offer.revision_id
    assert (checkout.amount_sats, checkout.price_unit) == (offer.amount_sats, "sats")
    assert checkout.duration_days == offer.duration_days
    assert tuple(checkout.scopes_json) == offer.scopes
    assert payment.amount_sats == offer.amount_sats
    assert payment.checkout_id == checkout.id


def test_checkout_retry_is_idempotent_and_conflict_is_rejected():
    db, service = _service()
    first = service.create("access-lite_pass", "manual", "checkout-intent-0002")
    second = service.create("access-lite_pass", "manual", "checkout-intent-0002")
    assert second.id == first.id
    assert db.query(AccessCheckoutSession).count() == 1
    assert db.query(AccessPaymentIntent).count() == 1
    try:
        service.create("access-pro_pass", "manual", "checkout-intent-0002")
    except ValueError as exc:
        assert str(exc) == "idempotency_conflict"
    else:
        raise AssertionError("idempotency conflict accepted")


def test_checkout_terms_do_not_drift_and_expired_is_never_eligible():
    db, service = _service()
    checkout = service.create("access-basic_pass", "manual", "checkout-intent-0003")
    frozen = (checkout.offer_revision_id, checkout.amount_sats, checkout.duration_days, checkout.capability, checkout.terms_version)
    checkout.expires_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=1)
    db.commit()
    restored = AccessCheckoutService(db, service.payment_service).get(checkout.id)
    assert (restored.offer_revision_id, restored.amount_sats, restored.duration_days, restored.capability, restored.terms_version) == frozen
    assert restored.status == "expired"
    assert not service.is_issuance_eligible(restored)


def test_caller_has_no_price_duration_capability_or_revision_input():
    from app.schemas.access_checkout import CheckoutCreateRequest
    assert set(CheckoutCreateRequest.model_fields) == {"offer_id", "payment_method", "idempotency_key"}
