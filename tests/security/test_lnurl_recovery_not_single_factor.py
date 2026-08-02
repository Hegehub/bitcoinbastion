from app.services.wallet_auth.recovery.models import RecoveryFactorType as F, RecoveryProfile
from app.services.wallet_auth.recovery.policy import PROFILE_REQUIREMENTS


def test_lnurl_auth_never_satisfies_a_profile_alone() -> None:
    for profile in RecoveryProfile:
        requirements = PROFILE_REQUIREMENTS[profile]
        verified = {F.LNURL_AUTH_PROOF}
        assert len(verified) < requirements.required_factor_count or not (
            requirements.required_factors <= verified
        )
