from __future__ import annotations

import asyncio
import base64
import hashlib
from datetime import UTC, datetime

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.domain.lnurl.payment_proofs import LNURLPaymentContext
from app.services.lnurl.entitlement_binding_service import (
    AccessRequestContext,
    DefaultBindingPolicy,
    InMemoryLNURLEntitlementBindingRepository,
    LNURLEntitlementBindingConfig,
    LNURLEntitlementBindingMode,
    LNURLEntitlementBindingService,
    LNURLEntitlementBindingState,
    LNURLEntitlementOperationType,
    LNURLSubscriptionProduct,
    PrincipalReference,
)
from app.services.lnurl.errors import (
    LNURLBindingActivationExpiredError,
    LNURLBindingAmountInvalidError,
    LNURLBindingPolicyDeniedError,
    LNURLBindingPrincipalMismatchError,
    LNURLBindingProductDisabledError,
    LNURLBindingStepUpRequiredError,
)
from app.services.lnurl.payment_proof import (
    InMemoryLNURLPaymentProofRepository,
    LNURLPaymentProofConfig,
    LNURLPaymentProofService,
)
from app.services.lnurl.verification_sources import (
    LNURLSettlementState,
    LNURLVerificationSourceType,
    SettlementSourceResult,
    test_bolt11 as make_test_bolt11,
)
from app.services.lnurl.verify import InMemoryLNURLVerifyRepository, LNURLPaymentForVerification, LNURLVerifyService


class Source:
    source_type = LNURLVerificationSourceType.INTERNAL_LIGHTNING_NODE

    def __init__(self, invoice: str, preimage: bytes):
        self.invoice = invoice
        self.preimage = preimage

    async def verify(self, payment):
        return SettlementSourceResult(
            self.source_type,
            True,
            LNURLSettlementState.SETTLED,
            invoice=self.invoice,
            preimage=self.preimage.hex(),
        )


def keys():
    private = Ed25519PrivateKey.generate()
    raw_private = private.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    raw_public = private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return base64.urlsafe_b64encode(raw_private).decode().rstrip("="), base64.urlsafe_b64encode(raw_public).decode().rstrip("=")


def make_proof(plan="pro_pass", amount=4000, principal_hash=None):
    preimage = b"e" * 32
    payment_hash = hashlib.sha256(preimage).hexdigest()
    invoice = make_test_bolt11(
        payment_hash=payment_hash,
        amount_msat=amount,
        network="lightning-mainnet",
        timestamp=datetime.now(UTC),
        description_hash="sha256:metadata",
    )
    payment = LNURLPaymentForVerification(
        "pay1",
        "lpay_1",
        invoice,
        amount,
        payment_hash,
        "lightning-mainnet",
        metadata_hash="sha256:metadata",
        plan_code=plan,
    )
    verify = LNURLVerifyService(repository=InMemoryLNURLVerifyRepository({"pay1": payment}), sources=[Source(invoice, preimage)])
    asyncio.run(verify.verify_payment("pay1"))
    priv, pub = keys()
    proof_service = LNURLPaymentProofService(
        verification_service=verify,
        repository=InMemoryLNURLPaymentProofRepository(),
        config=LNURLPaymentProofConfig(issuer_private_key=priv, issuer_public_key=pub),
    )
    proof = asyncio.run(
        proof_service.issue_payment_proof("pay1", payment_context=LNURLPaymentContext.SUBSCRIPTION, product_code=plan)
    )
    return proof_service, proof


def principal(mode=LNURLEntitlementBindingMode.AUTHENTICATED_CHECKOUT, h="hmac-sha256:principal"):
    return PrincipalReference(
        principal_hash=h,
        principal_type="lightning_wallet_principal",
        binding_mode=mode,
        auth_method="verified_lnurl_auth",
        verified_at=datetime.now(UTC),
        request_principal_hash=h,
        binding_verification_hash="sha256:auth",
    )


