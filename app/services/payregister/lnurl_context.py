"""Canonical PayRegister cashier/shift LNURL context builder."""
from __future__ import annotations

import html
import re
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from app.domain.payregister_lnurl.contexts import PayRegisterCanonicalContext
from app.domain.payregister_lnurl.errors import PayRegisterPolicyDeniedError
from app.services.access.crypto.hashing import canonical_json, hash_canonical_json_prefixed, hmac_sha256_prefixed, sha256_prefixed
from app.services.lnurl.pay_metadata import LNURLPayMetadataBuilder
from app.services.payregister.role_binding_service import PayRegisterResolvedRoleContext

_FORBIDDEN_VISIBLE = ("cashier", "principal_hash", "session", "access_pass", "private_key", "seed", "wallet", "role_binding", "hmac-sha256")
_SAFE_LABEL_RE = re.compile(r"^[A-Za-z0-9 ._#-]{1,64}$")


@dataclass(frozen=True, slots=True)
class PayRegisterContextBuildRequest:
    role_context: PayRegisterResolvedRoleContext
    terminal_device_fingerprint: str
    amount_msat: int
    currency: str = "BTC"
    payment_purpose: str = "merchant_sale"
    order_reference: str | None = None
    merchant_invoice_reference: str | None = None
    store_display_name: str = "PayRegister store"
    terminal_display_name: str = "PayRegister terminal"
    receipt_operator_label: str | None = None
    public_lightning_identifier: str | None = None
    ttl_seconds: int = 600


class PayRegisterContextBuilder:
    def __init__(self, *, pepper: str = "dev-payregister-context-pepper-change-me", clock: Any | None = None) -> None:
        self.pepper = pepper
        self.clock = clock or (lambda: datetime.now(UTC))

    def build_context(self, request: PayRegisterContextBuildRequest) -> PayRegisterCanonicalContext:
        if request.amount_msat <= 0:
            raise PayRegisterPolicyDeniedError("Amount must be positive")
        now = self.clock()
        context_id = f"prctx_{secrets.token_urlsafe(18)}"
        order_hash = hmac_sha256_prefixed(self.pepper, request.order_reference) if request.order_reference else None
        merchant_invoice_hash = sha256_prefixed(request.merchant_invoice_reference) if request.merchant_invoice_reference else None
        metadata = build_wallet_visible_payregister_metadata(request)
        metadata_hash = compute_payregister_metadata_hash(metadata)
        return PayRegisterCanonicalContext(
            context_type="bastion_payregister_payment_context",
            version=1,
            context_id=context_id,
            workspace_hash=request.role_context.workspace_hash,
            store_hash=request.role_context.store_hash,
            terminal_hash=request.role_context.terminal_hash,
            terminal_device_fingerprint=request.terminal_device_fingerprint,
            cashier_role_binding_hash=request.role_context.role_binding_hash,
            shift_hash=request.role_context.shift_hash,
            order_hash=order_hash,
            merchant_invoice_hash=merchant_invoice_hash,
            currency=request.currency,
            amount_msat=request.amount_msat,
            payment_purpose=request.payment_purpose,
            created_at=now,
            expires_at=now + timedelta(seconds=request.ttl_seconds),
            policy_hash=request.role_context.policy_hash,
            metadata_hash=metadata_hash,
        )


def build_wallet_visible_payregister_metadata(request: PayRegisterContextBuildRequest) -> list[list[str]]:
    store = _safe_display(request.store_display_name, fallback="PayRegister store")
    terminal = _safe_display(request.terminal_display_name, fallback="PayRegister terminal")
    order = _safe_public_reference(request.order_reference)
    plain = f"Payment to {store}"
    long_desc = f"{terminal} merchant payment. Receipt available after settlement."
    if order:
        long_desc = f"Order {order}. {long_desc}"
    if request.receipt_operator_label:
        long_desc = f"{long_desc} Served by {_safe_display(request.receipt_operator_label, fallback='shift operator')}."
    identifier = request.public_lightning_identifier or "store@payregister.bitcoin-bastion.com"
    result = LNURLPayMetadataBuilder().build_custom_metadata(plain_text=plain, long_description=long_desc, identifier=identifier)
    metadata = [[entry.mime_type, entry.value] for entry in result.entries]
    dumped = canonical_json(metadata).lower()
    if any(value in dumped for value in _FORBIDDEN_VISIBLE):
        raise PayRegisterPolicyDeniedError("Wallet-visible metadata contains private cashier context")
    return metadata


def compute_payregister_metadata_hash(metadata: list[list[str]]) -> str:
    return hash_canonical_json_prefixed(metadata)


def canonicalize_payregister_context(context: PayRegisterCanonicalContext) -> str:
    return canonical_json(
        {
            "type": context.context_type,
            "version": context.version,
            "context_id": context.context_id,
            "workspace_hash": context.workspace_hash,
            "store_hash": context.store_hash,
            "terminal_hash": context.terminal_hash,
            "terminal_device_fingerprint": context.terminal_device_fingerprint,
            "cashier_role_binding_hash": context.cashier_role_binding_hash,
            "shift_hash": context.shift_hash,
            "order_hash": context.order_hash,
            "merchant_invoice_hash": context.merchant_invoice_hash,
            "currency": context.currency,
            "amount_msat": context.amount_msat,
            "payment_purpose": context.payment_purpose,
            "created_at": context.created_at.isoformat().replace("+00:00", "Z"),
            "expires_at": context.expires_at.isoformat().replace("+00:00", "Z"),
            "policy_hash": context.policy_hash,
            "metadata_hash": context.metadata_hash,
        }
    )


def _safe_display(value: str, *, fallback: str) -> str:
    normalized = html.escape(" ".join(value.split()), quote=True)
    if not normalized or not _SAFE_LABEL_RE.fullmatch(normalized):
        return fallback
    lowered = normalized.lower()
    if any(secret in lowered for secret in ("@", "wallet", "principal", "session", "seed", "private")):
        return fallback
    return normalized


def _safe_public_reference(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = "".join(ch for ch in value if ch.isalnum() or ch in "-_.#")[:40]
    return normalized or None
