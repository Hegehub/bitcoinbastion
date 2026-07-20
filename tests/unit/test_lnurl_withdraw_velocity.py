from app.services.lnurl.withdraw_velocity import InMemoryLNURLWithdrawVelocityTracker, LNURLWithdrawVelocityEvent


def test_daily_principal_velocity_limit_is_enforced():
    tracker = InMemoryLNURLWithdrawVelocityTracker()
    tracker.record(LNURLWithdrawVelocityEvent(900, "cashback", "bitcoin-testnet", principal_hash="h"))
    decision = tracker.evaluate(LNURLWithdrawVelocityEvent(200, "cashback", "bitcoin-testnet", principal_hash="h"), max_amount_24h_msat=1000)
    assert not decision.allowed


def test_duplicate_destination_invoice_rejected():
    tracker = InMemoryLNURLWithdrawVelocityTracker()
    tracker.record(LNURLWithdrawVelocityEvent(1, "cashback", "bitcoin-testnet", destination_invoice_hash="sha256:i"))
    assert not tracker.evaluate(LNURLWithdrawVelocityEvent(1, "cashback", "bitcoin-testnet", destination_invoice_hash="sha256:i")).allowed
