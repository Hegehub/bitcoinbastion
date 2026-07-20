import pytest

from app.services.access.crypto.hashing import sha256_prefixed
from app.services.payregister.context_integrity import compute_context_hash, verify_invoice_context_binding, verify_settlement_context_binding
from app.services.payregister.lnurl_context import PayRegisterContextBuildRequest, PayRegisterContextBuilder
from tests.unit.test_payregister_context_builder import role_context


def context():
    return PayRegisterContextBuilder().build_context(PayRegisterContextBuildRequest(role_context=role_context(), terminal_device_fingerprint="sha256:device", amount_msat=2500000))


def test_invoice_settlement_must_match_original_context():
    ctx = context()
    ctx_hash = compute_context_hash(ctx)
    verify_invoice_context_binding(context=ctx, context_hash=ctx_hash, metadata_hash=ctx.metadata_hash, amount_msat=ctx.amount_msat, payment_request_id=ctx.context_id, workspace_hash=ctx.workspace_hash, terminal_hash=ctx.terminal_hash, shift_hash=ctx.shift_hash)
    verify_settlement_context_binding(context=ctx, context_hash=ctx_hash, metadata_hash=ctx.metadata_hash, amount_msat=ctx.amount_msat, payment_hash=sha256_prefixed("pay"), expected_payment_hash=sha256_prefixed("pay"))


def test_metadata_amount_terminal_and_shift_mismatch_rejected():
    ctx = context()
    ctx_hash = compute_context_hash(ctx)
    with pytest.raises(Exception):
        verify_invoice_context_binding(context=ctx, context_hash=ctx_hash, metadata_hash="sha256:wrong", amount_msat=ctx.amount_msat, payment_request_id=ctx.context_id, workspace_hash=ctx.workspace_hash, terminal_hash=ctx.terminal_hash, shift_hash=ctx.shift_hash)
    with pytest.raises(Exception):
        verify_invoice_context_binding(context=ctx, context_hash=ctx_hash, metadata_hash=ctx.metadata_hash, amount_msat=1, payment_request_id=ctx.context_id, workspace_hash=ctx.workspace_hash, terminal_hash="hmac:other", shift_hash=ctx.shift_hash)
