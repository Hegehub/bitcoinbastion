from __future__ import annotations

import asyncio
from dataclasses import asdict

from app.services.lnurl.entitlement_binding_service import LNURLEntitlementBindingMode
from tests.unit.test_lnurl_entitlement_binding_service import make_proof, principal, service_for


def test_lnurl_entitlement_binding_result_contract_is_stable_and_safe():
    proof_service, proof = make_proof()
    service = service_for(proof_service)
    result = asyncio.run(
        service.bind_settled_payment_to_principal(
            payment_proof_id=proof.proof_id,
            principal_reference=principal(LNURLEntitlementBindingMode.PAYERDATA_AUTH),
        )
    )
    payload = asdict(result)
    assert set(payload) == {
        "binding_id",
        "payment_proof_fingerprint",
        "principal_hash",
        "principal_type",
        "plan_code",
        "entitlement_id",
        "entitlement_status",
        "binding_status",
        "operation_type",
        "valid_from",
        "valid_until",
        "requires_wallet_activation",
        "policy_refresh_required",
        "audit_event_hash",
        "idempotent_replay",
        "limitations",
        "activation_reference",
    }
    assert "invoice" not in repr(payload).lower()
    assert "preimage" not in repr(payload).lower()


def test_lnurl_entitlement_reservation_contract_is_stable_and_safe():
    proof_service, proof = make_proof()
    service = service_for(proof_service)
    result = asyncio.run(service.bind_settled_payment_to_principal(payment_proof_id=proof.proof_id, principal_reference=None))
    assert result.binding_status == "pending_principal"
    assert result.requires_wallet_activation
    assert result.entitlement_id is None
    assert result.activation_reference and result.activation_reference.startswith("lnact_")
