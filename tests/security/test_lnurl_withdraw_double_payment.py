from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

from app.services.access.policy_context import AccessPolicyContext
from app.services.lnurl.withdraw_policy import FakeLNURLPayoutExecutor, LNURLPayoutActorType, LNURLPayoutPolicyContext, LNURLPayoutPolicyStage, LNURLPayoutPurpose, LNURLWithdrawPolicyLimits, LNURLWithdrawPolicyService, OriginalPaymentRefundState


def ctx(execution_id="exec", payment_hash="hmac-sha256:pay", amount=50_000):
    return LNURLPayoutPolicyContext(stage=LNURLPayoutPolicyStage.PAYMENT_EXECUTION, purpose=LNURLPayoutPurpose.SUBSCRIPTION_REFUND, actor_type=LNURLPayoutActorType.BUSINESS_ADMIN, amount_msat=amount, access_context=AccessPolicyContext(certificate_fingerprint="sha256:c", pass_lookup_hash="hmac-sha256:p", plan_code="enterprise_pass", effective_scopes={"payouts:execute"}, metric_entitlements={"groups": []}), original_payment=OriginalPaymentRefundState("sha256:proof", None, None, amount), step_up_fresh=True, invoice_hash="sha256:invoice", payment_hash_hash=payment_hash, payment_execution_id=execution_id, policy_approval_id="approval")


def test_same_payment_hash_cannot_be_marked_paid_twice() -> None:
    service = LNURLWithdrawPolicyService(executor=FakeLNURLPayoutExecutor())
    assert service.enqueue_payment(ctx()).queued is True
    service.record_paid("hmac-sha256:pay", execution_id="exec")
    try:
        service.record_paid("hmac-sha256:pay", execution_id="exec")
    except ValueError as exc:
        assert str(exc) == "payment_hash_duplicate"
    else:  # pragma: no cover
        raise AssertionError("duplicate payment hash should fail")


def test_reused_callback_cannot_enqueue_twice_for_one_execution_id() -> None:
    executor = FakeLNURLPayoutExecutor()
    service = LNURLWithdrawPolicyService(executor=executor)
    assert service.enqueue_payment(ctx()).queued is True
    assert service.enqueue_payment(ctx()).queued is True
    assert len(executor.enqueued) == 1


def test_concurrent_requests_cannot_exceed_amount_limits() -> None:
    service = LNURLWithdrawPolicyService(limits=LNURLWithdrawPolicyLimits(daily_max_msat=60_000, rolling_1h_max_msat=60_000))
    contexts = [ctx(execution_id=f"exec{i}", payment_hash=f"hmac-sha256:pay{i}", amount=50_000) for i in range(3)]
    with ThreadPoolExecutor(max_workers=3) as pool:
        decisions = list(pool.map(lambda c: service.evaluate_request_creation(replace(c, daily_amount_used_msat=20_000)), contexts))
    assert all(d.decision == "quota_exceeded" for d in decisions)