def service_for(proof_service, products=None, policy=None, cache=None):
    return LNURLEntitlementBindingService(
        payment_proof_service=proof_service,
        repository=InMemoryLNURLEntitlementBindingRepository(products=products),
        policy=policy or DefaultBindingPolicy(),
        cache_invalidator=cache,
    )


def test_authenticated_checkout_new_subscription_and_auditless_signature():
    proof_service, _ = make_proof(principal_hash="hmac-sha256:principal")
    svc = service_for(proof_service)
    result = asyncio.run(
        svc.bind_settled_payment_to_principal(
            payment_proof_id=next(iter(proof_service.repository._by_proof_id)),
            principal_reference=principal(),
            request_context=AccessRequestContext(pop_session_active=True),
        )
    )
    assert result.binding_status == "active"
    assert result.entitlement_status == "active"
    assert result.plan_code == "pro_pass"
    assert svc.verify_binding_integrity(result.binding_id)


def test_payerdata_auth_binding_requires_verified_auth_hash():
    proof_service, proof = make_proof()
    svc = service_for(proof_service)
    result = asyncio.run(
        svc.bind_settled_payment_to_principal(
            payment_proof_id=proof.proof_id,
            principal_reference=principal(LNURLEntitlementBindingMode.PAYERDATA_AUTH),
            request_context=AccessRequestContext(wallet_proof_fresh=True),
        )
    )
    assert result.binding_status == "active"


def test_anonymous_payment_creates_pending_reservation_then_activation_requires_wallet_proof():
    proof_service, proof = make_proof()
    svc = service_for(proof_service)
    reservation = asyncio.run(
        svc.bind_settled_payment_to_principal(payment_proof_id=proof.proof_id, principal_reference=None)
    )
    assert reservation.requires_wallet_activation
    assert reservation.activation_reference
    with pytest.raises(Exception):
        asyncio.run(
            svc.bind_settled_payment_to_principal(
                payment_proof_id=proof.proof_id,
                principal_reference=principal(LNURLEntitlementBindingMode.POST_PAYMENT_ACTIVATION),
                activation_reference=reservation.activation_reference,
                request_context=AccessRequestContext(wallet_proof_fresh=False),
            )
        )
    activated = asyncio.run(
        svc.bind_settled_payment_to_principal(
            payment_proof_id=proof.proof_id,
            principal_reference=principal(LNURLEntitlementBindingMode.POST_PAYMENT_ACTIVATION),
            activation_reference=reservation.activation_reference,
            request_context=AccessRequestContext(wallet_proof_fresh=True),
        )
    )
    assert activated.binding_status == "active"


def test_renewal_extends_and_upgrade_is_policy_gated():
    proof_service, proof = make_proof()
    svc = service_for(proof_service)
    p = principal(LNURLEntitlementBindingMode.PAYERDATA_AUTH)
    first = asyncio.run(svc.bind_settled_payment_to_principal(payment_proof_id=proof.proof_id, principal_reference=p))
    proof_service2, proof2 = make_proof()
    svc.payment_proof_service = proof_service2
    renewal = asyncio.run(
        svc.bind_settled_payment_to_principal(
            payment_proof_id=proof2.proof_id,
            principal_reference=p,
            operation_type=LNURLEntitlementOperationType.RENEWAL,
        )
    )
    assert renewal.binding_status == "renewal_applied"
    assert renewal.valid_until and first.valid_until and renewal.valid_until > first.valid_until
    proof_service3, proof3 = make_proof(plan="business_pass", amount=10000)
    svc.payment_proof_service = proof_service3
    with pytest.raises(LNURLBindingStepUpRequiredError):
        asyncio.run(
            svc.bind_settled_payment_to_principal(
                payment_proof_id=proof3.proof_id,
                principal_reference=p,
                operation_type=LNURLEntitlementOperationType.UPGRADE,
                request_context=AccessRequestContext(risk_level="high"),
            )
        )


