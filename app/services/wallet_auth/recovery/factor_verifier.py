from typing import Protocol

from app.services.wallet_auth.recovery.models import (
    RecoveryCapsule,
    RecoveryFactorResult,
    RecoveryFactorSubmission,
    RecoveryFactorType,
    RecoveryVerificationContext,
)


class RecoveryFactorVerifier(Protocol):
    factor_type: RecoveryFactorType
    enabled: bool

    async def verify(
        self,
        capsule: RecoveryCapsule,
        submission: RecoveryFactorSubmission,
        context: RecoveryVerificationContext,
    ) -> RecoveryFactorResult: ...


class LNURLAuthRecoveryFactorVerifier(RecoveryFactorVerifier, Protocol):
    """Prompt 58 integration boundary; no k1 callback implementation here."""


class RecoveryQuorumFactorVerifier(RecoveryFactorVerifier, Protocol):
    """Prompt 59 integration boundary; no quorum cryptography implementation here."""
