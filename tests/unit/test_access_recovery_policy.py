from datetime import UTC, datetime, timedelta

from app.services.access.recovery_policy import RecoveryPolicy
from app.services.access.recovery_quorum import RecoveryQuorumEvaluation


def _quorum(decision: str = "allow") -> RecoveryQuorumEvaluation:
    return RecoveryQuorumEvaluation("satisfied" if decision == "allow" else "incomplete", 2, ["a", "b"] if decision == "allow" else ["a"], [], decision, "reason")


def test_cooldown_enforced() -> None:
    decision = RecoveryPolicy().evaluate_completion(quorum=_quorum(), cooldown_until=datetime.now(UTC) + timedelta(seconds=60), failed_factor_count=0)
    assert decision.decision == "cooldown_required"


def test_quorum_incomplete_denies() -> None:
    decision = RecoveryPolicy().evaluate_completion(quorum=_quorum("quorum_incomplete"), cooldown_until=None, failed_factor_count=0)
    assert decision.allowed is False
    assert decision.decision == "quorum_incomplete"


def test_repeated_failed_attempts_locked() -> None:
    decision = RecoveryPolicy(max_attempts_per_hour=2).evaluate_factor(factor_valid=False, failed_factor_count=2)
    assert decision.decision == "recovery_locked"


def test_issuer_policy_required_for_enterprise() -> None:
    decision = RecoveryPolicy().evaluate_completion(quorum=_quorum(), cooldown_until=None, failed_factor_count=0, issuer_policy_required=True, issuer_policy_satisfied=False)
    assert decision.decision == "issuer_policy_required"
