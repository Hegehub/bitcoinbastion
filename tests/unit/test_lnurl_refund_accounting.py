from concurrent.futures import ThreadPoolExecutor

import pytest

from app.services.lnurl.refund_accounting import InMemoryRefundAccountingService, RefundAccountingError, RefundPaymentState


def service():
    s = InMemoryRefundAccountingService()
    s.put_payment(RefundPaymentState("sha256:orig", 1000))
    return s


def test_refund_above_remaining_balance_denied():
    with pytest.raises(RefundAccountingError, match="refund_balance_exceeded"):
        service().reserve_refund(original_payment_hash="sha256:orig", withdraw_request_id="w1", amount_msat=1001)


def test_failed_terminal_payout_releases_reservation_but_timeout_does_not():
    s = service()
    r = s.reserve_refund(original_payment_hash="sha256:orig", withdraw_request_id="w1", amount_msat=700)
    with pytest.raises(RefundAccountingError, match="ambiguous_payment_retains_reservation"):
        s.release_reservation(r.reservation_id, terminal_failure=False)
    assert s.remaining_refundable_amount_msat("sha256:orig") == 300
    s.release_reservation(r.reservation_id)
    assert s.remaining_refundable_amount_msat("sha256:orig") == 1000


def test_two_concurrent_refunds_cannot_over_reserve():
    s = service()
    def reserve(i):
        try:
            s.reserve_refund(original_payment_hash="sha256:orig", withdraw_request_id=f"w{i}", amount_msat=700)
            return True
        except RefundAccountingError:
            return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(reserve, [1, 2])) == 1
