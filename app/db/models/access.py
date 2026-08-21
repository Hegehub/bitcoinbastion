"""SQLAlchemy models for Bastion Proof-of-Access Auth storage.

These models define storage primitives only. They intentionally store hashes,
fingerprints, public keys, status values, timestamps, and redacted JSON rather
than raw Access Passes, raw sessions, recovery phrases, API key material, or
wallet secrets.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import Boolean, JSON, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow

JsonDict = dict[str, Any]
JsonList = list[dict[str, Any]] | list[str]
_JSON = JSONB().with_variant(JSON(), "sqlite")


class AccessPaymentIntentStatus(StrEnum):
    CREATED = "created"
    PENDING = "pending"
    SETTLED = "settled"
    EXPIRED = "expired"
    INVALID = "invalid"
    CANCELLED = "cancelled"
    FAILED = "failed"


class AccessCertificateStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    FROZEN = "frozen"
    REPLACED = "replaced"

class SubscriptionEntitlementStatus(StrEnum):
    ACTIVE = "active"
    GRACE = "grace"
    EXPIRED = "expired"
    REVOKED = "revoked"
    FROZEN = "frozen"
    UPGRADED = "upgraded"
    DOWNGRADED = "downgraded"


class AccessDeviceStatus(StrEnum):
    ACTIVE = "active"
    PENDING = "pending"
    REVOKED = "revoked"
    FROZEN = "frozen"
    REPLACED = "replaced"


class AccessChallengeStatus(StrEnum):
    CREATED = "created"
    USED = "used"
    EXPIRED = "expired"
    REVOKED = "revoked"


class AccessSessionStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    FROZEN = "frozen"


class AccessRevocationTargetType(StrEnum):
    PASS = "pass"
    CERTIFICATE = "certificate"
    ENTITLEMENT = "entitlement"
    DEVICE = "device"
    SESSION = "session"
    CHILD_API_KEY = "child_api_key"
    DELEGATED_PASS = "delegated_pass"
    OFFLINE_PACK = "offline_pack"
    ISSUER_KEY = "issuer_key"
    RECOVERY_QUORUM = "recovery_quorum"
    WORKSPACE_ROLE = "workspace_role"
    ACCESS_CERTIFICATE = "access_certificate"
    SUBSCRIPTION_ENTITLEMENT = "subscription_entitlement"
    METRIC_ENTITLEMENT = "metric_entitlement"
    ACCESS_DEVICE = "access_device"
    ACCESS_SESSION = "access_session"
    OFFLINE_VALIDITY_PACK = "offline_validity_pack"
    WALLET_PRINCIPAL = "wallet_principal"
    BITCOIN_WALLET_PRINCIPAL = "bitcoin_wallet_principal"
    LIGHTNING_WALLET_PRINCIPAL = "lightning_wallet_principal"
    WALLET_PROOF = "wallet_proof"
    WALLET_DEVICE = "wallet_device"
    WALLET_SESSION = "wallet_session"
    WALLET_STEP_UP_PROOF = "wallet_step_up_proof"
    WALLET_RECOVERY_CAPSULE = "wallet_recovery_capsule"
    MULTI_WALLET_QUORUM = "multi_wallet_quorum"
    LNURL_AUTH_KEY = "lnurl_auth_key"
    LNURL_AUTH_CHALLENGE = "lnurl_auth_challenge"
    LNURL_K1 = "lnurl_k1"
    LNURL_PAY_REQUEST = "lnurl_pay_request"
    LNURL_PAYMENT_PROOF = "lnurl_payment_proof"
    LNURL_WITHDRAW_REQUEST = "lnurl_withdraw_request"
    LIGHTNING_ADDRESS = "lightning_address"
    BUSINESS_WORKSPACE = "business_workspace"
    BUSINESS_ROLE_BINDING = "business_role_binding"
    PAYREGISTER_DEVICE = "payregister_device"
    PAYREGISTER_TERMINAL = "payregister_terminal"
    PAYREGISTER_CASHIER_SHIFT = "payregister_cashier_shift"
    TRANSPARENCY_CHECKPOINT = "transparency_checkpoint"
    TRANSPARENCY_PUBLICATION = "transparency_publication"
    TRANSPARENCY_STREAM = "transparency_stream"


class RecoveryAttemptStatus(StrEnum):
    STARTED = "started"
    FACTOR_VERIFIED = "factor_verified"
    COOLDOWN = "cooldown"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    LOCKED = "locked"


class AccessPaymentIntent(Base):
    __tablename__ = "access_payment_intents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_method: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    provider_invoice_id_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    invoice_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    payment_id_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    amount_sats: Mapped[int] = mapped_column(Integer, nullable=False)
    plan_code: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default=AccessPaymentIntentStatus.CREATED.value)
    checkout_url_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    subscription_period_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    checkout_id: Mapped[str | None] = mapped_column(
        ForeignKey("access_checkout_sessions.id"), nullable=True, unique=True, index=True
    )


class AccessCheckoutSession(Base):
    """Persistent immutable-terms bridge between an Offer and future issuance."""

    __tablename__ = "access_checkout_sessions"

    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    idempotency_key_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    offer_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    offer_revision_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    plan_code: Mapped[str] = mapped_column(String(40), nullable=False)
    capability: Mapped[str] = mapped_column(String(80), nullable=False)
    scopes_json: Mapped[JsonList] = mapped_column(_JSON, nullable=False, default=list)
    amount_sats: Mapped[int] = mapped_column(Integer, nullable=False)
    price_unit: Mapped[str] = mapped_column(String(16), nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    terms_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    eligibility_reason: Mapped[str] = mapped_column(String(48), nullable=False)
    payment_intent_id: Mapped[int | None] = mapped_column(Integer, nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)


class AccessIssuanceChallenge(Base):
    """One-time device proof bound to one frozen checkout."""

    __tablename__ = "access_issuance_challenges"

    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    checkout_id: Mapped[str] = mapped_column(ForeignKey("access_checkout_sessions.id"), nullable=False, index=True)
    device_public_key: Mapped[str] = mapped_column(Text, nullable=False)
    device_key_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    payload_json: Mapped[JsonDict] = mapped_column(_JSON, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    protocol_version: Mapped[str] = mapped_column(String(32), nullable=False)
    operation: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AccessIssuedGrant(Base):
    """Non-secret issued Access authority; exactly one grant per checkout."""

    __tablename__ = "access_issued_grants"

    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    checkout_id: Mapped[str] = mapped_column(ForeignKey("access_checkout_sessions.id"), nullable=False, unique=True)
    offer_revision_id: Mapped[str] = mapped_column(String(128), nullable=False)
    certificate_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    device_key_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    capability: Mapped[str] = mapped_column(String(80), nullable=False)
    scopes_json: Mapped[JsonList] = mapped_column(_JSON, nullable=False)
    terms_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class AccessCertificate(Base):
    __tablename__ = "access_certificates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pass_lookup_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    pass_commitment: Mapped[str] = mapped_column(String(128), nullable=False)
    certificate_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    plan_code: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default=AccessCertificateStatus.ACTIVE.value)
    device_key_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    primary_device_id: Mapped[int | None] = mapped_column(ForeignKey("access_devices.id"), nullable=True)
    issuer_key_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    crypto_epoch: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    hash_suite_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)
    scopes_json: Mapped[JsonList] = mapped_column(_JSON, nullable=False, default=list)
    public_keys_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)
    issuer_signature_json: Mapped[JsonDict] = mapped_column(_JSON, nullable=False, default=dict)
    issuer_envelope_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)
    issuer_envelope_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    signature_requirement_policy: Mapped[str | None] = mapped_column(String(60), nullable=True)
    crypto_assurance: Mapped[str | None] = mapped_column(String(40), nullable=True)
    requires_reissue: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    replaced_by_certificate_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)


class AccessCertificatePrincipalBinding(Base):
    __tablename__ = "access_certificate_principal_bindings"
    __table_args__ = (
        UniqueConstraint("certificate_id", name="uq_access_certificate_principal_binding_cert"),
        UniqueConstraint(
            "principal_binding_hash", name="uq_access_certificate_principal_binding_hash"
        ),
        Index("ix_access_certificate_binding_principal_status", "principal_hash", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    certificate_id: Mapped[int] = mapped_column(
        ForeignKey("access_certificates.id"), nullable=False, unique=True, index=True
    )
    certificate_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    principal_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    principal_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    principal_binding_hash: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True, index=True
    )
    proof_method: Mapped[str] = mapped_column(String(60), nullable=False)
    verification_strength: Mapped[str] = mapped_column(String(40), nullable=False)
    device_key_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    entitlement_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    assurance_profile: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    policy_epoch: Mapped[int] = mapped_column(Integer, nullable=False)
    principal_revocation_epoch: Mapped[int] = mapped_column(Integer, nullable=False)
    crypto_epoch: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True, default="active")
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class OfflineValidityPack(Base):
    __tablename__ = "offline_validity_packs"
    __table_args__ = (
        UniqueConstraint("pack_id_hash", name="uq_offline_validity_pack_id_hash"),
        UniqueConstraint("pack_fingerprint", name="uq_offline_validity_pack_fingerprint"),
        Index("ix_offline_pack_principal_status", "principal_hash", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pack_id_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    pack_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    principal_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    principal_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    device_key_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    access_certificate_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    entitlement_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    profile: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    policy_snapshot_json: Mapped[JsonDict] = mapped_column(_JSON, nullable=False)
    signed_pack_json: Mapped[JsonDict] = mapped_column(_JSON, nullable=False)
    revocation_epoch: Mapped[int] = mapped_column(Integer, nullable=False)
    policy_epoch: Mapped[int] = mapped_column(Integer, nullable=False)
    crypto_epoch: Mapped[int] = mapped_column(Integer, nullable=False)
    entitlement_epoch: Mapped[int] = mapped_column(Integer, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    not_before: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    reconcile_before: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True, default="active")
    issuer_key_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    signature_suite: Mapped[str] = mapped_column(String(40), nullable=False)
    issuer_envelope_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)
    issuer_envelope_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    signature_requirement_policy: Mapped[str | None] = mapped_column(String(60), nullable=True)
    crypto_assurance: Mapped[str | None] = mapped_column(String(40), nullable=True)
    requires_reissue: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class OfflinePackReconciliation(Base):
    __tablename__ = "offline_pack_reconciliations"
    __table_args__ = (UniqueConstraint("pack_id", "event_chain_root", name="uq_offline_reconcile_pack_root"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pack_id: Mapped[int] = mapped_column(ForeignKey("offline_validity_packs.id"), nullable=False, index=True)
    event_chain_root: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    event_count: Mapped[int] = mapped_column(Integer, nullable=False)
    reconciliation_status: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    reconciled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    result_json: Mapped[JsonDict] = mapped_column(_JSON, nullable=False)
    audit_event_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)


class OfflinePackLocalEvent(Base):
    """Durable device-local queue representation; deployments may store it in Local Vault."""

    __tablename__ = "offline_pack_local_events"
    __table_args__ = (
        UniqueConstraint("pack_id", "sequence_number", name="uq_offline_local_event_sequence"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pack_id: Mapped[int] = mapped_column(ForeignKey("offline_validity_packs.id"), nullable=False, index=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_event_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    event_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    safe_details_json: Mapped[JsonDict] = mapped_column(_JSON, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    reconciled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)


class SubscriptionEntitlement(Base):
    __tablename__ = "subscription_entitlements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pass_lookup_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    certificate_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    plan_code: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default=SubscriptionEntitlementStatus.ACTIVE.value)
    metric_entitlements_json: Mapped[JsonDict] = mapped_column(_JSON, nullable=False, default=dict)
    limits_json: Mapped[JsonDict] = mapped_column(_JSON, nullable=False, default=dict)
    scopes_json: Mapped[JsonList | None] = mapped_column(_JSON, nullable=True)
    issuer_key_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    issuer_signature_json: Mapped[JsonDict] = mapped_column(_JSON, nullable=False, default=dict)
    issuer_envelope_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)
    issuer_envelope_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    signature_requirement_policy: Mapped[str | None] = mapped_column(String(60), nullable=True)
    crypto_assurance: Mapped[str | None] = mapped_column(String(40), nullable=True)
    requires_reissue: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    crypto_epoch: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    valid_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    grace_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    previous_entitlement_id: Mapped[int | None] = mapped_column(ForeignKey("subscription_entitlements.id"), nullable=True)
    replaced_by_entitlement_id: Mapped[int | None] = mapped_column(ForeignKey("subscription_entitlements.id"), nullable=True)
    upgrade_from_plan: Mapped[str | None] = mapped_column(String(40), nullable=True)
    downgrade_from_plan: Mapped[str | None] = mapped_column(String(40), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    frozen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)


class AccessDevice(Base):
    __tablename__ = "access_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    certificate_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    device_key_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    device_public_key: Mapped[str] = mapped_column(Text, nullable=False)
    device_class: Mapped[str] = mapped_column(String(40), nullable=False, default="unknown")
    attestation_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default=AccessDeviceStatus.PENDING.value)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)


class AccessChallenge(Base):
    __tablename__ = "access_challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    challenge_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    certificate_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    device_key_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    origin: Mapped[str] = mapped_column(String(2048), nullable=False)
    requested_scopes_json: Mapped[JsonList] = mapped_column(_JSON, nullable=False, default=list)
    requested_action: Mapped[str | None] = mapped_column(String(255), nullable=True)
    server_nonce_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    client_nonce_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    challenge_payload_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default=AccessChallengeStatus.CREATED.value)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)


class AccessSession(Base):
    __tablename__ = "access_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    certificate_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    device_key_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    entitlement_id: Mapped[int | None] = mapped_column(ForeignKey("subscription_entitlements.id"), nullable=True)
    challenge_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    session_key_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    scopes_json: Mapped[JsonList] = mapped_column(_JSON, nullable=False, default=list)
    policy_context_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default=AccessSessionStatus.ACTIVE.value)
    risk_level: Mapped[str] = mapped_column(String(30), nullable=False, default="low")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    frozen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AccessRequestNonce(Base):
    __tablename__ = "access_request_nonces"
    __table_args__ = (UniqueConstraint("session_hash", "nonce_hash", name="uq_access_request_nonces_session_nonce"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    nonce_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    request_digest: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)


class AccessRevocation(Base):
    __tablename__ = "access_revocations"
    __table_args__ = (
        UniqueConstraint("target_type", "target_hash", "revocation_epoch", name="uq_access_revocations_target_epoch"),
        Index("ix_access_revocations_target", "target_type", "target_hash"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    target_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    target_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    revocation_epoch: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_by_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    signature_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)


class AccessAuditEvent(Base):
    __tablename__ = "access_audit_events"
    __table_args__ = (
        UniqueConstraint("chain_id", "sequence_number", name="uq_access_audit_chain_sequence"),
        UniqueConstraint("chain_id", "idempotency_key_hash", name="uq_access_audit_chain_idempotency"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    previous_event_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    event_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    chain_id: Mapped[str] = mapped_column(String(80), nullable=False, default="access-security", index=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    idempotency_key_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    event_category: Mapped[str] = mapped_column(String(40), nullable=False, default="security", index=True)
    event_status: Mapped[str] = mapped_column(String(30), nullable=False, default="success", index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="info", index=True)
    retention_class: Mapped[str] = mapped_column(String(30), nullable=False, default="security", index=True)
    actor_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    object_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    canonical_event_json: Mapped[JsonDict] = mapped_column(_JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)


class TransparencyCheckpointRecord(Base):
    """Immutable signed checkpoint fields plus separately mutable lifecycle status."""

    __tablename__ = "transparency_checkpoints"
    __table_args__ = (
        UniqueConstraint("stream_id_hash", "sequence_number", name="uq_transparency_stream_sequence"),
        UniqueConstraint("batch_identity_hash", name="uq_transparency_batch_identity"),
        Index("ix_transparency_type_created", "checkpoint_type", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    checkpoint_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    checkpoint_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    schema_epoch: Mapped[int] = mapped_column(Integer, nullable=False)
    crypto_epoch: Mapped[int] = mapped_column(Integer, nullable=False)
    policy_epoch: Mapped[int] = mapped_column(Integer, nullable=False)
    issuer_key_id: Mapped[str] = mapped_column(String(120), nullable=False)
    hash_suite: Mapped[str] = mapped_column(String(30), nullable=False)
    signature_suite: Mapped[str] = mapped_column(String(50), nullable=False)
    visibility: Mapped[str] = mapped_column(String(40), nullable=False)
    stream_id_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    batch_identity_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    source_count: Mapped[int] = mapped_column(Integer, nullable=False)
    batch_start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    batch_end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    root_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    previous_checkpoint_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    checkpoint_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    metadata_commitment: Mapped[str | None] = mapped_column(String(128), nullable=True)
    issuer_envelope_json: Mapped[JsonDict] = mapped_column(_JSON, nullable=False)
    post_quantum_signature_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)
    publication_status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    verification_status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    signed_payload_json: Mapped[JsonDict] = mapped_column(_JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    supersedes_checkpoint_id: Mapped[str | None] = mapped_column(String(128), nullable=True)


class TransparencyCheckpointSource(Base):
    __tablename__ = "transparency_checkpoint_sources"
    __table_args__ = (
        UniqueConstraint("checkpoint_id", "leaf_index", name="uq_transparency_source_index"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    checkpoint_id: Mapped[str] = mapped_column(
        ForeignKey("transparency_checkpoints.checkpoint_id"), nullable=False, index=True
    )
    leaf_index: Mapped[int] = mapped_column(Integer, nullable=False)
    leaf_type: Mapped[str] = mapped_column(String(80), nullable=False)
    leaf_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    object_commitment: Mapped[str] = mapped_column(String(128), nullable=False)
    event_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)

class AccessHumanIntent(Base):
    __tablename__ = "access_human_intents"
    __table_args__ = (
        Index("ix_access_human_intents_cert_action", "certificate_fingerprint", "action"),
        Index("ix_access_human_intents_status_expires", "status", "expires_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    intent_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    certificate_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    device_key_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default="created")
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    canonical_manifest_json: Mapped[JsonDict] = mapped_column(_JSON, nullable=False, default=dict)
    signature_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)


class MetricUsage(Base):
    __tablename__ = "metric_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pass_lookup_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    session_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    metric_group: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    credit_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    request_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)


class ChildApiKey(Base):
    __tablename__ = "child_api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_pass_lookup_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    key_id_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    key_secret_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    scopes_json: Mapped[JsonList] = mapped_column(_JSON, nullable=False, default=list)
    limits_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)
    cannot_access_json: Mapped[JsonList | None] = mapped_column(_JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default=AccessSessionStatus.ACTIVE.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class DelegatedPass(Base):
    __tablename__ = "delegated_passes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_pass_lookup_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    delegated_pass_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    delegated_to_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    scopes_json: Mapped[JsonList] = mapped_column(_JSON, nullable=False, default=list)
    constraints_json: Mapped[JsonDict] = mapped_column(_JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default=AccessSessionStatus.ACTIVE.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    valid_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class RecoveryQuorum(Base):
    __tablename__ = "recovery_quorums"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pass_lookup_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    certificate_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    quorum_type: Mapped[str] = mapped_column(String(80), nullable=False)
    threshold_required: Mapped[int] = mapped_column(Integer, nullable=False)
    total_factors: Mapped[int] = mapped_column(Integer, nullable=False)
    factors_json: Mapped[JsonList] = mapped_column(_JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default=AccessCertificateStatus.ACTIVE.value)
    policy_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class RecoveryAttempt(Base):
    __tablename__ = "recovery_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pass_lookup_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    recovery_quorum_id: Mapped[int | None] = mapped_column(ForeignKey("recovery_quorums.id"), nullable=True)
    attempt_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default=RecoveryAttemptStatus.STARTED.value)
    verified_factors_json: Mapped[JsonList | None] = mapped_column(_JSON, nullable=True)
    failed_factor_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cooldown_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)
