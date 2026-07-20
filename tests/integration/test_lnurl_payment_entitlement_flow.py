from __future__ import annotations

import asyncio

import pytest

from app.services.lnurl.entitlement_binding_service import (
    AccessRequestContext,
    InMemoryLNURLEntitlementBindingRepository,
    LNURLEntitlementBindingMode,
    LNURLEntitlementBindingService,
    LNURLEntitlementOperationType,
)
from app.services.lnurl.errors import LNURLBindingStepUpRequiredError
from tests.unit.test_lnurl_entitlement_binding_service import make_proof, principal


def test_lnurl_payment_to_entitlement_full_flow_and_replay_no_duplicate():
    proof_service, proof = make_proof()
    repo = InMemoryLNURLEntitlementBindingRepository()
    service = LNURLEntitlementBindingService(payment_proof_service=proof_service, repository=repo)
    # Invoice issuance alone was not enough: entitlement repository is empty before proof binding.
    assert repo.entitlements_by_principal == {}
    result = asyncio.run(
        service.bind_settled_payment_to_principal(
            payment_proof_id=proof.proof_id,
            principal_reference=principal(LNURLEntitlementBindingMode.PAYERDATA_AUTH),
            request_context=AccessRequestContext(wallet_proof_fresh=True),
        )
    )
    assert result.entitlement_status == "active"
    assert result.policy_refresh_required
    assert repo.consumptions[(proof.proof_id, "subscription_entitlement")] == result.binding_id
    replay = asyncio.run(
        service.bind_settled_payment_to_principal(
            payment_proof_id=proof.proof_id,
            principal_reference=principal(LNURLEntitlementBindingMode.PAYERDATA_AUTH),
        )
    )
    assert replay.idempotent_replay and replay.entitlement_id == result.entitlement_id
    assert len(repo.entitlements_by_principal) == 1


def test_anonymous_payment_reservation_then_fresh_lnurl_auth_activation():
    proof_service, proof = make_proof()
    service = LNURLEntitlementBindingService(payment_proof_service=proof_service)
    reservation = asyncio.run(service.bind_settled_payment_to_principal(payment_proof_id=proof.proof_id, principal_reference=None))
    assert reservation.requires_wallet_activation and reservation.entitlement_id is None
    activated = asyncio.run(
        service.bind_settled_payment_to_principal(
            payment_proof_id=proof.proof_id,
            principal_reference=principal(LNURLEntitlementBindingMode.POST_PAYMENT_ACTIVATION),
            activation_reference=reservation.activation_reference,
            request_context=AccessRequestContext(wallet_proof_fresh=True),
        )
    )
    assert activated.binding_status == "active"
    assert activated.entitlement_id


def test_upgrade_payment_requires_step_up_before_sensitive_plan_activation():
    proof_service, proof = make_proof(plan="business_pass", amount=10000)
    service = LNURLEntitlementBindingService(payment_proof_service=proof_service)
    with pytest.raises(LNURLBindingStepUpRequiredError):
        asyncio.run(
            service.bind_settled_payment_to_principal(
                payment_proof_id=proof.proof_id,
                principal_reference=principal(LNURLEntitlementBindingMode.PAYERDATA_AUTH),
                operation_type=LNURLEntitlementOperationType.UPGRADE,
                request_context=AccessRequestContext(risk_level="high"),
            )
        )
