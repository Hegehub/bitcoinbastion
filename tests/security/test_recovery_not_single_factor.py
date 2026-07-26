from app.services.wallet_auth.recovery.models import RecoveryFactorType as F, RecoveryProfile
from app.services.wallet_auth.recovery.policy import PROFILE_REQUIREMENTS


def test_pro_and_high_tiers_are_not_single_factor() -> None:
    for profile in (
        RecoveryProfile.PRO,
        RecoveryProfile.BUSINESS,
        RecoveryProfile.ENTERPRISE,
        RecoveryProfile.SOVEREIGN,
    ):
        assert PROFILE_REQUIREMENTS[profile].required_factor_count >= 3
    assert (
        F.LNURL_AUTH_PROOF not in PROFILE_REQUIREMENTS[RecoveryProfile.ENTERPRISE].required_factors
    )
