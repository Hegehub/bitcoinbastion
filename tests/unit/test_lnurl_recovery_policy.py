from app.services.wallet_auth.recovery.models import RecoveryFactorType as F, RecoveryProfile
from app.services.wallet_auth.recovery.policy import PROFILE_REQUIREMENTS
from app.services.lnurl.metrics import LNURL_RECOVERY_METRICS


def test_lnurl_is_one_factor_and_profiles_keep_stronger_requirements() -> None:
    lite = PROFILE_REQUIREMENTS[RecoveryProfile.LITE_BASIC]
    assert F.LNURL_AUTH_PROOF in lite.principal_proof_one_of
    assert lite.required_factor_count == 2

    pro = PROFILE_REQUIREMENTS[RecoveryProfile.PRO]
    assert {F.RECOVERY_FILE, F.TRUSTED_DEVICE} <= pro.required_factors
    assert pro.required_factor_count >= 3

    business = PROFILE_REQUIREMENTS[RecoveryProfile.BUSINESS]
    assert F.LNURL_AUTH_PROOF in business.principal_proof_one_of
    assert F.BUSINESS_ROLE_QUORUM in business.required_factors
    assert business.requires_quorum and business.requires_dual_control

    enterprise = PROFILE_REQUIREMENTS[RecoveryProfile.ENTERPRISE]
    assert F.LNURL_AUTH_PROOF in enterprise.allowed_factors
    assert F.LNURL_AUTH_PROOF not in enterprise.principal_proof_one_of
    assert enterprise.requires_quorum and enterprise.requires_transparency

    sovereign = PROFILE_REQUIREMENTS[RecoveryProfile.SOVEREIGN]
    assert F.LNURL_AUTH_PROOF in sovereign.allowed_factors
    assert F.LNURL_AUTH_PROOF not in sovereign.principal_proof_one_of
    assert {F.OFFLINE_RECOVERY_KIT, F.TRANSPARENCY_CHECKPOINT} <= sovereign.required_factors


def test_no_profile_allows_lnurl_as_sole_recovery_factor() -> None:
    for requirements in PROFILE_REQUIREMENTS.values():
        assert requirements.required_factor_count > 1
        assert requirements.required_factors != frozenset({F.LNURL_AUTH_PROOF})


def test_recovery_metrics_use_only_bounded_non_identifier_labels() -> None:
    assert len(LNURL_RECOVERY_METRICS) == 8
    for metric in LNURL_RECOVERY_METRICS.values():
        labels = set(metric._labelnames)
        assert labels == {
            "recovery_profile",
            "verification_strength",
            "decision",
            "reason_code",
            "environment",
        }
