"""SQLAlchemy models for the Bastion LNURL Layer.

Model definitions only. These models use hash-first storage for k1 values,
linking keys, invoices, callbacks, payment identifiers, receipt packets, and
payer data. They intentionally avoid raw wallet secrets and bearer-token style
access material.
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


class LNURLAuthChallenge(Base):
    __tablename__ = "lnurl_auth_challenges"
    __table_args__ = (
        UniqueConstraint("k1_hash", name="uq_lnurl_auth_challenges_k1_hash"),
        Index("ix_lnurl_auth_challenges_domain_action", "auth_domain", "action"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    challenge_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    k1_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    action: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    internal_action: Mapped[str | None] = mapped_column(String(120), nullable=True)
    auth_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    callback_url_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    principal_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    device_key_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    policy_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True, default="created")
    issued_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)

    attempts: Mapped[list[LNURLAuthAttempt]] = relationship(back_populates="challenge")


class LNURLAuthAttempt(Base):
    __tablename__ = "lnurl_auth_attempts"
    __table_args__ = (Index("ix_lnurl_auth_attempts_key_status", "key_hash", "verification_status"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    challenge_id: Mapped[int | None] = mapped_column(ForeignKey("lnurl_auth_challenges.id"), nullable=True, index=True)
    k1_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    sig_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    auth_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    verification_status: Mapped[str] = mapped_column(String(40), nullable=False, index=True, default="callback_received")
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    principal_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, index=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)

    challenge: Mapped[LNURLAuthChallenge | None] = relationship(back_populates="attempts")


class LNURLPrincipal(Base):
    __tablename__ = "lightning_principals"
    __table_args__ = (
        UniqueConstraint("auth_domain", "lnurl_key_hash", name="uq_lightning_principals_domain_key"),
        UniqueConstraint("principal_hash", name="uq_lightning_principals_principal_hash"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    principal_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    lnurl_key_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    auth_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    linking_key_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    verification_strength: Mapped[str] = mapped_column(String(40), nullable=False, default="standard")
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)


class LNURLPayRequest(Base):
    __tablename__ = "lnurl_pay_requests"
    __table_args__ = (UniqueConstraint("payment_id_hash", name="uq_lnurl_pay_requests_payment_id_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_id_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    principal_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    product_code: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    plan_code: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    amount_msat: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_sendable_msat: Mapped[int] = mapped_column(Integer, nullable=False)
    max_sendable_msat: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    callback_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    lightning_address: Mapped[str | None] = mapped_column(String(320), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True, default="created")
    issued_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)

    invoices: Mapped[list[LNURLInvoice]] = relationship(back_populates="payment_request")


class LNURLInvoice(Base):
    __tablename__ = "lnurl_invoices"
    __table_args__ = (UniqueConstraint("invoice_hash", name="uq_lnurl_invoices_invoice_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_request_id: Mapped[int] = mapped_column(ForeignKey("lnurl_pay_requests.id"), nullable=False, index=True)
    payment_id_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    invoice_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    payment_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    amount_msat: Mapped[int] = mapped_column(Integer, nullable=False)
    description_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True, default="invoice_issued")
    verify_url_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    settled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)

    payment_request: Mapped[LNURLPayRequest] = relationship(back_populates="invoices")


class LNURLPaymentProof(Base):
    __tablename__ = "lnurl_payment_proofs"
    __table_args__ = (UniqueConstraint("payment_id_hash", "invoice_hash", name="uq_lnurl_payment_proofs_payment_invoice"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_id_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    invoice_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    payment_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    preimage_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    principal_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    plan_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    amount_msat: Mapped[int] = mapped_column(Integer, nullable=False)
    settled: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True, default=False)
    settled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    verify_method: Mapped[str] = mapped_column(String(80), nullable=False)
    audit_event_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    issuer_signature_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    issuer_envelope_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)
    issuer_envelope_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    signature_requirement_policy: Mapped[str | None] = mapped_column(String(60), nullable=True)
    crypto_assurance: Mapped[str | None] = mapped_column(String(40), nullable=True)
    requires_reissue: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)


class LNURLVerifyCheck(Base):
    __tablename__ = "lnurl_verify_checks"
    __table_args__ = (Index("ix_lnurl_verify_payment_checked", "payment_id_hash", "checked_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_id_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    invoice_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    verify_url_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    settled: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True, default=False)
    response_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)


class LNURLWithdrawRequest(Base):
    __tablename__ = "lnurl_withdraw_requests"
    __table_args__ = (
        UniqueConstraint("withdraw_id_hash", name="uq_lnurl_withdraw_requests_withdraw_id_hash"),
        UniqueConstraint("k1_hash", name="uq_lnurl_withdraw_requests_k1_hash"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    withdraw_id_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    principal_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    k1_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    callback_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    min_withdrawable_msat: Mapped[int] = mapped_column(Integer, nullable=False)
    max_withdrawable_msat: Mapped[int] = mapped_column(Integer, nullable=False)
    default_description_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    withdraw_method: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True, default="created")
    policy_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)

    attempts: Mapped[list[LNURLWithdrawAttempt]] = relationship(back_populates="withdraw_request")


class LNURLWithdrawAttempt(Base):
    __tablename__ = "lnurl_withdraw_attempts"
    __table_args__ = (Index("ix_lnurl_withdraw_attempts_k1_status", "k1_hash", "attempt_status"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    withdraw_request_id: Mapped[int] = mapped_column(ForeignKey("lnurl_withdraw_requests.id"), nullable=False, index=True)
    withdraw_id_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    k1_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    invoice_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    amount_msat: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attempt_status: Mapped[str] = mapped_column(String(40), nullable=False, index=True, default="invoice_received")
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)

    withdraw_request: Mapped[LNURLWithdrawRequest] = relationship(back_populates="attempts")


class LNURLSuccessAction(Base):
    __tablename__ = "lnurl_success_actions"
    __table_args__ = (Index("ix_lnurl_success_actions_activation", "activation_ref_hash", "expires_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_id_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    description_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    url_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    activation_ref_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)


class LNURLPayerData(Base):
    __tablename__ = "lnurl_payer_data"
    __table_args__ = (Index("ix_lnurl_payer_data_payment_principal", "payment_id_hash", "principal_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_id_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    principal_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    payerdata_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    fields_json: Mapped[JsonDict] = mapped_column(_JSON, nullable=False, default=dict)
    auth_k1_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    pubkey_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    identifier_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    email_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    name_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    retention_policy: Mapped[str | None] = mapped_column(String(120), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)


class LightningAddress(Base):
    __tablename__ = "lightning_addresses"
    __table_args__ = (
        UniqueConstraint("domain", "name_hash", name="uq_lightning_addresses_domain_name_hash"),
        Index("ix_lightning_addresses_domain_status", "domain", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    address_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    product_code: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    principal_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    payregister_store_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    terminal_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True, default="active")
    metadata_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)


class LNURLReceiptPacket(Base):
    __tablename__ = "lnurl_receipt_packets"
    __table_args__ = (UniqueConstraint("receipt_hash", name="uq_lnurl_receipt_packets_receipt_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    receipt_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    payment_id_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    invoice_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    metadata_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    entitlement_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    audit_event_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    principal_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    payregister_context_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)


class PayRegisterLNURLBinding(Base):
    __tablename__ = "payregister_lnurl_terminals"
    __table_args__ = (UniqueConstraint("binding_hash", name="uq_payregister_lnurl_terminals_terminal_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    binding_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    store_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    terminal_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    cashier_shift_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    principal_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    lightning_address_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True, default="active")
    policy_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    metadata_json: Mapped[JsonDict | None] = mapped_column(_JSON, nullable=True)
