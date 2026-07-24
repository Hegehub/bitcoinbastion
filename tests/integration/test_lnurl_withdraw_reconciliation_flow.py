from app.domain.lnurl.withdraw_risk import LNURLWithdrawFailureCategory, LNURLWithdrawStatus
from app.services.lnurl.withdraw_executor import IdempotentLNURLWithdrawExecutor
from app.services.lnurl.withdraw_reconciliation import LNURLWithdrawReconciliationService, LocalWithdrawPaymentState, ProviderWithdrawPaymentState


def test_provider_timeout_requires_reconciliation_before_retry():
    executor = IdempotentLNURLWithdrawExecutor()
    attempt = executor.enqueue_or_get(withdraw_request_id="w", invoice_hash="sha256:i", payment_hash_hash="hmac:p", approved_amount_msat=1000, policy_hash="sha256:policy")
    executor.provider_timeout(attempt.idempotency_hash)
    assert attempt.reconciliation_required
    result = LNURLWithdrawReconciliationService().reconcile(LocalWithdrawPaymentState("w", attempt.status, 1000, "hmac:p"), ProviderWithdrawPaymentState(found=True, settled=False, failed=False, amount_msat=1000, payment_hash_hash="hmac:p"))
    assert result.outcome == "still_pending"
    assert result.next_status == LNURLWithdrawStatus.PAYMENT_IN_FLIGHT
    assert attempt.failure_category == LNURLWithdrawFailureCategory.PROVIDER_TIMEOUT
