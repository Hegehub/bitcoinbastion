from app.domain.payregister_lnurl.roles import PayRegisterActorType, PayRegisterCashierRole
from app.services.payregister.context_integrity import compute_context_hash, verify_context_hash
from app.services.payregister.lnurl_context import PayRegisterContextBuildRequest, PayRegisterContextBuilder, canonicalize_payregister_context
from app.services.payregister.role_binding_service import PayRegisterResolvedRoleContext


def role_context():
    return PayRegisterResolvedRoleContext(True, PayRegisterActorType.CASHIER, PayRegisterCashierRole.CASHIER, "hmac:workspace", "hmac:store", "hmac:terminal", "hmac:shift", "hmac:role", frozenset({"payregister:payment:create"}), frozenset({"payregister:refund:approve"}), "sha256:policy")


def test_canonical_context_uses_hashes_and_is_stable_for_integrity():
    context = PayRegisterContextBuilder().build_context(PayRegisterContextBuildRequest(role_context=role_context(), terminal_device_fingerprint="sha256:device", amount_msat=2500000, order_reference="9231", merchant_invoice_reference="inv-9231", store_display_name="Store 12", terminal_display_name="Terminal 3", public_lightning_identifier="store-12@payregister.bitcoin-bastion.com"))
    canonical = canonicalize_payregister_context(context)
    assert "cashier@example" not in canonical
    assert "9231" not in canonical
    context_hash = compute_context_hash(context)
    assert verify_context_hash(context, context_hash)
    assert context.metadata_hash.startswith("sha256:")