def test_duplicate_idempotent_and_principal_mismatch_rejected():
    proof_service, proof = make_proof()
    svc = service_for(proof_service)
    first = asyncio.run(svc.bind_settled_payment_to_principal(payment_proof_id=proof.proof_id, principal_reference=principal(LNURLEntitlementBindingMode.PAYERDATA_AUTH)))
    second = asyncio.run(svc.bind_settled_payment_to_principal(payment_proof_id=proof.proof_id, principal_reference=principal(LNURLEntitlementBindingMode.PAYERDATA_AUTH)))
    assert second.idempotent_replay and second.binding_id == first.binding_id
    with pytest.raises(LNURLBindingPrincipalMismatchError):
        asyncio.run(svc.bind_settled_payment_to_principal(payment_proof_id=proof.proof_id, principal_reference=principal(LNURLEntitlementBindingMode.PAYERDATA_AUTH, "hmac-sha256:other")))


def test_invalid_amount_disabled_product_expired_activation_and_policy_denial():
    proof_service, proof = make_proof(amount=3000)
    disabled = LNURLSubscriptionProduct("pro_pass", "pro_pass", 4000, 30, enabled=False)
    svc = service_for(proof_service, products={"pro_pass": disabled})
    with pytest.raises(LNURLBindingProductDisabledError):
        asyncio.run(svc.bind_settled_payment_to_principal(payment_proof_id=proof.proof_id, principal_reference=principal()))
    product = LNURLSubscriptionProduct("pro_pass", "pro_pass", 4000, 30)
    svc = service_for(proof_service, products={"pro_pass": product})
    with pytest.raises(LNURLBindingAmountInvalidError):
        asyncio.run(svc.bind_settled_payment_to_principal(payment_proof_id=proof.proof_id, principal_reference=principal()))

    class DenyPolicy:
        def decide(self, context):
            return "deny", "lnurl_binding_policy_denied"

    proof_service2, proof2 = make_proof()
    svc2 = service_for(proof_service2, policy=DenyPolicy())
    with pytest.raises(LNURLBindingPolicyDeniedError):
        asyncio.run(svc2.bind_settled_payment_to_principal(payment_proof_id=proof2.proof_id, principal_reference=principal(LNURLEntitlementBindingMode.PAYERDATA_AUTH)))

    proof_service3, proof3 = make_proof()
    svc3 = LNURLEntitlementBindingService(
        payment_proof_service=proof_service3,
        repository=InMemoryLNURLEntitlementBindingRepository(),
        config=LNURLEntitlementBindingConfig(activation_ttl_seconds=-1),
    )
    reservation = asyncio.run(svc3.bind_settled_payment_to_principal(payment_proof_id=proof3.proof_id, principal_reference=None))
    with pytest.raises(LNURLBindingActivationExpiredError):
        asyncio.run(svc3.bind_settled_payment_to_principal(payment_proof_id=proof3.proof_id, principal_reference=principal(LNURLEntitlementBindingMode.POST_PAYMENT_ACTIVATION), activation_reference=reservation.activation_reference, request_context=AccessRequestContext(wallet_proof_fresh=True)))


def test_cache_invalidation_retryable_freeze_and_consumption():
    proof_service, proof = make_proof()
    touched = []
    svc = service_for(proof_service, cache=touched.append)
    result = asyncio.run(svc.bind_settled_payment_to_principal(payment_proof_id=proof.proof_id, principal_reference=principal(LNURLEntitlementBindingMode.PAYERDATA_AUTH)))
    assert touched == ["hmac-sha256:principal"]
    assert (proof.proof_id, "subscription_entitlement") in svc.repository.consumptions
    frozen = svc.freeze_invalid_binding(result.binding_id, "terminal_failure")
    assert frozen.status == LNURLEntitlementBindingState.FROZEN.value
