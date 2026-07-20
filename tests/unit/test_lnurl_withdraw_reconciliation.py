from app.domain.lnurl.withdraw_risk import LNURLWithdrawStatus
from app.services.lnurl.withdraw_reconciliation import LNURLWithdrawReconciliationService, LocalWithdrawPaymentState, ProviderWithdrawPaymentState


def local():
    return LocalWithdrawPaymentState("sha256:w", LNURLWithdrawStatus.PAYMENT_IN_FLIGHT, 1000, "hmac:p")


def test_reconciliation_confirms_settlement_and_detects_mismatch():
    service = LNURLWithdrawReconciliationService()
    ok = service.reconcile(local(), ProviderWithdrawPaymentState(found=True, settled=True, amount_msat=1000, payment_hash_hash="hmac:p"))
    assert ok.outcome == "matched_settled"
    assert ok.next_status == LNURLWithdrawStatus.SETTLEMENT_CONFIRMED
    mismatch = service.reconcile(local(), ProviderWithdrawPaymentState(found=True, settled=True, amount_msat=2000, payment_hash_hash="hmac:p"))
    assert mismatch.outcome == "amount_mismatch"


def test_duplicate_provider_payment_produces_alert_state():
    result = LNURLWithdrawReconciliationService().reconcile(local(), ProviderWithdrawPaymentState(found=True, duplicate_count=2, amount_msat=1000, payment_hash_hash="hmac:p"))
    assert result.outcome == "duplicate_payment_detected"
