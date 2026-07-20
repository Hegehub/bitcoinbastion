from __future__ import annotations

from app.services.access.policy_context import AccessPolicyContext
from app.services.lnurl.withdraw_policy import LNURLPayoutActorType, LNURLPayoutPolicyContext, LNURLPayoutPolicyStage, LNURLPayoutPurpose, LNURLWithdrawPolicyService, OriginalPaymentRefundState


def access(role: str):
    return AccessPolicyContext(certificate_fingerprint="sha256:c", pass_lookup_hash="hmac-sha256:p", plan_code="enterprise_pass", effective_scopes={"refunds:payregister:create", "refunds:payregister:approve", "payouts:partner:approve", "payouts:execute", "lnurl:withdraw:read"}, business_role=role, metric_entitlements={"groups": []})


def ctx(actor, purpose, role="cashier", amount=50_000, step_up=True):
    return LNURLPayoutPolicyContext(stage=LNURLPayoutPolicyStage.REQUEST_CREATION, purpose=purpose, actor_type=actor, amount_msat=amount, access_context=access(role), business_role=role, original_payment=OriginalPaymentRefundState("sha256:proof", "workspace", None, amount), workspace_hash="workspace", step_up_fresh=step_up)


def test_cashier_cannot_approve_high_value_refund_or_other_workspace_payout() -> None:
    service = LNURLWithdrawPolicyService()
    high = service.evaluate_request_creation(ctx(LNURLPayoutActorType.CASHIER, LNURLPayoutPurpose.PAYREGISTER_REFUND, amount=2_000_000))
    assert high.reason_code == "cashier_cannot_approve_high_value_refund"
    other = service.evaluate_request_creation(ctx(LNURLPayoutActorType.CASHIER, LNURLPayoutPurpose.SUBSCRIPTION_REFUND))
    assert other.reason_code == "cashier_scope_limited_to_payregister_refund"


def test_payregister_device_cannot_approve_owner_payout() -> None:
    service = LNURLWithdrawPolicyService()
    decision = service.evaluate_request_creation(ctx(LNURLPayoutActorType.PAYREGISTER_DEVICE, LNURLPayoutPurpose.PARTNER_PAYOUT, role="device"))
    assert decision.reason_code == "payregister_device_cannot_approve_owner_payout"


def test_business_owner_still_subject_to_step_up_and_limits() -> None:
    service = LNURLWithdrawPolicyService()
    no_step = service.evaluate_request_creation(ctx(LNURLPayoutActorType.BUSINESS_OWNER, LNURLPayoutPurpose.PAYREGISTER_REFUND, role="owner", amount=2_000_000, step_up=False))
    assert no_step.decision == "step_up_required"
