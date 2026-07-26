"""Declarative Recovery Capsule profiles and central policy boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.services.wallet_auth.recovery.models import (
    RecoveryCapsule,
    RecoveryFactorType as F,
    RecoveryProfile,
)


@dataclass(frozen=True, slots=True)
class RecoveryProfileRequirements:
    profile: RecoveryProfile
    allowed_factors: frozenset[F]
    required_factors: frozenset[F]
    principal_proof_one_of: frozenset[F]
    required_factor_count: int
    requires_quorum: bool = False
    requires_transparency: bool = False
    requires_dual_control: bool = False
    trusted_device_requirement: str = "optional"
    revoke_all_sessions: bool = True
    freeze_children: bool = True


PRINCIPAL_PROOFS = frozenset({F.BIP322_WALLET_PROOF, F.LNURL_AUTH_PROOF, F.OWNER_WALLET_PROOF})
PROFILE_REQUIREMENTS: dict[RecoveryProfile, RecoveryProfileRequirements] = {
    RecoveryProfile.LITE_BASIC: RecoveryProfileRequirements(
        RecoveryProfile.LITE_BASIC,
        PRINCIPAL_PROOFS | {F.PAYMENT_PROOF, F.ACTIVE_SUBSCRIPTION_PROOF},
        frozenset(),
        PRINCIPAL_PROOFS,
        2,
        trusted_device_requirement="optional",
        freeze_children=False,
    ),
    RecoveryProfile.PLUS: RecoveryProfileRequirements(
        RecoveryProfile.PLUS,
        PRINCIPAL_PROOFS
        | {F.RECOVERY_FILE, F.TRUSTED_DEVICE, F.DEVICE_HISTORY, F.ACCESS_CERTIFICATE},
        frozenset({F.RECOVERY_FILE}),
        PRINCIPAL_PROOFS,
        3,
        trusted_device_requirement="history_required",
    ),
    RecoveryProfile.PRO: RecoveryProfileRequirements(
        RecoveryProfile.PRO,
        PRINCIPAL_PROOFS
        | {
            F.RECOVERY_FILE,
            F.TRUSTED_DEVICE,
            F.DEVICE_HISTORY,
            F.ACCESS_CERTIFICATE,
            F.HARDWARE_WALLET_PROOF,
        },
        frozenset({F.RECOVERY_FILE, F.TRUSTED_DEVICE}),
        PRINCIPAL_PROOFS,
        3,
        trusted_device_requirement="required",
    ),
    RecoveryProfile.BUSINESS: RecoveryProfileRequirements(
        RecoveryProfile.BUSINESS,
        frozenset(
            {
                F.OWNER_WALLET_PROOF,
                F.LNURL_AUTH_PROOF,
                F.ADMIN_WALLET_PROOF,
                F.BUSINESS_ROLE_QUORUM,
                F.TRUSTED_DEVICE,
                F.RECOVERY_FILE,
            }
        ),
        frozenset({F.BUSINESS_ROLE_QUORUM}),
        frozenset({F.OWNER_WALLET_PROOF, F.LNURL_AUTH_PROOF}),
        3,
        requires_quorum=True,
        requires_dual_control=True,
        trusted_device_requirement="required",
    ),
    RecoveryProfile.ENTERPRISE: RecoveryProfileRequirements(
        RecoveryProfile.ENTERPRISE,
        frozenset(
            {
                F.OWNER_WALLET_PROOF,
                F.ADMIN_WALLET_PROOF,
                F.MULTI_METHOD_QUORUM,
                F.HARDWARE_WALLET_PROOF,
                F.RECOVERY_FILE,
                F.TRANSPARENCY_CHECKPOINT,
                F.TRUSTED_DEVICE,
                F.LNURL_AUTH_PROOF,
            }
        ),
        frozenset({F.MULTI_METHOD_QUORUM, F.HARDWARE_WALLET_PROOF, F.TRANSPARENCY_CHECKPOINT}),
        frozenset({F.OWNER_WALLET_PROOF}),
        4,
        requires_quorum=True,
        requires_transparency=True,
        requires_dual_control=True,
        trusted_device_requirement="required",
    ),
    RecoveryProfile.SOVEREIGN: RecoveryProfileRequirements(
        RecoveryProfile.SOVEREIGN,
        frozenset(
            {
                F.MULTI_WALLET_QUORUM,
                F.MULTI_METHOD_QUORUM,
                F.HARDWARE_WALLET_PROOF,
                F.AIR_GAPPED_WALLET_PROOF,
                F.OFFLINE_RECOVERY_KIT,
                F.TRANSPARENCY_CHECKPOINT,
                F.LNURL_AUTH_PROOF,
            }
        ),
        frozenset({F.OFFLINE_RECOVERY_KIT, F.TRANSPARENCY_CHECKPOINT}),
        frozenset({F.MULTI_WALLET_QUORUM, F.MULTI_METHOD_QUORUM}),
        4,
        requires_quorum=True,
        requires_transparency=True,
        requires_dual_control=True,
        trusted_device_requirement="hardware_history_required",
    ),
}


class RecoveryPolicyAuthorizer(Protocol):
    def authorize(self, *, action: str, capsule: RecoveryCapsule) -> tuple[bool, str]: ...


class QuorumVerifierBoundary(Protocol):
    def satisfied(self, *, capsule: RecoveryCapsule) -> bool: ...


def factors_satisfy_profile(
    capsule: RecoveryCapsule, requirements: RecoveryProfileRequirements
) -> bool:
    verified = set(capsule.verified_factors)
    return (
        len(verified) >= requirements.required_factor_count
        and requirements.required_factors <= verified
        and bool(requirements.principal_proof_one_of & verified)
    )
