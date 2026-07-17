"""LNURL-pay subscription pricing primitives.

All monetary values are integer millisatoshis.  This module intentionally avoids
floating-point arithmetic and does not issue invoices or entitlements.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Callable, Protocol

from app.domain.access.errors import InvalidPlanCodeError
from app.domain.access.plans import PlanCode, normalize_plan_code
from app.services.access.crypto.hashing import hash_canonical_json_prefixed
from app.services.lnurl.pay.errors import (
    LNURLPayInvalidAmountError,
    LNURLPayInvalidRangeError,
    LNURLPayPlanUnavailableError,
    LNURLPayPricingExpiredError,
    LNURLPayUnknownPlanError,
)

DEFAULT_PLAN_PRICES_MSAT: dict[PlanCode, int] = {
    PlanCode.LITE: 10_000_000,
    PlanCode.BASIC: 50_000_000,
    PlanCode.PLUS: 150_000_000,
    PlanCode.PRO: 500_000_000,
    PlanCode.BUSINESS: 2_000_000_000,
    PlanCode.ENTERPRISE: 10_000_000_000,
}


@dataclass(frozen=True, slots=True)
class SubscriptionPriceQuote:
    plan_code: PlanCode
    product_code: str
    billing_period: str
    fixed_amount_msat: int | None
    min_amount_msat: int
    max_amount_msat: int
    pricing_version: str
    quote_expires_at: datetime
    price_source: str
    policy_hash: str
    variable_amount: bool = False

    def validate_amount(self, requested_amount_msat: int | None) -> int | None:
        if self.min_amount_msat < 1 or self.max_amount_msat < self.min_amount_msat:
            raise LNURLPayInvalidRangeError("Invalid LNURL-pay amount range")
        if self.fixed_amount_msat is not None and self.fixed_amount_msat <= 0:
            raise LNURLPayInvalidAmountError("Fixed amount must be positive")
        if requested_amount_msat is None:
            return self.fixed_amount_msat
        if not isinstance(requested_amount_msat, int) or isinstance(requested_amount_msat, bool):
            raise LNURLPayInvalidAmountError("Amount must be integer millisatoshis")
        if requested_amount_msat < self.min_amount_msat or requested_amount_msat > self.max_amount_msat:
            raise LNURLPayInvalidAmountError("Requested amount is outside allowed range")
        return requested_amount_msat


class SubscriptionPricingResolver(Protocol):
    def resolve_price(
        self,
        *,
        plan_code: PlanCode | str,
        product_code: str,
        requested_amount_msat: int | None = None,
    ) -> SubscriptionPriceQuote: ...


class StaticSubscriptionPricingResolver:
    """Deterministic resolver used until a product pricing store is wired in."""

    def __init__(
        self,
        prices_msat: Mapping[PlanCode | str, int] | None = None,
        *,
        disabled_plans: set[PlanCode | str] | None = None,
        variable_ranges_msat: Mapping[PlanCode | str, tuple[int, int]] | None = None,
        variable_amount_enabled: bool = False,
        billing_period: str = "monthly",
        pricing_version: str = "static-2026-07",
        quote_ttl_seconds: int = 600,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.clock = clock or (lambda: datetime.now(UTC))
        self.prices_msat = {normalize_plan_code(k): v for k, v in (prices_msat or DEFAULT_PLAN_PRICES_MSAT).items()}
        self.disabled_plans = {normalize_plan_code(plan) for plan in (disabled_plans or set())}
        self.variable_ranges_msat = {normalize_plan_code(k): v for k, v in (variable_ranges_msat or {}).items()}
        self.variable_amount_enabled = variable_amount_enabled
        self.billing_period = billing_period
        self.pricing_version = pricing_version
        self.quote_ttl_seconds = quote_ttl_seconds

    def resolve_price(
        self,
        *,
        plan_code: PlanCode | str,
        product_code: str,
        requested_amount_msat: int | None = None,
    ) -> SubscriptionPriceQuote:
        try:
            plan = normalize_plan_code(plan_code)
        except InvalidPlanCodeError as exc:
            raise LNURLPayUnknownPlanError("Unknown LNURL-pay subscription plan") from exc
        if plan in self.disabled_plans:
            raise LNURLPayPlanUnavailableError("Plan is unavailable")
        if product_code.strip() == "sovereign_mode":
            raise LNURLPayUnknownPlanError("Sovereign Mode is not a subscription plan")
        now = self.clock()
        if self.quote_ttl_seconds <= 0:
            raise LNURLPayPricingExpiredError("Pricing quote TTL must be positive")
        if plan in self.variable_ranges_msat:
            if not self.variable_amount_enabled:
                raise LNURLPayPlanUnavailableError("Variable LNURL-pay pricing is disabled")
            min_amount, max_amount = self.variable_ranges_msat[plan]
            quote = SubscriptionPriceQuote(
                plan_code=plan,
                product_code=product_code,
                billing_period=self.billing_period,
                fixed_amount_msat=None,
                min_amount_msat=min_amount,
                max_amount_msat=max_amount,
                pricing_version=self.pricing_version,
                quote_expires_at=now + timedelta(seconds=self.quote_ttl_seconds),
                price_source="static_policy",
                policy_hash=hash_canonical_json_prefixed({"plan": plan.value, "range": [min_amount, max_amount], "version": self.pricing_version}),
                variable_amount=True,
            )
        else:
            amount = self.prices_msat.get(plan)
            if amount is None:
                raise LNURLPayPlanUnavailableError("Plan price is unavailable")
            quote = SubscriptionPriceQuote(
                plan_code=plan,
                product_code=product_code,
                billing_period=self.billing_period,
                fixed_amount_msat=amount,
                min_amount_msat=amount,
                max_amount_msat=amount,
                pricing_version=self.pricing_version,
                quote_expires_at=now + timedelta(seconds=self.quote_ttl_seconds),
                price_source="static_policy",
                policy_hash=hash_canonical_json_prefixed({"plan": plan.value, "amount_msat": amount, "version": self.pricing_version}),
            )
        quote.validate_amount(requested_amount_msat)
        return quote
