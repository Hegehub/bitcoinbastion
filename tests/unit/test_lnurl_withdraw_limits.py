from app.domain.lnurl.withdraw_risk import LNURLWithdrawPurpose, LNURLWithdrawRiskDecision
from app.services.lnurl.withdraw_limits import LNURLWithdrawLimitConfig, LNURLWithdrawLimitEvaluator, LNURLWithdrawLimitInput, LNURLWithdrawPurposeLimits


def evaluator(**overrides):
    return LNURLWithdrawLimitEvaluator(LNURLWithdrawLimitConfig(enabled=True, mainnet_enabled=True, **overrides))


def test_single_payout_under_all_limits_allowed():
    result = evaluator().evaluate(LNURLWithdrawLimitInput(LNURLWithdrawPurpose.CASHBACK, 1000, "bitcoin-mainnet"))
    assert result.allowed


def test_effective_limit_uses_most_restrictive_rule():
    result = evaluator(purpose_overrides={LNURLWithdrawPurpose.PAYREGISTER_REFUND: LNURLWithdrawPurposeLimits(cashier_max_msat=250_000)}).evaluate(
        LNURLWithdrawLimitInput(LNURLWithdrawPurpose.PAYREGISTER_REFUND, 200_000, "bitcoin-mainnet", role="cashier", original_remaining_msat=180_000)
    )
    assert not result.allowed
    assert result.effective_max_single_msat == 180_000


def test_global_daily_limit_enforced():
    result = evaluator(global_max_daily_msat=5000).evaluate(LNURLWithdrawLimitInput(LNURLWithdrawPurpose.CASHBACK, 1000, "bitcoin-mainnet", global_daily_used_msat=4501))
    assert result.decision == LNURLWithdrawRiskDecision.QUOTA_EXCEEDED


def test_administrative_payout_disabled_by_default_and_faucet_denied_on_mainnet():
    assert not evaluator().evaluate(LNURLWithdrawLimitInput(LNURLWithdrawPurpose.ADMINISTRATIVE_ADJUSTMENT, 1000, "bitcoin-mainnet")).allowed
    assert not evaluator().evaluate(LNURLWithdrawLimitInput(LNURLWithdrawPurpose.TESTNET_FAUCET, 1000, "bitcoin-mainnet")).allowed
