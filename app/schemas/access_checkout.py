from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.domain.access.plans import PlanCode


class OfferAvailability(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class CheckoutStatus(StrEnum):
    AWAITING_PAYMENT = "awaiting_payment"
    ELIGIBLE = "eligible"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    FAILED = "failed"
    ISSUED = "issued"


class EligibilityReason(StrEnum):
    PAYMENT_PENDING = "payment_pending"
    PAYMENT_SETTLED = "payment_settled"
    CHECKOUT_EXPIRED = "checkout_expired"
    TERMINAL_STATE = "terminal_state"


class AccessOfferOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    offer_id: str
    revision_id: str
    plan_code: PlanCode
    capability: str
    scopes: tuple[str, ...]
    amount_sats: int = Field(ge=0)
    price_unit: str
    duration_days: int = Field(gt=0)
    terms_version: str
    availability: OfferAvailability
    limitations: tuple[str, ...]


class CheckoutCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    offer_id: str
    payment_method: str = "manual"
    idempotency_key: str = Field(min_length=16, max_length=128)


class CheckoutOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    checkout_id: str
    offer_id: str
    offer_revision_id: str
    plan_code: PlanCode
    capability: str
    scopes: tuple[str, ...]
    amount_sats: int
    price_unit: str
    duration_days: int
    terms_version: str
    status: CheckoutStatus
    issuance_eligible: bool
    eligibility_reason: EligibilityReason
    payment_intent_id: int | None
    created_at: datetime
    expires_at: datetime


class IssuanceChallengeCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    checkout_id: str
    device_public_key: str


class IssuanceChallengeOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    challenge_id: str
    checkout_id: str
    canonical_payload: str
    protocol_version: str
    algorithm: str
    expires_at: datetime


class AccessIssueRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    checkout_id: str
    challenge_id: str
    signature: str
    idempotency_key: str = Field(min_length=16, max_length=128)


class IssuedAccessOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    grant_id: str
    checkout_id: str
    offer_revision_id: str
    certificate_fingerprint: str
    device_key_fingerprint: str
    capability: str
    scopes: tuple[str, ...]
    terms_version: str
    status: str
    issued_at: datetime
    expires_at: datetime
