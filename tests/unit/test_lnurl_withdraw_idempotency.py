import pytest

from app.domain.lnurl.withdraw_risk import LNURLWithdrawFailureCategory, LNURLWithdrawStatus
from app.services.lnurl.withdraw_executor import IdempotentLNURLWithdrawExecutor, WithdrawExecutionError


def test_reused_callback_does_not_create_duplicate_payment():
    executor = IdempotentLNURLWithdrawExecutor()
    first = executor.enqueue_or_get(withdraw_request_id="w", invoice_hash="sha256:i", payment_hash_hash="hmac:p", approved_amount_msat=1000, policy_hash="sha256:policy")
    second = executor.enqueue_or_get(withdraw_request_id="w", invoice_hash="sha256:i", payment_hash_hash="hmac:p", approved_amount_msat=1000, policy_hash="sha256:policy")
    assert first is second


def test_provider_timeout_does_not_settle_or_blind_retry():
    executor = IdempotentLNURLWithdrawExecutor()
    attempt = executor.enqueue_or_get(withdraw_request_id="w", invoice_hash="sha256:i", payment_hash_hash="hmac:p", approved_amount_msat=1000, policy_hash="sha256:policy")
    timeout = executor.provider_timeout(attempt.idempotency_hash)
    assert timeout.status == LNURLWithdrawStatus.PAYMENT_IN_FLIGHT
    assert timeout.failure_category == LNURLWithdrawFailureCategory.PROVIDER_TIMEOUT
    assert timeout.reconciliation_required


def test_illegal_state_transition_fails():
    executor = IdempotentLNURLWithdrawExecutor()
    attempt = executor.enqueue_or_get(withdraw_request_id="w", invoice_hash="sha256:i", payment_hash_hash="hmac:p", approved_amount_msat=1000, policy_hash="sha256:policy")
    with pytest.raises(WithdrawExecutionError):
        executor.transition(attempt.idempotency_hash, LNURLWithdrawStatus.SETTLEMENT_CONFIRMED)
