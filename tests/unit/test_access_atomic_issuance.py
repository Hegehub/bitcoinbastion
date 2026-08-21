from datetime import UTC, datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models.access import (
    AccessCheckoutSession,
    AccessIssuedGrant,
    AccessIssuanceChallenge,
    AccessPaymentIntent,
)
from app.services.access.certificate_issuer import AccessCertificateIssuer
from app.services.access.crypto.signatures import Ed25519SignatureSuite
from app.services.access.issuance_service import AccessIssuanceError, AccessIssuanceService, SIGNING_CONTEXT


def _pem_pair():
    key = Ed25519PrivateKey.generate()
    private = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
    public = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    return private, public


def _setup():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = Session(engine)
    payment = AccessPaymentIntent(payment_method="manual", amount_sats=50_000, plan_code="plus_pass", status="paid")
    db.add(payment)
    db.flush()
    checkout = AccessCheckoutSession(
        id="checkout:a", idempotency_key_hash="sha256:intent", offer_id="access-plus_pass",
        offer_revision_id="access-plus_pass:v1", plan_code="plus_pass", capability="plus_pass",
        scopes_json=["signals:basic:read"], amount_sats=50_000, price_unit="sats", duration_days=30,
        terms_version="access-terms-v1", status="eligible", eligibility_reason="payment_settled",
        payment_intent_id=payment.id, created_at=datetime.now(UTC), updated_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(minutes=30),
    )
    payment.checkout_id = checkout.id
    db.add(checkout)
    issuer_private, issuer_public = _pem_pair()
    issuer = AccessCertificateIssuer(db, server_pepper="test-pepper", issuer_private_key=issuer_private,
                                     issuer_public_key=issuer_public, issuer_key_id="test-issuer")
    return db, checkout, AccessIssuanceService(db, issuer)


def test_valid_pop_atomically_issues_frozen_grant_and_retry_is_idempotent():
    db, checkout, service = _setup()
    device_private, device_public = _pem_pair()
    challenge = service.create_challenge(checkout.id, device_public)
    signed = Ed25519SignatureSuite().sign(challenge.payload_json, SIGNING_CONTEXT, "device", device_private)
    grant = service.verify_and_issue(checkout.id, challenge.id, signed.signature)
    retried = service.verify_and_issue(checkout.id, challenge.id, signed.signature)
    assert retried.id == grant.id
    assert db.query(AccessIssuedGrant).count() == 1
    assert grant.capability == checkout.capability
    assert grant.scopes_json == checkout.scopes_json
    assert grant.offer_revision_id == checkout.offer_revision_id
    assert grant.expires_at - grant.issued_at == timedelta(days=checkout.duration_days)
    assert checkout.status == "issued"


def test_invalid_signature_wrong_context_and_expiry_never_issue():
    db, checkout, service = _setup()
    _, public = _pem_pair()
    challenge = service.create_challenge(checkout.id, public)
    with pytest.raises(AccessIssuanceError, match="invalid_signature"):
        service.verify_and_issue(checkout.id, challenge.id, "not-a-signature")
    with pytest.raises(AccessIssuanceError, match="checkout_not_found"):
        service.verify_and_issue("checkout:other", challenge.id, "not-a-signature")
    challenge.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    with pytest.raises(AccessIssuanceError, match="challenge_expired"):
        service.verify_and_issue(checkout.id, challenge.id, "not-a-signature")
    assert db.query(AccessIssuedGrant).count() == 0


def test_toctou_checkout_ineligible_after_challenge_prevents_issuance():
    db, checkout, service = _setup()
    private, public = _pem_pair()
    challenge = service.create_challenge(checkout.id, public)
    signature = Ed25519SignatureSuite().sign(challenge.payload_json, SIGNING_CONTEXT, "device", private).signature
    checkout.status = "cancelled"
    with pytest.raises(AccessIssuanceError, match="checkout_not_eligible"):
        service.verify_and_issue(checkout.id, challenge.id, signature)
    assert db.query(AccessIssuedGrant).count() == 0


def test_contract_has_no_caller_authoritative_terms_or_private_key():
    from app.schemas.access_checkout import AccessIssueRequest, IssuanceChallengeCreateRequest

    assert set(IssuanceChallengeCreateRequest.model_fields) == {"checkout_id", "device_public_key"}
    assert set(AccessIssueRequest.model_fields) == {"checkout_id", "challenge_id", "signature", "idempotency_key"}
    forbidden = {"price", "amount", "duration", "capability", "scope", "terms", "private_key"}
    assert not forbidden & set(AccessIssueRequest.model_fields)


def test_simultaneous_pi1_requests_create_exactly_one_semantic_grant(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pi1-race.db'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    issuer_private, issuer_public = _pem_pair()
    device_private, device_public = _pem_pair()
    with sessions() as db:
        payment = AccessPaymentIntent(
            payment_method="manual", amount_sats=50_000, plan_code="plus_pass", status="paid"
        )
        db.add(payment)
        db.flush()
        checkout = AccessCheckoutSession(
            id="checkout:race", idempotency_key_hash="sha256:race",
            offer_id="access-plus_pass", offer_revision_id="access-plus_pass:v1",
            plan_code="plus_pass", capability="plus_pass",
            scopes_json=["signals:basic:read"], amount_sats=50_000, price_unit="sats",
            duration_days=30, terms_version="access-terms-v1", status="eligible",
            eligibility_reason="payment_settled", payment_intent_id=payment.id,
            created_at=datetime.now(UTC), updated_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
        )
        payment.checkout_id = checkout.id
        db.add(checkout)
        issuer = AccessCertificateIssuer(
            db, server_pepper="test-pepper", issuer_private_key=issuer_private,
            issuer_public_key=issuer_public, issuer_key_id="test-issuer",
        )
        challenge = AccessIssuanceService(db, issuer).create_challenge(checkout.id, device_public)
        signature = Ed25519SignatureSuite().sign(
            challenge.payload_json, SIGNING_CONTEXT, "device", device_private
        ).signature
        challenge_id = challenge.id
        db.commit()

    barrier = Barrier(2)

    def issue_once() -> str:
        with sessions() as db:
            issuer = AccessCertificateIssuer(
                db, server_pepper="test-pepper", issuer_private_key=issuer_private,
                issuer_public_key=issuer_public, issuer_key_id="test-issuer",
            )
            barrier.wait()
            grant = AccessIssuanceService(db, issuer).verify_and_issue(
                "checkout:race", challenge_id, signature
            )
            db.commit()
            return grant.id

    with ThreadPoolExecutor(max_workers=2) as pool:
        grant_ids = list(pool.map(lambda _: issue_once(), range(2)))

    with sessions() as db:
        assert len(set(grant_ids)) == 1
        assert db.query(AccessIssuedGrant).count() == 1
        assert db.get(AccessCheckoutSession, "checkout:race").status == "issued"
        challenge = db.get(AccessIssuanceChallenge, challenge_id)
        assert challenge.status == "consumed"
        assert challenge.consumed_at is not None
