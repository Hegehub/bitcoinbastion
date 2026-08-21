from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChildKeyCreatedViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    key_id: str
    scopes: tuple[str, ...]
    expires_at: datetime
    warning: str | None


class AccessOfferViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    offer_id: str
    revision_id: str
    capability: str
    scopes: tuple[str, ...]
    amount_sats: int
    price_unit: str
    duration_days: int
    terms_version: str
    limitations: tuple[str, ...]


class AccessCheckoutViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    checkout_id: str
    offer_revision_id: str
    capability: str
    scopes: tuple[str, ...]
    amount_sats: int
    price_unit: str
    duration_days: int
    terms_version: str
    status: str
    issuance_eligible: bool
    eligibility_reason: str
    expires_at: datetime


class AccessChallengeViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    challenge_id: str
    checkout_id: str
    canonical_payload: str
    protocol_version: str
    algorithm: str
    expires_at: datetime


class IssuedAccessViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
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
