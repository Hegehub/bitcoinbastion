import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from app.services.wallet_auth.recovery.errors import RecoveryFactorError
from app.services.wallet_auth.recovery.factor_registry import RecoveryFactorRegistry
from app.services.wallet_auth.recovery.models import (
    RecoveryCapsule,
    RecoveryCapsuleStatus,
    RecoveryFactorResult,
    RecoveryFactorSubmission,
    RecoveryFactorType,
    RecoveryProfile,
    RecoveryVerificationContext,
)


class Verifier:
    factor_type = RecoveryFactorType.BIP322_WALLET_PROOF
    enabled = True

    async def verify(self, capsule, submission, context):
        return RecoveryFactorResult(
            True,
            self.factor_type,
            submission.factor_fingerprint,
            "standard",
            datetime.now(UTC),
            datetime.now(UTC) + timedelta(minutes=5),
            "verified",
            replay_reference_hash=submission.proof_reference_hash,
        )


def capsule() -> RecoveryCapsule:
    now = datetime.now(UTC)
    return RecoveryCapsule(
        "id",
        "hmac:c",
        1,
        1,
        1,
        "hmac:p",
        "bitcoin_wallet_principal",
        RecoveryProfile.LITE_BASIC,
        RecoveryCapsuleStatus.AWAITING_FACTORS,
        (),
        (),
        2,
        None,
        "optional",
        None,
        None,
        now + timedelta(days=1),
        0,
        5,
        "medium",
        "lost_device",
        (),
        (),
        now,
        now,
    )


def test_registry_rejects_unknown_duplicate_revoked_expired_and_replay() -> None:
    registry = RecoveryFactorRegistry()
    registry.register(Verifier())
    submission = RecoveryFactorSubmission(
        RecoveryFactorType.BIP322_WALLET_PROOF, "hmac:proof", "sha256:factor", datetime.now(UTC)
    )
    assert asyncio.run(
        registry.verify(capsule(), submission, RecoveryVerificationContext("hmac:p", 1))
    ).verified
    with pytest.raises(RecoveryFactorError, match="replayed"):
        asyncio.run(
            registry.verify(
                capsule(),
                submission,
                RecoveryVerificationContext("hmac:p", 1, {"replay_used": True}),
            )
        )
    with pytest.raises(RecoveryFactorError, match="unsupported"):
        asyncio.run(
            RecoveryFactorRegistry().verify(
                capsule(), submission, RecoveryVerificationContext("hmac:p", 1)
            )
        )
    duplicate = replace(capsule(), verified_factors=(RecoveryFactorType.BIP322_WALLET_PROOF,))
    with pytest.raises(RecoveryFactorError, match="duplicate"):
        asyncio.run(
            registry.verify(duplicate, submission, RecoveryVerificationContext("hmac:p", 1))
        )
