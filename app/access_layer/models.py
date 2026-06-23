"""
Models for the Bastion Proof‑of‑Access Auth PQ layer.

These pydantic models define the core data structures used by the access
layer: payment proofs, access certificates, subscription entitlements
and API entitlements. They mirror the conceptual structure described in
the Bastion Proof‑of‑Access Auth PQ specification:

* A user pays for a tier of service and receives an immutable payment proof.
* The backend issues a signed access certificate bound to a device key.
* Subscription entitlements describe which metric groups, limits and quotas
  are granted for the subscribed tier.
* API entitlements further refine the allowed API surface (history range,
  interval granularity, websocket streams, number of child API keys, etc).

These models are deliberately simple and do not implement cryptographic
functions. Implementers must ensure that secrets (private keys, session
keys) are kept off-server and that hashes use HMAC‑SHA256 where appropriate.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class PaymentStatus(str, Enum):
    """Enumerated status values for payment proofs."""

    CREATED = "created"
    PENDING = "pending"
    PAID = "paid"
    EXPIRED = "expired"
    FAILED = "failed"


class PaymentProof(BaseModel):
    """
    Record of a payment event that grants entitlement to an access certificate.

    The `payment_id_hash` and `invoice_hash` fields should be derived using
    HMAC‑SHA256 with a server pepper so that leaked database content does not
    reveal the underlying payment identifiers. The `amount` should be expressed
    in satoshis for Lightning payments or satoshis for on‑chain payments.
    """

    payment_id_hash: str
    invoice_hash: str
    amount: int
    status: PaymentStatus = PaymentStatus.PENDING
    timestamp: datetime
    product_tier: str


class ApiEntitlements(BaseModel):
    """
    Defines per‑tier API entitlements for metrics access.

    * `metric_groups` lists high‑level categories of metrics that are enabled
      for the tier (e.g. market.intelligence, signals.standard).
    * `max_history_days` controls how far back historical queries may go.
    * `min_interval` defines the smallest time granularity accepted (e.g. '1m').
    * `websocket_streams` limits concurrent websocket streams.
    * `batch_query` indicates whether multiple metrics may be requested at once.
    * `child_api_keys` limits how many derived API keys may be created.
    """

    metric_groups: List[str] = Field(default_factory=list)
    max_history_days: int = 0
    min_interval: str = "1h"
    websocket_streams: int = 0
    batch_query: bool = False
    child_api_keys: int = 0


class SubscriptionEntitlement(BaseModel):
    """
    Describes a subscription plan bound to an access certificate.

    The subscription describes the plan name (e.g. 'lite_pass', 'pro_pass'),
    its lifecycle status, validity period, metric entitlements and request
    limits. A cryptographic signature from the Bastion issuer should be
    included in `issuer_signature` to bind the entitlement to the certificate.
    """

    plan: str
    status: str = "active"
    valid_from: datetime
    valid_until: datetime
    metric_entitlements: Dict[str, int] = Field(
        default_factory=dict,
        description="Mapping of metric group names to daily credit allowances.",
    )
    limits: Dict[str, int] = Field(
        default_factory=dict, description="Optional request/per‑minute or per‑day limits."
    )
    issuer_signature: Dict[str, str] = Field(
        default_factory=dict,
        description="Signature over the entitlement using the issuer private key.",
    )


class AccessCertificate(BaseModel):
    """
    Signed access certificate granting rights to the Bastion platform.

    An access certificate is a signed statement from the issuer that binds a
    subscription tier and a set of scopes to a device public key. The
    `pass_commitment` and `pass_lookup_hash` values are cryptographic
    commitments derived from a unique pass identifier using HMAC‑SHA256. The
    `public_keys` mapping may include classical and post‑quantum variants.

    The certificate alone does not grant access. Clients must prove
    possession of the corresponding private key and satisfy policy checks.
    """

    type: str = "bastion_access_certificate"
    version: int = 1
    pass_commitment: str
    pass_lookup_hash: str
    certificate_fingerprint: str
    tier: str
    public_keys: Dict[str, str] = Field(default_factory=dict)
    scopes: List[str] = Field(default_factory=list)
    subscription: Optional[SubscriptionEntitlement] = None
    api_entitlements: Optional[ApiEntitlements] = None
    issued_at: datetime
    expires_at: datetime
    crypto_epoch: int = 1
    hash_suite: Dict[str, str] = Field(
        default_factory=lambda: {"primary": "SHA-256"},
        description="Indicates the primary and secondary hash algorithms.",
    )
    issuer_signatures: Dict[str, Dict[str, str]] = Field(
        default_factory=dict,
        description="Issuer signatures keyed by algorithm name (e.g. classical, post_quantum).",
    )


class SessionStatus(str, Enum):
    """Status values for proof‑of‑possession sessions."""

    ACTIVE = "active"
    EXPIRED = "expired"
    FROZEN = "frozen"
    REVOKED = "revoked"


class AccessSession(BaseModel):
    """
    Represents a short‑lived proof‑of‑possession session.

    After clients present a challenge signed with their device private key,
    the backend issues a session token and a session public key. Every API
    request must be signed with the session private key and validated against
    quotas, scopes, and policy.
    """

    session_id: str
    session_token: str
    session_key_fingerprint: str
    scopes: List[str]
    created_at: datetime
    expires_at: datetime
    status: SessionStatus = SessionStatus.ACTIVE
