from app.services.wallet_auth.recovery.models import RecoveryFactorType as F, RecoveryProfile
from app.services.wallet_auth.recovery.policy import PROFILE_REQUIREMENTS


def test_lnurl_auth_alone_cannot_recover_pro_or_higher() -> None:
    for profile in (
        RecoveryProfile.PRO,
        RecoveryProfile.BUSINESS,
        RecoveryProfile.ENTERPRISE,
        RecoveryProfile.SOVEREIGN,
    ):
        requirements = PROFILE_REQUIREMENTS[profile]
        assert (
            requirements.required_factor_count > 1
            or F.LNURL_AUTH_PROOF not in requirements.allowed_factors
        )
