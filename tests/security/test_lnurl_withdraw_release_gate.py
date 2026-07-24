import pytest

from app.domain.lnurl.withdraw_risk import LNURLWithdrawPurpose, LNURLWithdrawRiskDecision
from app.services.lnurl.metrics import LNURLWithdrawMetrics
from app.services.lnurl.withdraw_limits import LNURLWithdrawLimitConfig, LNURLWithdrawLimitEvaluator, LNURLWithdrawLimitInput
from app.services.lnurl.withdraw_risk import LNURLWithdrawRiskContext, LNURLWithdrawRiskService


def test_release_gate_fails_closed_for_mainnet_and_admin_adjustment():
    evaluator = LNURLWithdrawLimitEvaluator(LNURLWithdrawLimitConfig(enabled=True, mainnet_enabled=False))
    assert not evaluator.evaluate(LNURLWithdrawLimitInput(LNURLWithdrawPurpose.CASHBACK, 1000, "bitcoin-mainnet")).allowed
    evaluator = LNURLWithdrawLimitEvaluator(LNURLWithdrawLimitConfig(enabled=True, mainnet_enabled=True))
    assert not evaluator.evaluate(LNURLWithdrawLimitInput(LNURLWithdrawPurpose.ADMINISTRATIVE_ADJUSTMENT, 1000, "bitcoin-mainnet")).allowed


def test_valid_k1_alone_cannot_authorize_payout_or_bypass_policy():
    service = LNURLWithdrawRiskService(limits=LNURLWithdrawLimitEvaluator(LNURLWithdrawLimitConfig(enabled=True, mainnet_enabled=True)))
    result = service.evaluate_request(LNURLWithdrawRiskContext("w", LNURLWithdrawPurpose.CASHBACK, 2_000_000, "bitcoin-mainnet", principal_hash="sha256:p", pop_session_age_seconds=1))
    assert result.decision == LNURLWithdrawRiskDecision.STEP_UP_REQUIRED


def test_lockdown_and_revocation_block_payouts():
    service = LNURLWithdrawRiskService(limits=LNURLWithdrawLimitEvaluator(LNURLWithdrawLimitConfig(enabled=True, mainnet_enabled=True)))
    assert service.evaluate_execution(LNURLWithdrawRiskContext("w", LNURLWithdrawPurpose.CASHBACK, 1000, "bitcoin-mainnet", lockdown=True)).decision == LNURLWithdrawRiskDecision.LOCKDOWN
    assert service.evaluate_execution(LNURLWithdrawRiskContext("w", LNURLWithdrawPurpose.CASHBACK, 1000, "bitcoin-mainnet", revoked=True)).decision == LNURLWithdrawRiskDecision.REVOKED


def test_metrics_reject_sensitive_high_cardinality_labels():
    metrics = LNURLWithdrawMetrics()
    metrics.record("bastion_lnurl_withdraw_denied_total", {"purpose": "cashback", "decision": "deny"})
    with pytest.raises(ValueError):
        metrics.record("bastion_lnurl_withdraw_denied_total", {"invoice": "lnbc..."})
