"""PayRegister context and settlement integrity checks."""
from __future__ import annotations

from app.domain.payregister_lnurl.contexts import PayRegisterCanonicalContext
from app.domain.payregister_lnurl.errors import PayRegisterIntegrityError
from app.services.access.crypto.hashing import sha256_prefixed
from app.services.payregister.lnurl_context import canonicalize_payregister_context


def compute_context_hash(context: PayRegisterCanonicalContext) -> str:
    return sha256_prefixed(canonicalize_payregister_context(context))


def verify_context_hash(context: PayRegisterCanonicalContext, expected_hash: str) -> bool:
    return compute_context_hash(context) == expected_hash


def verify_invoice_context_binding(*, context: PayRegisterCanonicalContext, context_hash: str, metadata_hash: str, amount_msat: int, payment_request_id: str, workspace_hash: str, terminal_hash: str, shift_hash: str) -> None:
    if not verify_context_hash(context, context_hash):
        raise PayRegisterIntegrityError("Context hash mismatch")
    if context.metadata_hash != metadata_hash or context.amount_msat != amount_msat:
        raise PayRegisterIntegrityError("Invoice metadata or amount mismatch")
    if context.workspace_hash != workspace_hash or context.terminal_hash != terminal_hash or context.shift_hash != shift_hash:
        raise PayRegisterIntegrityError("Invoice context scope mismatch")
    if not payment_request_id.startswith("prctx_"):
        raise PayRegisterIntegrityError("Unexpected payment request reference")


def verify_settlement_context_binding(*, context: PayRegisterCanonicalContext, context_hash: str, metadata_hash: str, amount_msat: int, payment_hash: str, expected_payment_hash: str) -> None:
    if not verify_context_hash(context, context_hash):
        raise PayRegisterIntegrityError("Settlement context hash mismatch")
    if context.metadata_hash != metadata_hash or context.amount_msat != amount_msat:
        raise PayRegisterIntegrityError("Settlement amount or metadata mismatch")
    if payment_hash != expected_payment_hash:
        raise PayRegisterIntegrityError("Settlement payment hash mismatch")
