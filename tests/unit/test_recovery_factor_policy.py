from datetime import UTC, datetime, timedelta

from app.services.wallet_auth.recovery.models import (
    RecoveryCapsule,
    RecoveryCapsuleStatus,
    RecoveryFactorType as F,
    RecoveryProfile,
)
from app.services.wallet_auth.recovery.policy import PROFILE_REQUIREMENTS, factors_satisfy_profile


def make(profile: RecoveryProfile, factors: tuple[F, ...]) -> RecoveryCapsule:
    now = datetime.now(UTC)
    req = PROFILE_REQUIREMENTS[profile]
    return RecoveryCapsule(
        "id",
        "hmac:c",
        1,
        1,
        1,
        "hmac:p",
        "bitcoin_wallet_principal",
        profile,
        RecoveryCapsuleStatus.AWAITING_FACTORS,
        tuple(req.required_factors),
        factors,
        req.required_factor_count,
        None,
        req.trusted_device_requirement,
        None,
        None,
        now + timedelta(days=1),
        0,
        5,
        "medium",
        "lost",
        (),
        (),
        now,
        now,
    )


def test_profiles_require_principal_factor_and_high_tier_boundaries() -> None:
    assert factors_satisfy_profile(
        make(RecoveryProfile.LITE_BASIC, (F.BIP322_WALLET_PROOF, F.PAYMENT_PROOF)),
        PROFILE_REQUIREMENTS[RecoveryProfile.LITE_BASIC],
    )
    assert not factors_satisfy_profile(
        make(RecoveryProfile.PRO, (F.LNURL_AUTH_PROOF,)), PROFILE_REQUIREMENTS[RecoveryProfile.PRO]
    )
    assert PROFILE_REQUIREMENTS[RecoveryProfile.BUSINESS].requires_quorum
    assert PROFILE_REQUIREMENTS[RecoveryProfile.ENTERPRISE].requires_transparency
    assert PROFILE_REQUIREMENTS[RecoveryProfile.SOVEREIGN].requires_quorum
