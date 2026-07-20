from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.services.access.policy_context import AccessPolicyContext
from app.services.lnurl.withdraw_policy import LNURLPayoutActorType, LNURLPayoutPolicyContext, LNURLPayoutPolicyDecision, LNURLPayoutPolicyStage, LNURLPayoutPurpose, LNURLWithdrawPolicyService, OriginalPaymentRefundState


def access() -> AccessPolicyContext:
    return AccessPolicyContext(certificate_fingerprint="sha256:cert", pass_lookup_hash="hmac-sha256:pass", plan_code="enterprise_pass", effective_scopes={"refunds:subscription:create", "refunds:subscription:approve", "lnurl:withdraw:read"}, business_role="admin", metric_entitlements={"groups": []})


def ctx(**kwargs) -> LNURLPayoutPolicyContext:
    base = dict(stage=LNURLPayoutPolicyStage.REQUEST_CREATION, purpose=LNURLPayoutPurpose.SUBSCRIPTION_REFUND, actor_type=LNURLPayoutActorType.BUSINESS_ADMIN, amount_msat=50_000, access_context=access(), workspace_hash="workspace:a", business_role="admin", step_up_fresh=True)
    base.update(kwargs)
    return LNURLPayoutPolicyContext(**base)


def payment(amount=100_000, refunded=0, workspace="workspace:a", days=30):
    return OriginalPaymentRefundState("sha256:proof", workspace, "principal", amount, refunded, datetime.now(UTC) - timedelta(days=1), days)


def test_refund_requires_original_payment_where_policy_says_so() -> None:
    assert LNURLWithdrawPolicyService().evaluate_request_creation(ctx(original_payment=None)).decision == "original_payment_required"


def test_refund_cannot_exceed_remaining_refundable_amount() -> None:
    decision = LNURLWithdrawPolicyService().evaluate_request_creation(ctx(original_payment=payment(refunded=75_000), amount_msat=50_000))
    assert decision.decision == LNURLPayoutPolicyDecision.AMOUNT_EXCEEDED.value


def test_partial_refunds_reduce_refundable_remainder_and_duplicate_full_refund_rejected() -> None:
    service = LNURLWithdrawPolicyService()
    state = payment()
    service.refund_ledger.put(state)
    updated = service.refund_ledger.reserve_refund(state.payment_proof_hash, 25_000)
    assert updated.remaining_refundable_msat == 75_000
    service.refund_ledger.reserve_refund(state.payment_proof_hash, 75_000)
    try:
        service.refund_ledger.reserve_refund(state.payment_proof_hash, 1)
    except ValueError as exc:
        assert str(exc) == "refund_limit_exceeded"
    else:  # pragma: no cover
        raise AssertionError("duplicate full refund should fail")


def test_unrelated_workspace_payment_rejected() -> None:
    decision = LNURLWithdrawPolicyService().evaluate_request_creation(ctx(original_payment=payment(workspace="workspace:b")))
    assert decision.decision == LNURLPayoutPolicyDecision.OBJECT_MISMATCH.value


def test_expired_refund_window_denied_or_escalated() -> None:
    expired = OriginalPaymentRefundState("sha256:proof", "workspace:a", "principal", 100_000, 0, datetime.now(UTC) - timedelta(days=60), 30)
    decision = LNURLWithdrawPolicyService().evaluate_request_creation(ctx(original_payment=expired))
    assert decision.decision == LNURLPayoutPolicyDecision.REFUND_WINDOW_EXPIRED.value


def test_payerdata_and_comment_cannot_establish_refund_ownership() -> None:
    decision = LNURLWithdrawPolicyService().evaluate_request_creation(ctx(original_payment=None, metadata={"payerData": "email@example.com", "comment": "refund me"}))
    assert decision.decision == LNURLPayoutPolicyDecision.ORIGINAL_PAYMENT_REQUIRED.value
