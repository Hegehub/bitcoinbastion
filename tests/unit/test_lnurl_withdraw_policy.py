from __future__ import annotations

from datetime import UTC, datetime
from dataclasses import replace

from app.services.access.policy_context import AccessPolicyContext
from app.services.lnurl.withdraw_policy import (
    FakeLNURLPayoutExecutor,
    LNURLPayoutActorType,
    LNURLPayoutPolicyContext,
    LNURLPayoutPolicyDecision,
    LNURLPayoutPolicyStage,
    LNURLPayoutPurpose,
    LNURLWithdrawPolicyLimits,
    LNURLWithdrawPolicyService,
    OriginalPaymentRefundState,
)


def access(role: str = "admin") -> AccessPolicyContext:
    return AccessPolicyContext(
        certificate_fingerprint="sha256:cert",
        pass_lookup_hash="hmac-sha256:pass",
        plan_code="enterprise_pass",
        effective_scopes={
            "refunds:subscription:create",
            "refunds:subscription:approve",
            "refunds:payregister:create",
            "refunds:payregister:approve",
            "payouts:partner:approve",
            "payouts:bounty:approve",
            "payouts:execute",
            "lnurl:withdraw:read",
            "lnurl:withdraw:create",
            "lnurl:withdraw:approve",
            "lnurl:withdraw:cancel",
            "payouts:cashback:create",
        },
        business_role=role,
        workspace_id_hash="hmac-sha256:workspace",
        metric_entitlements={"groups": []},
    )


def original(amount: int = 5_000_000, refunded: int = 0, workspace: str = "hmac-sha256:workspace") -> OriginalPaymentRefundState:
    return OriginalPaymentRefundState("sha256:proof", workspace, "hmac-sha256:principal", amount, refunded, datetime.now(UTC))


def ctx(**kwargs) -> LNURLPayoutPolicyContext:
    values = dict(
        stage=LNURLPayoutPolicyStage.REQUEST_CREATION,
        purpose=LNURLPayoutPurpose.SUBSCRIPTION_REFUND,
        actor_type=LNURLPayoutActorType.BUSINESS_ADMIN,
        amount_msat=50_000,
        access_context=access(),
        original_payment=original(),
        workspace_hash="hmac-sha256:workspace",
        business_role="admin",
        step_up_fresh=True,
    )
    values.update(kwargs)
    return LNURLPayoutPolicyContext(**values)


def test_unknown_payout_purpose_and_actor_denied() -> None:
    service = LNURLWithdrawPolicyService()
    decision = service.evaluate_request_creation(ctx(purpose="unknown"))
    assert decision.allowed is False
    assert decision.reason_code == "unknown_purpose_or_actor"
    assert service.evaluate_request_creation(ctx(actor_type="unknown")).allowed is False


def test_revocation_and_lockdown_deny_all_policy_stages() -> None:
    service = LNURLWithdrawPolicyService()
    for stage in LNURLPayoutPolicyStage:
        context = ctx(stage=stage, lockdown_active=True)
        decision = service._evaluate(context, stage, "test")
        assert decision.decision == LNURLPayoutPolicyDecision.LOCKDOWN_ACTIVE.value
        revoked = service._evaluate(ctx(stage=stage, revoked_targets=("session",)), stage, "test")
        assert revoked.decision == LNURLPayoutPolicyDecision.REVOKED.value


def test_low_risk_policy_allows_without_owner_quorum() -> None:
    service = LNURLWithdrawPolicyService()
    decision = service.evaluate_request_creation(
        ctx(purpose=LNURLPayoutPurpose.CASHBACK, actor_type=LNURLPayoutActorType.WALLET_PRINCIPAL, amount_msat=10_000, original_payment=None, access_context=access("admin"))
    )
    assert decision.allowed is True
    assert decision.risk_level == "low"


