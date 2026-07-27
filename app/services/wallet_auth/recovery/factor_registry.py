from datetime import UTC, datetime

from app.services.wallet_auth.recovery.errors import RecoveryFactorError
from app.services.wallet_auth.recovery.factor_verifier import RecoveryFactorVerifier
from app.services.wallet_auth.recovery.models import (
    RecoveryCapsule,
    RecoveryFactorResult,
    RecoveryFactorSubmission,
    RecoveryFactorType,
    RecoveryVerificationContext,
)
from app.services.wallet_auth.recovery.policy import PROFILE_REQUIREMENTS


class RecoveryFactorRegistry:
    def __init__(self) -> None:
        self._verifiers: dict[RecoveryFactorType, RecoveryFactorVerifier] = {}

    def register(self, verifier: RecoveryFactorVerifier) -> None:
        if verifier.factor_type in self._verifiers:
            raise RecoveryFactorError("recovery_factor_verifier_already_registered")
        self._verifiers[verifier.factor_type] = verifier

    async def verify(
        self,
        capsule: RecoveryCapsule,
        submission: RecoveryFactorSubmission,
        context: RecoveryVerificationContext,
    ) -> RecoveryFactorResult:
        verifier = self._verifiers.get(submission.factor_type)
        if verifier is None or not verifier.enabled:
            raise RecoveryFactorError("recovery_factor_unsupported")
        if (
            submission.factor_type
            not in PROFILE_REQUIREMENTS[capsule.recovery_profile].allowed_factors
        ):
            raise RecoveryFactorError("recovery_factor_not_allowed")
        if submission.factor_type in capsule.verified_factors:
            raise RecoveryFactorError("recovery_duplicate_factor")
        if context.revocation_state.get("replay_used"):
            raise RecoveryFactorError("recovery_factor_replayed")
        if context.revocation_state.get("factor_revoked"):
            raise RecoveryFactorError("recovery_factor_revoked")
        result = await verifier.verify(capsule, submission, context)
        now = datetime.now(UTC)
        if result.expires_at and result.expires_at <= now:
            raise RecoveryFactorError("recovery_factor_expired")
        if not result.verified:
            raise RecoveryFactorError(result.reason_code or "recovery_factor_invalid")
        return result
