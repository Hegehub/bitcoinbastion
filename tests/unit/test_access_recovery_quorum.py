from app.domain.access.plans import PlanCode
from app.services.access.recovery_quorum import RecoveryFactorType, evaluate_recovery_quorum, recovery_quorum_profile


def test_lite_recovery_is_single_factor() -> None:
    profile = recovery_quorum_profile(PlanCode.LITE)
    assert profile.threshold == 1
    assert RecoveryFactorType.RECOVERY_PHRASE_12 in profile.allowed_factors


def test_pro_recovery_requires_two_of_three() -> None:
    profile = recovery_quorum_profile(PlanCode.PRO)
    assert profile.threshold == 2
    incomplete = evaluate_recovery_quorum(profile, [RecoveryFactorType.RECOVERY_PHRASE_24])
    assert incomplete.decision == "quorum_incomplete"
    satisfied = evaluate_recovery_quorum(profile, [RecoveryFactorType.RECOVERY_PHRASE_24, RecoveryFactorType.DESKTOP_VAULT])
    assert satisfied.decision == "allow"


def test_business_recovery_requires_two_of_three() -> None:
    profile = recovery_quorum_profile(PlanCode.BUSINESS)
    assert profile.threshold == 2
    assert evaluate_recovery_quorum(profile, [RecoveryFactorType.OWNER_VAULT]).decision == "quorum_incomplete"
    assert evaluate_recovery_quorum(profile, [RecoveryFactorType.OWNER_VAULT, RecoveryFactorType.ADMIN_VAULT]).decision == "allow"


def test_enterprise_recovery_requires_three_of_five() -> None:
    profile = recovery_quorum_profile(PlanCode.ENTERPRISE)
    assert profile.threshold == 3
    assert evaluate_recovery_quorum(profile, [RecoveryFactorType.OWNER_VAULT, RecoveryFactorType.ADMIN_VAULT]).decision == "quorum_incomplete"
    assert evaluate_recovery_quorum(profile, [RecoveryFactorType.OWNER_VAULT, RecoveryFactorType.ADMIN_VAULT, RecoveryFactorType.HARDWARE_KEY]).decision == "allow"
