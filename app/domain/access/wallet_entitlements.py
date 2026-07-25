"""Wallet-bound subscription entitlement domain objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class EntitlementSubjectType(StrEnum):
    BITCOIN_WALLET_PRINCIPAL = "bitcoin_wallet_principal"
    LIGHTNING_WALLET_PRINCIPAL = "lightning_wallet_principal"
    ACCESS_CERTIFICATE = "access_certificate"
    BUSINESS_WORKSPACE = "business_workspace"
    BUSINESS_ROLE = "business_role"
    PAYREGISTER_OWNER = "payregister_owner"
    PAYREGISTER_DEVICE = "payregister_device"
    DELEGATED_PASS = "delegated_pass"
    CHILD_API_KEY = "child_api_key"


class WalletEntitlementStatus(StrEnum):
    PENDING_PAYMENT = "pending_payment"
    PENDING_VERIFICATION = "pending_verification"
    ACTIVE = "active"
    GRACE_PERIOD = "grace_period"
    SUSPENDED = "suspended"
    DOWNGRADE_PENDING = "downgrade_pending"
    EXPIRED = "expired"
    REVOKED = "revoked"
    RECOVERY_LOCKED = "recovery_locked"
    PAYMENT_DISPUTED = "payment_disputed"


class EntitlementPaymentMethod(StrEnum):
    LNURL_PAY = "lnurl_pay"
    LIGHTNING_ADDRESS = "lightning_address"
    LIGHTNING_INVOICE = "lightning_invoice"
    BTCPAY = "btcpay"
    ONCHAIN_BTC = "onchain_btc"
    MANUAL_GRANT = "manual_grant"
    BUSINESS_INVOICE = "business_invoice"
    ENTERPRISE_CONTRACT = "enterprise_contract"
    VOUCHER = "voucher"


@dataclass(frozen=True, slots=True)
class EntitlementLimits:
    requests_per_minute: int | None
    requests_per_day: int | None
    daily_metric_credits: int | None
    monthly_metric_credits: int | None
    history_days: int | None
    minimum_interval_seconds: int | None
    child_api_keys: int | None
    delegated_passes: int | str | None
    concurrent_sessions: int | None = None

    def narrowed_with(self, other: "EntitlementLimits | None") -> "EntitlementLimits":
        if other is None:
            return self

        def minimum(left: int | None, right: int | None) -> int | None:
            if left is None:
                return right
            if right is None:
                return left
            return min(left, right)

        return EntitlementLimits(
            requests_per_minute=minimum(self.requests_per_minute, other.requests_per_minute),
            requests_per_day=minimum(self.requests_per_day, other.requests_per_day),
            daily_metric_credits=minimum(self.daily_metric_credits, other.daily_metric_credits),
            monthly_metric_credits=minimum(self.monthly_metric_credits, other.monthly_metric_credits),
            history_days=minimum(self.history_days, other.history_days),
            minimum_interval_seconds=max(filter(None, [self.minimum_interval_seconds, other.minimum_interval_seconds]), default=None),
            child_api_keys=minimum(self.child_api_keys, other.child_api_keys),
            delegated_passes=self.delegated_passes if other.delegated_passes is None else other.delegated_passes,
            concurrent_sessions=minimum(self.concurrent_sessions, other.concurrent_sessions),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "requests_per_minute": self.requests_per_minute,
            "requests_per_day": self.requests_per_day,
            "daily_metric_credits": self.daily_metric_credits,
            "monthly_metric_credits": self.monthly_metric_credits,
            "history_days": self.history_days,
            "minimum_interval_seconds": self.minimum_interval_seconds,
            "child_api_keys": self.child_api_keys,
            "delegated_passes": self.delegated_passes,
            "concurrent_sessions": self.concurrent_sessions,
        }


@dataclass(frozen=True, slots=True)
class EntitlementAssurance:
    minimum_proof_strength: str = "standard"
    high_risk_step_up_required: bool = True
    access_certificate_required: bool = False
    hardware_wallet_required: bool = False
    quorum_policy: dict[str, Any] | None = None
    sovereign_mode: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "minimum_proof_strength": self.minimum_proof_strength,
            "high_risk_step_up_required": self.high_risk_step_up_required,
            "access_certificate_required": self.access_certificate_required,
            "hardware_wallet_required": self.hardware_wallet_required,
            "quorum_policy": self.quorum_policy,
            "sovereign_mode": self.sovereign_mode,
        }


@dataclass(frozen=True, slots=True)
class IssuerSignatureMetadata:
    alg: str
    key_id: str
    sig: str
    crypto_epoch: int
    public_key_fingerprint: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "alg": self.alg,
            "key_id": self.key_id,
            "sig": self.sig,
            "crypto_epoch": self.crypto_epoch,
            "public_key_fingerprint": self.public_key_fingerprint,
        }


@dataclass(frozen=True, slots=True)
class WalletSubscriptionEntitlement:
    type: str
    version: int
    entitlement_id_hash: str
    subject_type: EntitlementSubjectType
    principal_hash: str
    parent_entitlement_hash: str | None
    workspace_id_hash: str | None
    plan_code: str
    status: WalletEntitlementStatus
    wallet_bound: bool
    payment_method: EntitlementPaymentMethod
    payment_proof_hash: str | None
    metric_groups: frozenset[str]
    scopes: frozenset[str]
    limits: EntitlementLimits
    assurance: EntitlementAssurance
    issued_at: datetime
    valid_from: datetime
    valid_until: datetime
    grace_until: datetime | None
    schema_epoch: int
    policy_epoch: int
    crypto_epoch: int
    issuer_key_id: str
    issuer_signatures: tuple[IssuerSignatureMetadata, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    def signed_payload(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "version": self.version,
            "entitlement_id_hash": self.entitlement_id_hash,
            "subject_type": self.subject_type.value,
            "principal_hash": self.principal_hash,
            "parent_entitlement_hash": self.parent_entitlement_hash,
            "workspace_id_hash": self.workspace_id_hash,
            "plan_code": self.plan_code,
            "status": self.status.value,
            "wallet_bound": self.wallet_bound,
            "payment_method": self.payment_method.value,
            "payment_proof_hash": self.payment_proof_hash,
            "metric_groups": sorted(self.metric_groups),
            "scopes": sorted(self.scopes),
            "limits": self.limits.as_dict(),
            "assurance": self.assurance.as_dict(),
            "issued_at": self.issued_at.isoformat().replace("+00:00", "Z"),
            "valid_from": self.valid_from.isoformat().replace("+00:00", "Z"),
            "valid_until": self.valid_until.isoformat().replace("+00:00", "Z"),
            "grace_until": self.grace_until.isoformat().replace("+00:00", "Z") if self.grace_until else None,
            "schema_epoch": self.schema_epoch,
            "policy_epoch": self.policy_epoch,
            "crypto_epoch": self.crypto_epoch,
            "issuer_key_id": self.issuer_key_id,
            "metadata": self.metadata,
        }

    def public_payload(self) -> dict[str, Any]:
        return {**self.signed_payload(), "issuer_signatures": [sig.as_dict() for sig in self.issuer_signatures]}


@dataclass(frozen=True, slots=True)
class EntitlementRestriction:
    scopes: frozenset[str] | None = None
    metric_groups: frozenset[str] | None = None
    limits: EntitlementLimits | None = None
    requires_step_up: bool = False
    revoked: bool = False
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class EffectiveEntitlement:
    entitlement_id_hash: str
    subject_type: EntitlementSubjectType
    principal_hash: str
    plan_code: str
    status: str
    scopes: frozenset[str]
    metric_groups: frozenset[str]
    limits: EntitlementLimits
    assurance: EntitlementAssurance
    requires_step_up: bool
    policy_decision: str
    reason_codes: tuple[str, ...]
