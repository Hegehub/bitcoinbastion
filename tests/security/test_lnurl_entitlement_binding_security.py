from __future__ import annotations

import asyncio

import pytest

from app.domain.lnurl.payment_proofs import LNURLPaymentProofStatus
from app.services.lnurl.entitlement_binding_service import (
    AccessRequestContext,
    InMemoryLNURLEntitlementBindingRepository,
    LNURLEntitlementBindingMode,
    LNURLEntitlementBindingService,
    LNURLSubscriptionProduct,
    PrincipalReference,
)
from app.services.lnurl.errors import (
    LNURLBindingAmountInvalidError,
    LNURLBindingPolicyDeniedError,
    LNURLBindingPrincipalMismatchError,
    LNURLBindingPrincipalRequiredError,
    LNURLPaymentNotSettledError,
    LNURLPaymentProofInvalidError,
    LNURLPaymentProofRevokedBindingError,
)
from tests.unit.test_lnurl_entitlement_binding_service import make_proof, principal


def bind(service, proof_id, principal_ref=None, activation=None, context=None):
    return asyncio.run(
        service.bind_settled_payment_to_principal(
            payment_proof_id=proof_id,
            principal_reference=principal_ref,
            activation_reference=activation,
            request_context=context or AccessRequestContext(pop_session_active=True),
        )
    )


def test_invoice_issuance_or_unsettled_payment_cannot_create_entitlement():
    proof_service, proof = make_proof()
    proof_service.repository.update(__import__("dataclasses").replace(proof, settled=False))
    service = LNURLEntitlementBindingService(payment_proof_service=proof_service)
    with pytest.raises(LNURLPaymentNotSettledError):
        bind(service, proof.proof_id, principal())


def test_invalid_or_revoked_payment_proof_cannot_create_entitlement():
    proof_service, proof = make_proof()
    tampered = __import__("dataclasses").replace(proof, amount_msat=proof.amount_msat + 1)
    proof_service.repository.update(tampered)
    service = LNURLEntitlementBindingService(payment_proof_service=proof_service)
    with pytest.raises(LNURLPaymentProofInvalidError):
        bind(service, proof.proof_id, principal())
    proof_service2, proof2 = make_proof()
    proof_service2.repository.update(__import__("dataclasses").replace(proof2, status=LNURLPaymentProofStatus.REVOKED.value))
    service2 = LNURLEntitlementBindingService(payment_proof_service=proof_service2)
    with pytest.raises(LNURLPaymentProofRevokedBindingError):
        bind(service2, proof2.proof_id, principal())


def test_payment_hash_preimage_activation_reference_email_comment_and_lightning_address_are_not_identity():
    proof_service, proof = make_proof()
    service = LNURLEntitlementBindingService(payment_proof_service=proof_service)
    reservation = bind(service, proof.proof_id, None)
    assert reservation.activation_reference
    replay = bind(service, proof.proof_id, None, activation=reservation.activation_reference)
    assert replay.entitlement_id is None and replay.requires_wallet_activation
    for fake in ["payment_hash", "preimage", "person@example.com", "comment says paid", "alice@example.com"]:
        bad = PrincipalReference(fake, "lightning_address", LNURLEntitlementBindingMode.POST_PAYMENT_ACTIVATION, "unverified", __import__("datetime").datetime.now(__import__("datetime").UTC))
        with pytest.raises(LNURLBindingPrincipalRequiredError):
            bind(service, proof.proof_id, bad, activation=reservation.activation_reference, context=AccessRequestContext(wallet_proof_fresh=True))


def test_different_principal_duplicate_and_concurrent_binding_cannot_issue_twice():
    proof_service, proof = make_proof()
    service = LNURLEntitlementBindingService(payment_proof_service=proof_service)
    first = bind(service, proof.proof_id, principal(LNURLEntitlementBindingMode.PAYERDATA_AUTH))
    second = bind(service, proof.proof_id, principal(LNURLEntitlementBindingMode.PAYERDATA_AUTH))
    assert second.idempotent_replay and first.entitlement_id == second.entitlement_id
    with pytest.raises(LNURLBindingPrincipalMismatchError):
        bind(service, proof.proof_id, principal(LNURLEntitlementBindingMode.PAYERDATA_AUTH, "hmac-sha256:attacker"))


def test_underpayment_disabled_product_revoked_principal_and_policy_cannot_be_bypassed():
    proof_service, proof = make_proof(amount=3000)
    product = LNURLSubscriptionProduct("pro_pass", "pro_pass", 4000, 30)
    service = LNURLEntitlementBindingService(
        payment_proof_service=proof_service,
        repository=InMemoryLNURLEntitlementBindingRepository(products={"pro_pass": product}),
    )
    with pytest.raises(LNURLBindingAmountInvalidError):
        bind(service, proof.proof_id, principal())
    proof_service2, proof2 = make_proof()
    bad_principal = principal()
    bad_principal = __import__("dataclasses").replace(bad_principal, principal_status="revoked")
    service2 = LNURLEntitlementBindingService(payment_proof_service=proof_service2)
    with pytest.raises(LNURLBindingPolicyDeniedError):
        bind(service2, proof2.proof_id, bad_principal)


def test_raw_secrets_are_not_in_binding_records_or_results():
    proof_service, proof = make_proof()
    service = LNURLEntitlementBindingService(payment_proof_service=proof_service)
    result = bind(service, proof.proof_id, principal(LNURLEntitlementBindingMode.PAYERDATA_AUTH))
    rendered = repr(result) + repr(service.resolve_payment_binding(proof.proof_id))
    for forbidden in ["lnbc", "preimage", "raw_activation", "wallet_seed", "xprv", "session_token"]:
        assert forbidden not in rendered.lower()
