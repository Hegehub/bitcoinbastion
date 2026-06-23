"""
Pydantic request/response schemas for the Bastion access layer API.

These schemas represent typical payloads and responses for payment intents,
certificate issuance and session creation. They refer to the core models
defined in `models.py` for reuse.
"""
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .models import ApiEntitlements, SubscriptionEntitlement, AccessCertificate, PaymentProof


class PaymentIntentCreateRequest(BaseModel):
    """Client request to initiate a payment for a subscription tier."""

    amount: int = Field(..., ge=1, description="Amount in satoshis to pay for the subscription.")
    tier: str = Field(..., description="Subscription plan identifier (e.g. 'lite_pass').")


class PaymentIntentResponse(BaseModel):
    """Response returned after creating a payment intent."""

    payment_id_hash: str
    invoice_hash: str
    amount: int
    status: str
    expires_at: Optional[datetime] = None


class CertificateIssueRequest(BaseModel):
    """Client request to issue an access certificate after paying."""

    payment_id_hash: str = Field(..., description="Hashed identifier of the paid payment intent.")
    device_public_keys: Dict[str, str] = Field(
        ..., description="Map of device public key type to key string."
    )
    tier: str = Field(..., description="Subscription tier the certificate should grant.")
    subscription: Optional[SubscriptionEntitlement] = None
    scopes: Optional[List[str]] = None


class AccessCertificateResponse(AccessCertificate):
    """Response containing a signed access certificate."""
    pass
