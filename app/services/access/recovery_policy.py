"""Policy checks for Bastion Proof-of-Access recovery."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from app.services.access.recovery_quorum import RecoveryQuorumEvaluation


class RecoveryPolicyDecisionCode(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    COOLDOWN_REQUIRED = "cooldown_required"
    QUORUM_INCOMPLETE = "quorum_incomplete"
    FACTOR_INVALID = "factor_invalid"
    RECOVERY_LOCKED = "recovery_locked"
    POLICY_CHECK_REQUIRED = "policy_check_required"
    ISSUER_POLICY_REQUIRED = "issuer_policy_required"
    LOCKDOWN_REQUIRED = "lockdown_required"


@dataclass(frozen=True)
class RecoveryPolicyDecision:
    decision: str
    allowed: bool
    reason: str
    retry_after_seconds: int | None = None
    metadata: dict[str, Any] | None = None


class RecoveryPolicy:
    def __init__(self, *, max_attempts_per_hour: int = 5) -> None:
        self.max_attempts_per_hour = max_attempts_per_hour

    def evaluate_completion(
        self,
        *,
        quorum: RecoveryQuorumEvaluation,
        cooldown_until: datetime | None,
        failed_factor_count: int,
        target_revoked: bool = False,
        lockdown: bool = False,
        issuer_policy_required: bool = False,
        issuer_policy_satisfied: bool = False,
    ) -> RecoveryPolicyDecision:
        now = datetime.now(UTC)
        if target_revoked:
            return RecoveryPolicyDecision("deny", False, "target_revoked")
        if lockdown:
            return RecoveryPolicyDecision(
                RecoveryPolicyDecisionCode.LOCKDOWN_REQUIRED.value, False, "lockdown_required"
            )
        if failed_factor_count >= self.max_attempts_per_hour:
            return RecoveryPolicyDecision(
                RecoveryPolicyDecisionCode.RECOVERY_LOCKED.value, False, "recovery_attempts_exceeded"
            )
        if cooldown_until and cooldown_until.tzinfo is None:
            cooldown_until = cooldown_until.replace(tzinfo=UTC)
        if cooldown_until and cooldown_until > now:
            return RecoveryPolicyDecision(
                RecoveryPolicyDecisionCode.COOLDOWN_REQUIRED.value,
                False,
                "recovery_cooldown_required",
                retry_after_seconds=int((cooldown_until - now).total_seconds()),
            )
        if quorum.decision != "allow":
            return RecoveryPolicyDecision(
                RecoveryPolicyDecisionCode.QUORUM_INCOMPLETE.value, False, quorum.reason
            )
        if issuer_policy_required and not issuer_policy_satisfied:
            return RecoveryPolicyDecision(
                RecoveryPolicyDecisionCode.ISSUER_POLICY_REQUIRED.value,
                False,
                "issuer_policy_required",
            )
        return RecoveryPolicyDecision(RecoveryPolicyDecisionCode.ALLOW.value, True, "recovery_allowed")

    def evaluate_factor(
        self, *, factor_valid: bool, failed_factor_count: int
    ) -> RecoveryPolicyDecision:
        if failed_factor_count >= self.max_attempts_per_hour:
            return RecoveryPolicyDecision(
                RecoveryPolicyDecisionCode.RECOVERY_LOCKED.value, False, "recovery_attempts_exceeded"
            )
        if not factor_valid:
            return RecoveryPolicyDecision(
                RecoveryPolicyDecisionCode.FACTOR_INVALID.value, False, "recovery_factor_invalid"
            )
        return RecoveryPolicyDecision(RecoveryPolicyDecisionCode.ALLOW.value, True, "factor_allowed")
