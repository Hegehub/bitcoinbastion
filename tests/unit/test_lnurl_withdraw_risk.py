from app.domain.lnurl.withdraw_risk import LNURLWithdrawPurpose, LNURLWithdrawRiskDecision
from app.services.lnurl.withdraw_cooldown import InMemoryLNURLWithdrawCooldownService
from app.services.lnurl.withdraw_limits import LNURLWithdrawLimitConfig, LNURLWithdrawLimitEvaluator
from app.services.lnurl.withdraw_risk import LNURLWithdrawRiskContext, LNURLWithdrawRiskService


def risk_service():
    return LNURLWithdrawRiskService(limits=LNURLWithdrawLimitEvaluator(LNURLWithdrawLimitConfig(enabled=True, mainnet_enabled=True, global_max_single_msat=10_000_000)))


def ctx(**kw):
    values = dict(withdraw_id="w", purpose=LNURLWithdrawPurpose.CASHBACK, amount_msat=1000, network="bitcoin-mainnet", principal_hash="sha256:p", pop_session_age_seconds=10)
    values.update(kw)
    return LNURLWithdrawRiskContext(**values)


def test_single_payout_under_all_limits_is_allowed_and_hashes_policy():
    result = risk_service().evaluate_request(ctx())
    assert result.allowed
    assert result.policy_hash.startswith("sha256:")


def test_high_value_payout_requires_step_up_and_manual_review():
    assert risk_service().evaluate_request(ctx(amount_msat=2_000_000)).decision == LNURLWithdrawRiskDecision.STEP_UP_REQUIRED
    assert risk_service().evaluate_request(ctx(amount_msat=6_000_000, lnurl_auth_proof_age_seconds=1)).decision == LNURLWithdrawRiskDecision.MANUAL_REVIEW_REQUIRED


def test_revoked_and_lockdown_deny():
    assert risk_service().evaluate_request(ctx(revoked=True)).decision == LNURLWithdrawRiskDecision.REVOKED
    assert risk_service().evaluate_request(ctx(lockdown=True)).decision == LNURLWithdrawRiskDecision.LOCKDOWN


def test_cooldown_blocks_recent_recovery():
    cooldown = InMemoryLNURLWithdrawCooldownService()
    cooldown.add_cooldown(subject_hash="sha256:p", reason_code="recent_recovery_completion", seconds=60)
    result = LNURLWithdrawRiskService(limits=LNURLWithdrawLimitEvaluator(LNURLWithdrawLimitConfig(enabled=True, mainnet_enabled=True)), cooldown=cooldown).evaluate_request(ctx())
    assert result.decision == LNURLWithdrawRiskDecision.COOLDOWN_REQUIRED
