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

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
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
    issued_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    replaced_by_certificate_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)


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
    issuer_signature_json: Mapped[JsonDict] = mapped_column(_JSON, nullable=False, default=dict)
    valid_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    grace_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    previous_entitlement_id: Mapped[int | None] = mapped_column(ForeignKey("subscription_entitlements.id"), nullable=True)
    upgrade_from_plan: Mapped[str | None] = mapped_column(String(40), nullable=True)
    downgrade_from_plan: Mapped[str | None] = mapped_column(String(40), nullable=True)
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

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    previous_event_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    actor_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    object_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    canonical_event_json: Mapped[JsonDict] = mapped_column(_JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)


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
