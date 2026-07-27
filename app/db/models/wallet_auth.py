"""SQLAlchemy models for Wallet-first Proof-of-Access Auth PQ v2.

Model definitions only. These tables intentionally use hashes, fingerprints,
status strings, timestamps, and redacted JSON metadata rather than raw wallet
addresses, raw signatures, raw sessions, raw recovery material, or wallet
secrets.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, JSON, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.time_utils import utcnow

JsonDict = dict[str, Any]
JsonList = list[dict[str, Any]] | list[str]
_JSON = JSONB().with_variant(JSON(), "sqlite")

# metadata_json columns in this module must never contain raw Bitcoin addresses,
# raw LNURL linking keys, raw k1 values, raw private keys, raw seed/mnemonic
# material, raw Access Passes, raw session tokens, raw recovery phrases, raw
# payment preimages, raw issuer private keys, or raw device private keys.


class WalletPrincipal(Base):
    __tablename__ = "wallet_principals"
    __table_args__ = (
        Index("ix_wallet_principals_type_status", "principal_type", "status"),
        Index("ix_wallet_principals_auth_domain_key", "auth_domain", "lnurl_key_hash"),
        UniqueConstraint("principal_hash", name="uq_wallet_principals_principal_hash"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    principal_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    principal_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True, default="pending_verification")
    verification_strength: Mapped[str] = mapped_column(String(40), nullable=False, default="compatibility")
    primary_proof_method: Mapped[str] = mapped_column(String(60), nullable=False)
    network: Mapped[str | None] = mapped_column(String(40), nullable=True)
    address_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    script_pubkey_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    lnurl_key_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    auth_domain: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    product_pseudonym: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    policy_epoch: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    crypto_epoch: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    schema_epoch: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)

    proofs: Mapped[list[WalletProof]] = relationship(back_populates="principal")
    devices: Mapped[list[WalletDevice]] = relationship(back_populates="principal")
    sessions: Mapped[list[WalletSession]] = relationship(back_populates="principal")
    step_up_proofs: Mapped[list[WalletStepUpProof]] = relationship(back_populates="principal")
    recovery_capsules: Mapped[list[RecoveryCapsule]] = relationship(back_populates="principal")


class WalletProof(Base):
    __tablename__ = "bitcoin_wallet_proofs"
    __table_args__ = (Index("ix_wallet_proofs_principal_type", "principal_hash", "proof_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    principal_id: Mapped[int] = mapped_column(ForeignKey("wallet_principals.id"), nullable=False, index=True)
    principal_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    proof_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    proof_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    verification_strength: Mapped[str] = mapped_column(String(40), nullable=False, default="compatibility")
    script_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    network: Mapped[str | None] = mapped_column(String(40), nullable=True)
    key_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    challenge_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    policy_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True, default="created")
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)

    principal: Mapped[WalletPrincipal] = relationship(back_populates="proofs")


class WalletDevice(Base):
    __tablename__ = "wallet_devices"
    __table_args__ = (UniqueConstraint("device_id_hash", name="uq_wallet_devices_device_id_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    principal_id: Mapped[int] = mapped_column(ForeignKey("wallet_principals.id"), nullable=False, index=True)
    principal_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    device_id_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    device_key_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    device_class: Mapped[str] = mapped_column(String(60), nullable=False, index=True, default="unknown")
    binding_method: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True, default="pending")
    risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)

    principal: Mapped[WalletPrincipal] = relationship(back_populates="devices")
    sessions: Mapped[list[WalletSession]] = relationship(back_populates="device")
    step_up_proofs: Mapped[list[WalletStepUpProof]] = relationship(back_populates="device")


class WalletSession(Base):
    __tablename__ = "wallet_sessions"
    __table_args__ = (UniqueConstraint("session_hash", name="uq_wallet_sessions_session_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    principal_id: Mapped[int] = mapped_column(ForeignKey("wallet_principals.id"), nullable=False, index=True)
    principal_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("wallet_devices.id"), nullable=False, index=True)
    device_key_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    session_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    session_public_key_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True, default="active")
    auth_method: Mapped[str] = mapped_column(String(60), nullable=False)
    verification_strength: Mapped[str] = mapped_column(String(40), nullable=False)
    scopes_json: Mapped[JsonList] = mapped_column(_JSON, nullable=False, default=list)
    policy_context_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    frozen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)

    principal: Mapped[WalletPrincipal] = relationship(back_populates="sessions")
    device: Mapped[WalletDevice] = relationship(back_populates="sessions")
    nonces: Mapped[list[WalletSessionNonce]] = relationship(back_populates="session")


class WalletSessionNonce(Base):
    __tablename__ = "wallet_session_nonces"
    __table_args__ = (
        UniqueConstraint("session_hash", "nonce_hash", name="uq_wallet_session_nonces_session_nonce"),
        Index("ix_wallet_session_nonces_used", "session_hash", "used_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("wallet_sessions.id"), nullable=False, index=True)
    session_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    nonce_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    request_digest_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)

    session: Mapped[WalletSession] = relationship(back_populates="nonces")


class WalletStepUpProof(Base):
    __tablename__ = "wallet_step_up_proofs"
    __table_args__ = (Index("ix_wallet_step_up_principal_action", "principal_hash", "action"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    principal_id: Mapped[int] = mapped_column(ForeignKey("wallet_principals.id"), nullable=False, index=True)
    principal_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    device_id: Mapped[int | None] = mapped_column(ForeignKey("wallet_devices.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    proof_type: Mapped[str] = mapped_column(String(60), nullable=False)
    proof_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    intent_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    policy_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    verification_strength: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True, default="created")
    issued_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)

    principal: Mapped[WalletPrincipal] = relationship(back_populates="step_up_proofs")
    device: Mapped[WalletDevice | None] = relationship(back_populates="step_up_proofs")


class RecoveryCapsule(Base):
    __tablename__ = "recovery_capsules"
    __table_args__ = (UniqueConstraint("capsule_hash", name="uq_recovery_capsules_capsule_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    principal_id: Mapped[int] = mapped_column(ForeignKey("wallet_principals.id"), nullable=False, index=True)
    principal_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    capsule_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    recovery_profile: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True, default="created")
    required_factors_json: Mapped[JsonList] = mapped_column(_JSON, nullable=False, default=list)
    completed_factors_json: Mapped[JsonList] = mapped_column(_JSON, nullable=False, default=list)
    cooldown_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    policy_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    transparency_checkpoint_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    issuer_envelope_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)
    issuer_envelope_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    signature_requirement_policy: Mapped[str | None] = mapped_column(String(60), nullable=True)
    crypto_assurance: Mapped[str | None] = mapped_column(String(40), nullable=True)
    requires_reissue: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)

    principal: Mapped[WalletPrincipal] = relationship(back_populates="recovery_capsules")


class MultiWalletQuorum(Base):
    __tablename__ = "multi_wallet_quorums"
    __table_args__ = (UniqueConstraint("quorum_hash", name="uq_multi_wallet_quorums_quorum_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    principal_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    quorum_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    quorum_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    threshold_required: Mapped[int] = mapped_column(Integer, nullable=False)
    participant_count: Mapped[int] = mapped_column(Integer, nullable=False)
    participant_hashes_json: Mapped[JsonList] = mapped_column(_JSON, nullable=False, default=list)
    allowed_proof_types_json: Mapped[JsonList] = mapped_column(_JSON, nullable=False, default=list)
    role_constraints_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True, default="active")
    policy_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)


class WalletPrivacyCommitment(Base):
    __tablename__ = "wallet_privacy_commitments"
    __table_args__ = (
        Index("ix_wallet_privacy_context_pseudonym", "product_context", "pseudonym_hash"),
        UniqueConstraint("commitment_hash", name="uq_wallet_privacy_commitments_commitment_hash"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    principal_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    product_context: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    pseudonym_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    commitment_type: Mapped[str] = mapped_column(String(80), nullable=False)
    commitment_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    retention_policy: Mapped[str | None] = mapped_column(String(120), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)


class WalletAuthChallenge(Base):
    __tablename__ = "wallet_auth_challenges"
    __table_args__ = (
        UniqueConstraint("challenge_id", name="uq_wallet_auth_challenges_challenge_id"),
        UniqueConstraint("challenge_hash", name="uq_wallet_auth_challenges_challenge_hash"),
        Index("ix_wallet_auth_challenges_status_expiry", "status", "expires_at"),
        Index("ix_wallet_auth_challenges_context", "purpose", "network", "origin_hash"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    challenge_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    challenge_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    nonce_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    intent_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    network: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    proof_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    origin: Mapped[str] = mapped_column(String(255), nullable=False)
    origin_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    device_key_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    policy_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    requested_scopes_json: Mapped[JsonList] = mapped_column(_JSON, nullable=False, default=list)
    risk_level: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    principal_hint_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failure_reason_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True, default="pending")
    schema_epoch: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    policy_epoch: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    crypto_epoch: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    intent_json: Mapped[JsonDict] = mapped_column(_JSON, nullable=False, default=dict)
    signable_message_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)