def test_high_risk_policy_requires_fresh_step_up_and_legacy_signature_rejected() -> None:
    service = LNURLWithdrawPolicyService()
    high = service.evaluate_request_creation(ctx(amount_msat=2_000_000, step_up_fresh=False))
    assert high.decision == LNURLPayoutPolicyDecision.STEP_UP_REQUIRED.value
    legacy = service.evaluate_request_creation(ctx(amount_msat=2_000_000, step_up_fresh=True, legacy_signature=True))
    assert legacy.decision == LNURLPayoutPolicyDecision.STEP_UP_REQUIRED.value


def test_critical_payout_requires_human_intent_and_quorum() -> None:
    service = LNURLWithdrawPolicyService(limits=LNURLWithdrawPolicyLimits(global_max_msat=25_000_000, rolling_1h_max_msat=25_000_000, daily_max_msat=25_000_000))
    critical = ctx(purpose=LNURLPayoutPurpose.BUG_BOUNTY, actor_type=LNURLPayoutActorType.BUG_BOUNTY_REVIEWER, amount_msat=10_000_000, original_payment=None, access_context=access(), step_up_fresh=True)
    assert service.evaluate_request_creation(critical).decision == LNURLPayoutPolicyDecision.STEP_UP_REQUIRED.value
    with_intent = service.evaluate_request_creation(replace(critical, human_intent_verified=True))
    assert with_intent.decision == LNURLPayoutPolicyDecision.QUORUM_REQUIRED.value
    approved = service.evaluate_request_creation(replace(critical, human_intent_verified=True, quorum_approved=True))
    assert approved.allowed is True


def test_amount_and_rolling_limits_denied() -> None:
    service = LNURLWithdrawPolicyService(limits=LNURLWithdrawPolicyLimits(daily_max_msat=60_000, rolling_1h_max_msat=60_000))
    assert service.evaluate_request_creation(ctx(amount_msat=20_000_000)).decision == LNURLPayoutPolicyDecision.AMOUNT_EXCEEDED.value
    assert service.evaluate_request_creation(ctx(daily_amount_used_msat=20_000, rolling_amount_used_msat=50_000)).decision == LNURLPayoutPolicyDecision.QUOTA_EXCEEDED.value


def test_actor_boundaries_system_job_cashier_and_device() -> None:
    service = LNURLWithdrawPolicyService()
    assert service.evaluate_request_creation(ctx(actor_type=LNURLPayoutActorType.SYSTEM_JOB)).reason_code == "system_job_cannot_approve_own_payout"
    assert service.evaluate_request_creation(ctx(actor_type=LNURLPayoutActorType.CASHIER, purpose=LNURLPayoutPurpose.SUBSCRIPTION_REFUND)).reason_code == "cashier_scope_limited_to_payregister_refund"
    assert service.evaluate_request_creation(ctx(actor_type=LNURLPayoutActorType.PAYREGISTER_DEVICE, purpose=LNURLPayoutPurpose.PARTNER_PAYOUT, original_payment=None)).reason_code == "payregister_device_cannot_approve_owner_payout"


def test_execution_requires_prior_policy_approval_and_executor_idempotency() -> None:
    executor = FakeLNURLPayoutExecutor()
    service = LNURLWithdrawPolicyService(executor=executor)
    no_approval = service.enqueue_payment(ctx(stage=LNURLPayoutPolicyStage.PAYMENT_EXECUTION, invoice_hash="sha256:invoice", payment_hash_hash="hmac-sha256:pay", payment_execution_id="exec1"))
    assert no_approval.queued is False
    approved_ctx = ctx(stage=LNURLPayoutPolicyStage.PAYMENT_EXECUTION, invoice_hash="sha256:invoice", payment_hash_hash="hmac-sha256:pay", payment_execution_id="exec1", policy_approval_id="approval1")
    first = service.enqueue_payment(approved_ctx)
    second = service.enqueue_payment(approved_ctx)
    assert first.queued is True
    assert second.queued is True
    assert len(executor.enqueued) == 1


def test_retry_requires_policy_decision() -> None:
    service = LNURLWithdrawPolicyService()
    retry = service.evaluate_retry(ctx(stage=LNURLPayoutPolicyStage.RETRY, step_up_fresh=True))
    assert retry.allowed is True
