from datetime import UTC, datetime

from app.domain.lnurl.withdraw_risk import LNURLWithdrawPurpose, LNURLWithdrawStatus
from app.services.lnurl.refund_accounting import InMemoryRefundAccountingService, RefundPaymentState
from app.services.lnurl.verification_sources import test_bolt11 as make_test_bolt11
from app.services.lnurl.withdraw_executor import IdempotentLNURLWithdrawExecutor
from app.services.lnurl.withdraw_invoice_validator import LNURLWithdrawInvoiceValidationRequest, LNURLWithdrawInvoiceValidator
from app.services.lnurl.withdraw_limits import LNURLWithdrawLimitConfig, LNURLWithdrawLimitEvaluator
from app.services.lnurl.withdraw_risk import LNURLWithdrawRiskContext, LNURLWithdrawRiskService


def test_full_risk_refund_flow_blocks_duplicate_payment():
    accounting = InMemoryRefundAccountingService()
    accounting.put_payment(RefundPaymentState("sha256:orig", 250_000))
    reserve = accounting.reserve_refund(original_payment_hash="sha256:orig", withdraw_request_id="w", amount_msat=100_000)
    risk = LNURLWithdrawRiskService(limits=LNURLWithdrawLimitEvaluator(LNURLWithdrawLimitConfig(enabled=True, mainnet_enabled=True)))
    context = LNURLWithdrawRiskContext("w", LNURLWithdrawPurpose.SUBSCRIPTION_REFUND, 100_000, "bitcoin-mainnet", principal_hash="sha256:p", original_payment_hash="sha256:orig", original_remaining_msat=150_000, pop_session_age_seconds=1, lnurl_auth_proof_age_seconds=1)
    assert risk.evaluate_request(context).allowed
    inv = make_test_bolt11(payment_hash="ph", amount_msat=100_000, network="bitcoin-mainnet", timestamp=datetime.now(UTC), expiry_seconds=600)
    valid = LNURLWithdrawInvoiceValidator().validate(LNURLWithdrawInvoiceValidationRequest(inv, "bitcoin-mainnet", 100_000))
    assert valid.allowed
    executor = IdempotentLNURLWithdrawExecutor()
    attempt = executor.enqueue_or_get(withdraw_request_id="w", invoice_hash=valid.invoice_hash, payment_hash_hash=valid.payment_hash_hash, approved_amount_msat=100_000, policy_hash="sha256:policy")
    duplicate = executor.enqueue_or_get(withdraw_request_id="w", invoice_hash=valid.invoice_hash, payment_hash_hash=valid.payment_hash_hash, approved_amount_msat=100_000, policy_hash="sha256:policy")
    assert attempt is duplicate
    executor.transition(attempt.idempotency_hash, LNURLWithdrawStatus.PAYMENT_IN_FLIGHT)
    executor.transition(attempt.idempotency_hash, LNURLWithdrawStatus.PAYMENT_SUCCEEDED)
    executor.transition(attempt.idempotency_hash, LNURLWithdrawStatus.SETTLEMENT_CONFIRMED)
    accounting.confirm_refund(reserve.reservation_id)
    assert accounting.remaining_refundable_amount_msat("sha256:orig") == 150_000
