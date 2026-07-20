from app.domain.lnurl.withdraw_risk import LNURLWithdrawPurpose
from app.services.lnurl.withdraw_limits import LNURLWithdrawLimitConfig, LNURLWithdrawLimitEvaluator, LNURLWithdrawLimitInput, LNURLWithdrawPurposeLimits


def test_payregister_cashier_limit_more_restrictive_than_merchant_limit():
    evaluator = LNURLWithdrawLimitEvaluator(
        LNURLWithdrawLimitConfig(
            enabled=True,
            mainnet_enabled=True,
            purpose_overrides={LNURLWithdrawPurpose.PAYREGISTER_REFUND: LNURLWithdrawPurposeLimits(cashier_max_msat=250_000, max_daily_merchant_msat=2_000_000)},
        )
    )
    result = evaluator.evaluate(LNURLWithdrawLimitInput(LNURLWithdrawPurpose.PAYREGISTER_REFUND, 300_000, "bitcoin-mainnet", role="cashier", original_remaining_msat=1_000_000))
    assert not result.allowed
    assert result.effective_max_single_msat == 250_000
