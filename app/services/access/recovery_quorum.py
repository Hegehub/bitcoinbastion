"""Recovery quorum profiles for Bastion Proof-of-Access recovery."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.access.plans import PlanCode, normalize_plan_code


class RecoveryFactorType(StrEnum):
    DESKTOP_VAULT = "desktop_vault"
    MOBILE_VAULT = "mobile_vault"
    RECOVERY_PHRASE_12 = "recovery_phrase_12"
    RECOVERY_PHRASE_24 = "recovery_phrase_24"
    OWNER_VAULT = "owner_vault"
    ADMIN_VAULT = "admin_vault"
    HARDWARE_KEY = "hardware_key"
    OFFLINE_RECOVERY_KIT = "offline_recovery_kit"
    BUSINESS_RECOVERY_SEED = "business_recovery_seed"
    RECOVERY_CODE = "recovery_code"
    LOCAL_VAULT_BACKUP = "local_vault_backup"


@dataclass(frozen=True)
class RecoveryQuorumProfile:
    plan_code: PlanCode
    threshold: int
    allowed_factors: frozenset[RecoveryFactorType]
    required_factors: frozenset[RecoveryFactorType]
    cooldown_seconds: int
    requires_audit_packet: bool
    requires_policy_check: bool


@dataclass(frozen=True)
class RecoveryQuorumEvaluation:
    status: str
    threshold: int
    verified_factors: list[str]
    missing_factors: list[str]
    decision: str
    reason: str


def recovery_quorum_profile(
    plan_code: PlanCode | str,
    *,
    cooldown_seconds: int = 900,
    plus_two_of_three_enabled: bool = False,
) -> RecoveryQuorumProfile:
    plan = normalize_plan_code(plan_code)
    if plan == PlanCode.LITE:
        return RecoveryQuorumProfile(
            plan,
            1,
            frozenset({RecoveryFactorType.RECOVERY_PHRASE_12, RecoveryFactorType.RECOVERY_CODE}),
            frozenset(),
            cooldown_seconds,
            False,
            False,
        )
    if plan == PlanCode.BASIC:
        return RecoveryQuorumProfile(
            plan,
            1,
            frozenset({RecoveryFactorType.RECOVERY_PHRASE_12, RecoveryFactorType.LOCAL_VAULT_BACKUP}),
            frozenset(),
            cooldown_seconds,
            True,
            False,
        )
    if plan == PlanCode.PLUS:
        return RecoveryQuorumProfile(
            plan,
            2 if plus_two_of_three_enabled else 1,
            frozenset(
                {
                    RecoveryFactorType.DESKTOP_VAULT,
                    RecoveryFactorType.MOBILE_VAULT,
                    RecoveryFactorType.RECOVERY_PHRASE_12,
                }
            ),
            frozenset(),
            cooldown_seconds,
            True,
            False,
        )
    if plan == PlanCode.PRO:
        return RecoveryQuorumProfile(
            plan,
            2,
            frozenset(
                {
                    RecoveryFactorType.DESKTOP_VAULT,
                    RecoveryFactorType.MOBILE_VAULT,
                    RecoveryFactorType.RECOVERY_PHRASE_24,
                }
            ),
            frozenset(),
            cooldown_seconds,
            True,
            True,
        )
    if plan == PlanCode.BUSINESS:
        return RecoveryQuorumProfile(
            plan,
            2,
            frozenset(
                {
                    RecoveryFactorType.OWNER_VAULT,
                    RecoveryFactorType.ADMIN_VAULT,
                    RecoveryFactorType.BUSINESS_RECOVERY_SEED,
                }
            ),
            frozenset(),
            cooldown_seconds,
            True,
            True,
        )
    if plan == PlanCode.ENTERPRISE:
        return RecoveryQuorumProfile(
            plan,
            3,
            frozenset(
                {
                    RecoveryFactorType.OWNER_VAULT,
                    RecoveryFactorType.ADMIN_VAULT,
                    RecoveryFactorType.HARDWARE_KEY,
                    RecoveryFactorType.RECOVERY_PHRASE_24,
                    RecoveryFactorType.OFFLINE_RECOVERY_KIT,
                }
            ),
            frozenset(),
            cooldown_seconds,
            True,
            True,
        )
    raise ValueError("unknown_recovery_plan")


def evaluate_recovery_quorum(
    profile: RecoveryQuorumProfile, verified_factors: list[str | RecoveryFactorType]
) -> RecoveryQuorumEvaluation:
    normalized = []
    for factor in verified_factors:
        try:
            candidate = RecoveryFactorType(str(factor))
        except ValueError:
            continue
        if candidate in profile.allowed_factors and candidate.value not in normalized:
            normalized.append(candidate.value)
    missing = [factor.value for factor in profile.allowed_factors if factor.value not in normalized]
    if len(normalized) >= profile.threshold:
        return RecoveryQuorumEvaluation(
            status="satisfied",
            threshold=profile.threshold,
            verified_factors=normalized,
            missing_factors=[],
            decision="allow",
            reason="recovery_quorum_satisfied",
        )
    return RecoveryQuorumEvaluation(
        status="incomplete",
        threshold=profile.threshold,
        verified_factors=normalized,
        missing_factors=missing,
        decision="quorum_incomplete",
        reason="recovery_quorum_incomplete",
    )
