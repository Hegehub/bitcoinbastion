"""Declarative LNURL-withdraw financial limits."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.lnurl.withdraw_risk import LNURLWithdrawPurpose, LNURLWithdrawRiskDecision

MAINNET = "bitcoin-mainnet"
FAUCET_PURPOSES = {LNURLWithdrawPurpose.TESTNET_FAUCET, LNURLWithdrawPurpose.SIGNET_FAUCET}
REFUND_PURPOSES = {LNURLWithdrawPurpose.SUBSCRIPTION_REFUND, LNURLWithdrawPurpose.PAYREGISTER_REFUND}


@dataclass(frozen=True)
class LNURLWithdrawPurposeLimits:
    max_single_msat: int | None = None
    max_daily_principal_msat: int | None = None
    max_daily_business_msat: int | None = None
    max_daily_merchant_msat: int | None = None
    max_requests_per_hour: int | None = None
    original_payment_required: bool | None = None
    max_refund_percent: int = 100
    allow_partial_refunds: bool = True
    allow_over_refunds: bool = False
    step_up_above_msat: int | None = None
    manual_review_above_msat: int | None = None
    cashier_max_msat: int | None = None
    allowed_networks: frozenset[str] | None = None
    administrative_adjustment_enabled: bool = False


@dataclass(frozen=True)
class LNURLWithdrawLimitConfig:
    enabled: bool = False
    mainnet_enabled: bool = False
    global_max_single_msat: int = 5_000_000
    global_max_daily_msat: int = 50_000_000
    global_max_requests_per_hour: int = 20
    require_original_payment: bool = True
    allow_over_refunds: bool = False
    default_step_up_above_msat: int = 1_000_000
    default_manual_review_above_msat: int = 5_000_000
    purpose_overrides: dict[LNURLWithdrawPurpose, LNURLWithdrawPurposeLimits] = field(default_factory=dict)

    def validate(self) -> None:
        values = [
            self.global_max_single_msat,
            self.global_max_daily_msat,
            self.global_max_requests_per_hour,
            self.default_step_up_above_msat,
            self.default_manual_review_above_msat,
        ]
        if any(value < 0 for value in values):
            raise ValueError("lnurl withdraw limits must not be negative")
        if self.enabled and self.mainnet_enabled and (self.global_max_single_msat <= 0 or self.global_max_daily_msat <= 0):
            raise ValueError("mainnet withdraw requires positive finite global limits")


@dataclass(frozen=True)
class LNURLWithdrawLimitInput:
    purpose: LNURLWithdrawPurpose
    amount_msat: int
    network: str
    role: str | None = None
    principal_daily_used_msat: int = 0
    business_daily_used_msat: int = 0
    merchant_daily_used_msat: int = 0
    global_daily_used_msat: int = 0
    requests_this_hour: int = 0
    original_remaining_msat: int | None = None
    device_max_msat: int | None = None
    terminal_max_msat: int | None = None
    workspace_max_msat: int | None = None
    incident_ceiling_msat: int | None = None


@dataclass(frozen=True)
class LNURLWithdrawLimitResult:
    allowed: bool
    decision: LNURLWithdrawRiskDecision
    effective_max_single_msat: int
    remaining_daily_msat: int
    reason_codes: tuple[str, ...]
    effective_limits: dict[str, int]
    requires_step_up: bool = False
    requires_manual_review: bool = False


class LNURLWithdrawLimitEvaluator:
    def __init__(self, config: LNURLWithdrawLimitConfig | None = None) -> None:
        self.config = config or LNURLWithdrawLimitConfig()
        self.config.validate()

    def evaluate(self, request: LNURLWithdrawLimitInput) -> LNURLWithdrawLimitResult:
        limits = self.config.purpose_overrides.get(request.purpose, LNURLWithdrawPurposeLimits())
        reasons: list[str] = []
        effective = {"global_single_msat": self.config.global_max_single_msat}
        ceilings = [self.config.global_max_single_msat]
        if not self.config.enabled:
            return self._deny(LNURLWithdrawRiskDecision.DENY, "withdraw_disabled", effective)
        if request.network == MAINNET and not self.config.mainnet_enabled:
            return self._deny(LNURLWithdrawRiskDecision.DENY, "mainnet_withdraw_disabled", effective)
        if request.purpose in FAUCET_PURPOSES and request.network == MAINNET:
            return self._deny(LNURLWithdrawRiskDecision.DENY, "faucet_mainnet_denied", effective)
        if request.purpose == LNURLWithdrawPurpose.ADMINISTRATIVE_ADJUSTMENT and not limits.administrative_adjustment_enabled:
            return self._deny(LNURLWithdrawRiskDecision.DENY, "administrative_adjustment_disabled", effective)
        if request.amount_msat <= 0:
            return self._deny(LNURLWithdrawRiskDecision.AMOUNT_EXCEEDED, "amount_must_be_positive", effective)
        if limits.allowed_networks is not None and request.network not in limits.allowed_networks:
            return self._deny(LNURLWithdrawRiskDecision.DENY, "network_not_allowed", effective)
        if limits.max_single_msat is not None:
            ceilings.append(limits.max_single_msat)
            effective["purpose_single_msat"] = limits.max_single_msat
        for key, value in {
            "workspace_single_msat": request.workspace_max_msat,
            "terminal_single_msat": request.terminal_max_msat,
            "device_single_msat": request.device_max_msat,
            "incident_single_msat": request.incident_ceiling_msat,
        }.items():
            if value is not None:
                ceilings.append(value)
                effective[key] = value
        if request.role == "cashier" and limits.cashier_max_msat is not None:
            ceilings.append(limits.cashier_max_msat)
            effective["cashier_single_msat"] = limits.cashier_max_msat
        original_required = self.config.require_original_payment if limits.original_payment_required is None else limits.original_payment_required
        if original_required and request.purpose in REFUND_PURPOSES and request.original_remaining_msat is None:
            return self._deny(LNURLWithdrawRiskDecision.ORIGINAL_PAYMENT_REQUIRED, "original_payment_missing", effective)
        if request.original_remaining_msat is not None:
            ceilings.append(request.original_remaining_msat)
            effective["original_remaining_msat"] = request.original_remaining_msat
        effective_max = min(ceilings)
        remaining_daily = self.config.global_max_daily_msat - request.global_daily_used_msat
        effective["global_remaining_daily_msat"] = remaining_daily
        if request.requests_this_hour >= (limits.max_requests_per_hour or self.config.global_max_requests_per_hour):
            return self._deny(LNURLWithdrawRiskDecision.VELOCITY_EXCEEDED, "request_velocity_exceeded", effective, effective_max, remaining_daily)
        daily_candidates = [remaining_daily]
        for key, configured, used in (
            ("principal_remaining_daily_msat", limits.max_daily_principal_msat, request.principal_daily_used_msat),
            ("business_remaining_daily_msat", limits.max_daily_business_msat, request.business_daily_used_msat),
            ("merchant_remaining_daily_msat", limits.max_daily_merchant_msat, request.merchant_daily_used_msat),
        ):
            if configured is not None:
                remaining = configured - used
                daily_candidates.append(remaining)
                effective[key] = remaining
        remaining_daily = min(daily_candidates)
        if request.amount_msat > effective_max:
            return self._deny(LNURLWithdrawRiskDecision.AMOUNT_EXCEEDED, "single_amount_limit_exceeded", effective, effective_max, remaining_daily)
        if request.amount_msat > remaining_daily:
            return self._deny(LNURLWithdrawRiskDecision.QUOTA_EXCEEDED, "daily_limit_exceeded", effective, effective_max, remaining_daily)
        step_threshold = limits.step_up_above_msat if limits.step_up_above_msat is not None else self.config.default_step_up_above_msat
        review_threshold = limits.manual_review_above_msat if limits.manual_review_above_msat is not None else self.config.default_manual_review_above_msat
        if request.amount_msat > step_threshold:
            reasons.append("fresh_step_up_required")
        if request.amount_msat > review_threshold or request.purpose == LNURLWithdrawPurpose.BUG_BOUNTY:
            reasons.append("manual_review_required")
        if not reasons:
            reasons.append("amount_within_limit")
        return LNURLWithdrawLimitResult(
            allowed=True,
            decision=LNURLWithdrawRiskDecision.ALLOW,
            effective_max_single_msat=effective_max,
            remaining_daily_msat=remaining_daily,
            reason_codes=tuple(reasons),
            effective_limits=effective,
            requires_step_up="fresh_step_up_required" in reasons,
            requires_manual_review="manual_review_required" in reasons,
        )

    def _deny(self, decision: LNURLWithdrawRiskDecision, reason: str, effective: dict[str, int], effective_max: int | None = None, remaining_daily: int | None = None) -> LNURLWithdrawLimitResult:
        return LNURLWithdrawLimitResult(False, decision, effective_max or self.config.global_max_single_msat, remaining_daily or self.config.global_max_daily_msat, (reason,), effective)
