from datetime import UTC, datetime, timedelta
import base64

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.domain.access.plans import PlanCode
from app.domain.access.wallet_entitlements import EntitlementSubjectType, WalletEntitlementStatus
from app.services.access.wallet_entitlement_service import EntitlementPolicyError, IssuerContext, PrincipalState, VerifiedPaymentProofRef, WalletBoundSubscriptionEntitlementService


def ctx():
    key = Ed25519PrivateKey.generate()
    private = key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
    return IssuerContext(base64.urlsafe_b64encode(private).decode().rstrip("="), "issuer-1")


def entitlement(service, issuer_ctx):
    return service.issue_wallet_bound_entitlement(principal=PrincipalState("hmac-sha256:p", EntitlementSubjectType.BITCOIN_WALLET_PRINCIPAL), verified_payment_proof=VerifiedPaymentProofRef("sha256:p", "plus_pass", 1, "bitcoin-mainnet", True, True, None, "hmac-sha256:p"), plan_code="plus_pass", payment_method="lnurl_pay", valid_from=datetime.now(UTC), valid_until=datetime.now(UTC)+timedelta(days=1), issuer_context=issuer_ctx)


def test_upgrade_requires_payment_and_step_up_and_does_not_broaden_child_keys():
    issuer_ctx = ctx()
    service = WalletBoundSubscriptionEntitlementService()
    ent = entitlement(service, issuer_ctx)
    with pytest.raises(EntitlementPolicyError, match="upgrade_step_up_required"):
        service.upgrade_entitlement(ent, new_plan_code=PlanCode.PRO, payment_proof=VerifiedPaymentProofRef("sha256:up", "pro_pass", 1, "bitcoin-mainnet", True, True), issuer_context=issuer_ctx)
    upgraded = service.upgrade_entitlement(ent, new_plan_code=PlanCode.PRO, payment_proof=VerifiedPaymentProofRef("sha256:up", "pro_pass", 1, "bitcoin-mainnet", True, True), issuer_context=issuer_ctx, step_up_fresh=True)
    assert upgraded.plan_code == "pro_pass"
    assert upgraded.metadata.get("child_keys_not_modified") is None


def test_downgrade_freezes_incompatible_children_and_schedule_state():
    issuer_ctx = ctx()
    service = WalletBoundSubscriptionEntitlementService()
    ent = entitlement(service, issuer_ctx)
    scheduled = service.schedule_downgrade(ent, new_plan_code="basic_pass", effective_at=datetime.now(UTC)+timedelta(days=1), issuer_context=issuer_ctx)
    assert scheduled.status == WalletEntitlementStatus.DOWNGRADE_PENDING
    downgraded = service.apply_downgrade(ent, new_plan_code="basic_pass", issuer_context=issuer_ctx, child_hashes=["sha256:child"])
    assert downgraded.plan_code == "basic_pass"
    assert "sha256:child" in service.repository.frozen_children[ent.entitlement_id_hash]
