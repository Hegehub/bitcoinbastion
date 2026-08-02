from datetime import UTC, datetime, timedelta

from app.services.wallet_auth.recovery.models import RecoveryCapsule, RecoveryCapsuleStatus
from app.services.wallet_auth.recovery.models import RecoveryFactorType as F, RecoveryProfile
from app.services.wallet_auth.recovery.policy import PROFILE_REQUIREMENTS
from app.services.wallet_auth.recovery.risk import assess_recovery_risk


def test_risk_can_require_quorum_or_lockdown_without_authorizing() -> None:
    business = make(RecoveryProfile.BUSINESS, (F.OWNER_WALLET_PROOF,))
    assert assess_recovery_risk(business, access_integrity_score=90).decision == "require_quorum"
    critical = assess_recovery_risk(business, access_integrity_score=10, recent_revocation=True)
    assert critical.decision == "lockdown_required" and critical.freeze_roles


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
