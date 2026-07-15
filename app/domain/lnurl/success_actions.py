"""LNURL successAction domain primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

_FORBIDDEN_URL_TERMS = ("access_pass", "session_token", "recovery", "private_key", "seed", "mnemonic", "xprv")


class LNURLSuccessActionType(StrEnum):
    MESSAGE = "message"
    URL = "url"


class BastionSuccessActionPurpose(StrEnum):
    SUBSCRIPTION_ACTIVATED = "subscription_activated"
    SUBSCRIPTION_RENEWED = "subscription_renewed"
    SUBSCRIPTION_UPGRADED = "subscription_upgraded"
    RECEIPT = "receipt"
    VAULT_SETUP = "vault_setup"
    PAYREGISTER_RECEIPT = "payregister_receipt"
    BUSINESS_ONBOARDING = "business_onboarding"
    MERCHANT_CONFIRMATION = "merchant_confirmation"


@dataclass(frozen=True, slots=True)
class LNURLSuccessActionDescriptor:
    action_type: LNURLSuccessActionType
    purpose: BastionSuccessActionPurpose
    description: str
    message: str | None = None
    url_reference: str | None = None
    expires_at: datetime | None = None
    requires_entitlement_check: bool = True

    def __post_init__(self) -> None:
        if not self.description.strip():
            raise ValueError("success_action_description_required")
        haystack = " ".join(value for value in (self.description, self.message or "", self.url_reference or "")).lower()
        if any(term in haystack for term in _FORBIDDEN_URL_TERMS):
            raise ValueError("success_action_forbidden_secret_reference")
        if self.action_type is LNURLSuccessActionType.URL and not self.url_reference:
            raise ValueError("success_action_url_reference_required")
