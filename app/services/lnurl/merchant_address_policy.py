"""Policy hooks for Merchant Lightning Address management and resolution."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class MerchantAddressPolicyDecision:
    allowed: bool
    reason_code: str = "allowed"
    requires_step_up: bool = False
    policy_hash: str = "sha256:merchant-ln-policy-v1"


class MerchantAddressPolicyHook(Protocol):
    def evaluate(self, action: str, context: dict[str, Any]) -> MerchantAddressPolicyDecision: ...


class AllowMerchantAddressPolicy:
    def evaluate(self, action: str, context: dict[str, Any]) -> MerchantAddressPolicyDecision:
        return MerchantAddressPolicyDecision(True)


POLICY_ACTIONS = frozenset(
    {
        "merchant_domain:create",
        "merchant_domain:verify",
        "merchant_address:create",
        "merchant_address:update",
        "merchant_address:activate",
        "merchant_address:suspend",
        "merchant_address:revoke",
        "merchant_address:resolve",
        "merchant_address:bind_store",
        "merchant_address:bind_terminal",
        "merchant_address:bind_cashier_shift",
        "merchant_address:configure_payer_data",
        "merchant_address:configure_success_action",
    }
)
