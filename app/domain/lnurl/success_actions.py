"""LNURL successAction and activation domain primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

LNURL_SUCCESS_MESSAGE_MAX_LENGTH = 144
LNURL_SUCCESS_DESCRIPTION_MAX_LENGTH = 144
LNURL_ACTIVATION_REFERENCE_BYTES = 32
LNURL_ACTIVATION_DEFAULT_TTL_SECONDS = 3600
LNURL_ACTIVATION_MAX_TTL_SECONDS = 86400
LNURL_SUCCESS_ACTION_ALLOWED_SCHEMES = frozenset({"https"})
LNURL_SUCCESS_ACTION_ONION_SCHEMES = frozenset({"http", "https"})

_FORBIDDEN_URL_TERMS = (
    "access_pass",
    "session_token",
    "recovery",
    "private_key",
    "seed",
    "mnemonic",
    "xprv",
    "preimage",
)


class LNURLSuccessActionType(StrEnum):
    """Externally supported LNURL successAction tags."""

    MESSAGE = "message"
    URL = "url"


class LNURLActivationPurpose(StrEnum):
    """Server-side purpose for an opaque post-payment activation reference."""

    SUBSCRIPTION_ACTIVATION = "subscription_activation"
    SUBSCRIPTION_RENEWAL = "subscription_renewal"
    SUBSCRIPTION_UPGRADE = "subscription_upgrade"
    VAULT_SETUP = "vault_setup"
    ACCESS_CERTIFICATE_SETUP = "access_certificate_setup"
    PAYREGISTER_RECEIPT = "payregister_receipt"
    MERCHANT_RECEIPT = "merchant_receipt"
    BUSINESS_ONBOARDING = "business_onboarding"
    ENTERPRISE_ONBOARDING = "enterprise_onboarding"
    PAYMENT_RECEIPT = "payment_receipt"
    CONTRIBUTION_RECEIPT = "contribution_receipt"


class LNURLActivationStatus(StrEnum):
    """Activation state machine; early states never imply settlement or access."""

    CREATED = "created"
    INVOICE_ISSUED = "invoice_issued"
    PAYMENT_PENDING = "payment_pending"
    PAYMENT_SETTLED = "payment_settled"
    ENTITLEMENT_PENDING = "entitlement_pending"
    READY = "ready"
    OPENED = "opened"
    COMPLETED = "completed"
    EXPIRED = "expired"
    REVOKED = "revoked"
    REFUNDED = "refunded"
    FAILED = "failed"


class BastionSuccessActionPurpose(StrEnum):
    """Backward-compatible purpose enum used by earlier LNURL-pay prompts."""

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


def contains_forbidden_success_action_secret(value: str) -> bool:
    """Return true when text appears to contain material forbidden in successAction output."""

    lowered = value.lower()
    return any(term in lowered for term in _FORBIDDEN_URL_TERMS)
