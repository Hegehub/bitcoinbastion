"""Policy and revocation hooks for PayRegister LNURL-pay."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class PayRegisterLNURLPolicyDecision:
    allowed: bool
    reason_code: str = "allowed"
    policy_hash: str = "policy:payregister-lnurl-static-v1"


class PayRegisterLNURLPolicyHook(Protocol):
    def evaluate(self, action: str, context: Mapping[str, Any]) -> PayRegisterLNURLPolicyDecision: ...


class AllowPayRegisterLNURLPolicy:
    def evaluate(self, action: str, context: Mapping[str, Any]) -> PayRegisterLNURLPolicyDecision:
        return PayRegisterLNURLPolicyDecision(True)


class PayRegisterLNURLRevocationChecker(Protocol):
    def is_revoked(self, target_type: str, target_hash: str) -> bool: ...


class NoopPayRegisterLNURLRevocationChecker:
    def is_revoked(self, target_type: str, target_hash: str) -> bool:
        return False


POLICY_ACTIONS = {
    "endpoint_create": "payregister_lnurl_endpoint_create",
    "endpoint_update": "payregister_lnurl_endpoint_update",
    "endpoint_suspend": "payregister_lnurl_endpoint_suspend",
    "checkout_publish": "payregister_lnurl_checkout_publish",
    "invoice_create": "payregister_lnurl_invoice_create",
    "payment_settle": "payregister_lnurl_payment_settle",
    "receipt_view": "payregister_lnurl_receipt_view",
}
