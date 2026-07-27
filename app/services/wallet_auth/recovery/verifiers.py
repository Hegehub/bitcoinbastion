"""Verifier adapters around existing evidence services; no cryptography is implemented here."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from app.services.wallet_auth.recovery.models import (
    RecoveryCapsule,
    RecoveryFactorResult,
    RecoveryFactorSubmission,
    RecoveryFactorType,
    RecoveryVerificationContext,
)

EvidenceCheck = Callable[
    [RecoveryCapsule, RecoveryFactorSubmission, RecoveryVerificationContext], tuple[bool, str, str]
]


class ExistingEvidenceFactorVerifier:
    """Calls an existing verifier/repository and converts only its verified result."""

    enabled = True

    def __init__(self, factor_type: RecoveryFactorType, evidence_check: EvidenceCheck) -> None:
        self.factor_type, self.evidence_check = factor_type, evidence_check

    async def verify(
        self,
        capsule: RecoveryCapsule,
        submission: RecoveryFactorSubmission,
        context: RecoveryVerificationContext,
    ) -> RecoveryFactorResult:
        verified, strength, reason = self.evidence_check(capsule, submission, context)
        now = datetime.now(UTC)
        return RecoveryFactorResult(
            verified,
            self.factor_type,
            submission.factor_fingerprint,
            strength,
            now,
            now + timedelta(minutes=5) if verified else None,
            reason,
            (),
            {"evidence_fingerprint": submission.factor_fingerprint},
            True,
            submission.proof_reference_hash,
        )


def trusted_device_evidence_check(
    capsule: RecoveryCapsule,
    submission: RecoveryFactorSubmission,
    context: RecoveryVerificationContext,
) -> tuple[bool, str, str]:
    data = submission.metadata
    age_days = data.get("device_age_days")
    risk_score = data.get("risk_score")
    valid = (
        data.get("status") == "active"
        and isinstance(age_days, int)
        and age_days >= 7
        and isinstance(risk_score, int)
        and risk_score <= 40
        and bool(data.get("previous_wallet_binding"))
        and bool(data.get("recent_successful_session"))
        and not data.get("recently_enrolled")
        and not context.revocation_state.get("device_revoked")
    )
    if data.get("device_class") == "browser_extension" and capsule.recovery_profile.value in {
        "business",
        "enterprise",
        "sovereign",
    }:
        valid = False
    return (
        valid,
        "standard" if valid else "unverified",
        "trusted_device_verified" if valid else "device_not_trusted",
    )


def payment_proof_evidence_check(
    capsule: RecoveryCapsule,
    submission: RecoveryFactorSubmission,
    context: RecoveryVerificationContext,
) -> tuple[bool, str, str]:
    data = submission.metadata
    valid = (
        data.get("settlement_verified") is True
        and data.get("principal_hash") == capsule.principal_hash
        and data.get("payment_proof_status") == "active"
        and not data.get("duplicate")
        and not context.revocation_state.get("payment_proof_revoked")
    )
    return (
        valid,
        "supporting" if valid else "unverified",
        "payment_continuity_verified" if valid else "payment_not_verified",
    )
