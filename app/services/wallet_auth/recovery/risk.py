from dataclasses import dataclass

from app.services.wallet_auth.recovery.models import RecoveryCapsule, RecoveryProfile


@dataclass(frozen=True, slots=True)
class RecoveryRiskAssessment:
    risk_level: str
    decision: str
    reason_codes: tuple[str, ...]
    extend_cooldown: bool = False
    freeze_roles: bool = False


def assess_recovery_risk(
    capsule: RecoveryCapsule,
    *,
    access_integrity_score: int | None,
    recent_revocation: bool = False,
    recent_device_enrollment: bool = False,
    legacy_proof_used: bool = False,
) -> RecoveryRiskAssessment:
    reasons: list[str] = []
    if recent_revocation:
        reasons.append("recent_revocation")
    if recent_device_enrollment:
        reasons.append("recent_device_enrollment")
    if legacy_proof_used:
        reasons.append("legacy_proof_used")
    if access_integrity_score is None or access_integrity_score < 30:
        reasons.append("integrity_critical")
    high_tier = capsule.recovery_profile in {
        RecoveryProfile.BUSINESS,
        RecoveryProfile.ENTERPRISE,
        RecoveryProfile.SOVEREIGN,
    }
    if len(reasons) >= 2:
        return RecoveryRiskAssessment(
            "critical", "lockdown_required", tuple(reasons), True, high_tier
        )
    if reasons:
        return RecoveryRiskAssessment(
            "high", "require_additional_factor", tuple(reasons), True, high_tier
        )
    if high_tier:
        return RecoveryRiskAssessment("medium", "require_quorum", (), False, True)
    return RecoveryRiskAssessment("low", "continue", ())
