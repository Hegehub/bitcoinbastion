from app.domain.lnurl.withdraw_risk import LNURLWithdrawPurpose, LNURLWithdrawStatus, can_transition


def test_withdraw_risk_domain_contains_required_values():
    assert LNURLWithdrawPurpose.ADMINISTRATIVE_ADJUSTMENT.value == "administrative_adjustment"
    assert LNURLWithdrawStatus.PAYMENT_IN_FLIGHT.value == "payment_in_flight"
    assert LNURLWithdrawStatus.SETTLEMENT_CONFIRMED.value == "settlement_confirmed"


def test_illegal_terminal_transition_fails():
    assert can_transition(LNURLWithdrawStatus.PAYMENT_IN_FLIGHT, LNURLWithdrawStatus.PAYMENT_SUCCEEDED)
    assert not can_transition(LNURLWithdrawStatus.SETTLEMENT_CONFIRMED, LNURLWithdrawStatus.PAYMENT_QUEUED)
