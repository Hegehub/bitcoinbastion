from app.services.lnurl.withdraw_cooldown import InMemoryLNURLWithdrawCooldownService


def test_recently_recovered_principal_receives_cooldown():
    service = InMemoryLNURLWithdrawCooldownService()
    service.add_cooldown(subject_hash="sha256:p", reason_code="recent_recovery_completion", seconds=60)
    decision = service.evaluate("sha256:p")
    assert not decision.allowed
    assert decision.reason_code == "recent_recovery_completion"
