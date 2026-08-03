from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal


class WalletAuthAction(StrEnum):
    REGISTER = "register"
    LOGIN = "login"
    NEW_DEVICE = "new_device"
    STEP_UP = "step_up"
    RECOVERY = "recovery"
    LOCKDOWN = "lockdown"


class AuthFlowState(StrEnum):
    GENERATING = "generating"
    WAITING_FOR_WALLET = "waiting_for_wallet"
    VERIFYING = "verifying"
    WALLET_VERIFIED = "wallet_verified"
    BINDING_DEVICE = "binding_device"
    CREATING_SESSION = "creating_session"
    AUTHENTICATED = "authenticated"
    EXPIRED = "expired"
    REJECTED = "rejected"
    UNSUPPORTED_WALLET = "unsupported_wallet"
    ERROR = "error"


class PaymentState(StrEnum):
    CREATING_PAYMENT = "creating_payment"
    WAITING_FOR_WALLET = "waiting_for_wallet"
    INVOICE_ISSUED = "invoice_issued"
    PAYMENT_PENDING = "payment_pending"
    VERIFYING = "verifying"
    SETTLED = "settled"
    ACTIVATING_ENTITLEMENT = "activating_entitlement"
    ACTIVE = "active"
    EXPIRED = "expired"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class WalletChallenge:
    challenge_id: str
    canonical_intent: str
    intent_hash: str
    expires_at: str
    network: str
    proof_type: str
    safety_warning: str


@dataclass(frozen=True, slots=True)
class LnurlAuthChallenge:
    challenge_id: str
    lnurl: str
    action: Literal["register", "login", "link", "auth"]
    domain: str
    expires_at: str


@dataclass(frozen=True, slots=True)
class PaymentVerification:
    payment_id: str
    settled: bool
    verified_at: str | None = None
    payment_proof_reference: str | None = None
    entitlement_reference: str | None = None
    success_action: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class PopSessionMetadata:
    session_token: str = field(repr=False)
    principal: str
    expires_at: str
    scopes: tuple[str, ...] = ()
