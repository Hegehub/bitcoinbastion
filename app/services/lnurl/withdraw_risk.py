"""Risk orchestration for LNURL-withdraw lifecycle checks."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.lnurl.withdraw_risk import LNURLWithdrawPurpose, LNURLWithdrawRiskDecision, LNURLWithdrawRiskLevel
from app.services.access.crypto.hashing import hash_canonical_json_prefixed
from app.services.lnurl.withdraw_cooldown import InMemoryLNURLWithdrawCooldownService
from app.services.lnurl.withdraw_limits import LNURLWithdrawLimitEvaluator, LNURLWithdrawLimitInput
from app.services.lnurl.withdraw_velocity import InMemoryLNURLWithdrawVelocityTracker, LNURLWithdrawVelocityEvent


@dataclass(frozen=True)
class LNURLWithdrawRiskContext:
    withdraw_id: str
    purpose: LNURLWithdrawPurpose
    amount_msat: int
    network: str
    principal_hash: str | None = None
    principal_type: str | None = None
    device_fingerprint: str | None = None
    session_fingerprint: str | None = None
    business_workspace_hash: str | None = None
    merchant_hash: str | None = None
    payregister_device_hash: str | None = None
    cashier_role_hash: str | None = None
    original_payment_hash: str | None = None
    original_invoice_hash: str | None = None
    subscription_entitlement_hash: str | None = None
    destination_invoice_hash: str | None = None
    requested_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    wallet_proof_age_seconds: int | None = None
    lnurl_auth_proof_age_seconds: int | None = None
    pop_session_age_seconds: int | None = None
    device_risk: int = 0
    principal_risk: int = 0
    role: str | None = None
    original_remaining_msat: int | None = None
    revoked: bool = False
    lockdown: bool = False
    provider_healthy: bool = True
    prior_policy_hash: str | None = None


@dataclass(frozen=True)
class LNURLWithdrawRiskResult:
    decision: LNURLWithdrawRiskDecision
    risk_level: LNURLWithdrawRiskLevel
    risk_score: int
    reason_codes: tuple[str, ...]
    required_controls: tuple[str, ...]
    effective_limits: dict[str, int]
    policy_hash: str
    evaluated_at: datetime

    @property
    def allowed(self) -> bool:
        return self.decision == LNURLWithdrawRiskDecision.ALLOW


class LNURLWithdrawRiskService:
    def __init__(self, *, limits: LNURLWithdrawLimitEvaluator | None = None, velocity: InMemoryLNURLWithdrawVelocityTracker | None = None, cooldown: InMemoryLNURLWithdrawCooldownService | None = None) -> None:
        self.limits = limits or LNURLWithdrawLimitEvaluator()
        self.velocity = velocity or InMemoryLNURLWithdrawVelocityTracker()
        self.cooldown = cooldown or InMemoryLNURLWithdrawCooldownService()

    def evaluate_request(self, context: LNURLWithdrawRiskContext) -> LNURLWithdrawRiskResult:
        return self._evaluate("request_creation", context)

    def evaluate_invoice(self, context: LNURLWithdrawRiskContext, *, invoice_valid: bool = True) -> LNURLWithdrawRiskResult:
        if not invoice_valid:
            return self._build(context, LNURLWithdrawRiskDecision.DESTINATION_REJECTED, ("invoice_invalid",), ("audit",), {})
        return self._evaluate("invoice_acceptance", context)

    def evaluate_execution(self, context: LNURLWithdrawRiskContext) -> LNURLWithdrawRiskResult:
        return self._evaluate("payment_execution", context)

    def evaluate_provider_result(self, context: LNURLWithdrawRiskContext, *, provider_timeout: bool = False) -> LNURLWithdrawRiskResult:
        if provider_timeout:
            return self._build(context, LNURLWithdrawRiskDecision.MANUAL_REVIEW_REQUIRED, ("provider_timeout_reconciliation_required",), ("reconciliation", "audit"), {})
        return self._evaluate("provider_result", context)

    def evaluate_reconciliation(self, context: LNURLWithdrawRiskContext, *, mismatch: bool = False) -> LNURLWithdrawRiskResult:
        if mismatch:
            return self._build(context, LNURLWithdrawRiskDecision.MANUAL_REVIEW_REQUIRED, ("reconciliation_mismatch",), ("manual_review", "audit"), {})
        return self._build(context, LNURLWithdrawRiskDecision.ALLOW, ("reconciliation_matched",), ("audit",), {})

    def calculate_risk_score(self, context: LNURLWithdrawRiskContext) -> int:
        score = context.device_risk + context.principal_risk
        if context.amount_msat > 5_000_000:
            score += 45
        elif context.amount_msat > 1_000_000:
            score += 25
        elif context.amount_msat > 250_000:
            score += 10
        if context.purpose in {LNURLWithdrawPurpose.BUG_BOUNTY, LNURLWithdrawPurpose.PARTNER_PAYOUT, LNURLWithdrawPurpose.ADMINISTRATIVE_ADJUSTMENT}:
            score += 25
        if context.role == "cashier":
            score += 10
        if context.pop_session_age_seconds is None:
            score += 20
        if not context.provider_healthy:
            score += 20
        return max(0, min(score, 100))

    def determine_step_up(self, context: LNURLWithdrawRiskContext) -> tuple[str, ...]:
        controls = ["pop_session", "audit"]
        if context.amount_msat > 1_000_000 or context.role in {"admin", "owner"}:
            controls.append("fresh_lnurl_auth")
        if context.amount_msat > 5_000_000:
            controls.append("human_intent")
        return tuple(controls)

    def determine_manual_review(self, context: LNURLWithdrawRiskContext) -> bool:
        return context.amount_msat > 5_000_000 or context.purpose in {LNURLWithdrawPurpose.BUG_BOUNTY, LNURLWithdrawPurpose.ADMINISTRATIVE_ADJUSTMENT}

    def _evaluate(self, stage: str, context: LNURLWithdrawRiskContext) -> LNURLWithdrawRiskResult:
        if context.lockdown:
            return self._build(context, LNURLWithdrawRiskDecision.LOCKDOWN, ("lockdown_active",), ("audit",), {})
        if context.revoked:
            return self._build(context, LNURLWithdrawRiskDecision.REVOKED, ("principal_or_request_revoked",), ("audit",), {})
        subject = context.principal_hash or context.device_fingerprint or context.withdraw_id
        cooldown = self.cooldown.evaluate(subject)
        if not cooldown.allowed:
            return self._build(context, cooldown.decision, (cooldown.reason_code,), ("cooldown", "audit"), {})
        limit = self.limits.evaluate(
            LNURLWithdrawLimitInput(
                purpose=context.purpose,
                amount_msat=context.amount_msat,
                network=context.network,
                role=context.role,
                original_remaining_msat=context.original_remaining_msat,
            )
        )
        if not limit.allowed:
            return self._build(context, limit.decision, limit.reason_codes, ("audit",), limit.effective_limits)
        velocity = self.velocity.evaluate(
            LNURLWithdrawVelocityEvent(
                amount_msat=context.amount_msat,
                purpose=context.purpose.value,
                network=context.network,
                principal_hash=context.principal_hash,
                merchant_hash=context.merchant_hash,
                payregister_device_hash=context.payregister_device_hash,
                device_fingerprint=context.device_fingerprint,
                destination_invoice_hash=context.destination_invoice_hash,
                original_payment_hash=context.original_payment_hash,
            )
        )
        if not velocity.allowed:
            return self._build(context, velocity.decision, velocity.reason_codes, ("audit",), {**limit.effective_limits, **velocity.counters})
        controls = self.determine_step_up(context)
        if limit.requires_manual_review or self.determine_manual_review(context):
            return self._build(context, LNURLWithdrawRiskDecision.MANUAL_REVIEW_REQUIRED, (*limit.reason_codes, "manual_review_required", stage), controls, limit.effective_limits)
        if limit.requires_step_up and context.lnurl_auth_proof_age_seconds is None:
            return self._build(context, LNURLWithdrawRiskDecision.STEP_UP_REQUIRED, (*limit.reason_codes, "fresh_step_up_required", stage), controls, limit.effective_limits)
        return self._build(context, LNURLWithdrawRiskDecision.ALLOW, (*limit.reason_codes, "velocity_within_limit", stage), controls, limit.effective_limits)

    def _build(self, context: LNURLWithdrawRiskContext, decision: LNURLWithdrawRiskDecision, reasons: tuple[str, ...], controls: tuple[str, ...], effective_limits: dict[str, int]) -> LNURLWithdrawRiskResult:
        score = self.calculate_risk_score(context)
        level = LNURLWithdrawRiskLevel.CRITICAL if score >= 80 else LNURLWithdrawRiskLevel.HIGH if score >= 55 else LNURLWithdrawRiskLevel.MEDIUM if score >= 25 else LNURLWithdrawRiskLevel.LOW
        policy_hash = hash_canonical_json_prefixed({"purpose": context.purpose.value, "amount_msat": context.amount_msat, "network": context.network, "decision": decision.value, "reason_codes": reasons})
        return LNURLWithdrawRiskResult(decision, level, score, reasons, controls, effective_limits, policy_hash, datetime.now(UTC))
