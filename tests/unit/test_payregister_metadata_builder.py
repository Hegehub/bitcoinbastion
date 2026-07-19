
from app.domain.payregister_lnurl.roles import PayRegisterActorType, PayRegisterCashierRole
from app.services.payregister.lnurl_context import PayRegisterContextBuildRequest, build_wallet_visible_payregister_metadata, compute_payregister_metadata_hash
from app.services.payregister.role_binding_service import PayRegisterResolvedRoleContext


def role_context():
    return PayRegisterResolvedRoleContext(True, PayRegisterActorType.CASHIER, PayRegisterCashierRole.CASHIER, "hmac:workspace", "hmac:store", "hmac:terminal", "hmac:shift", "hmac:role", frozenset({"payregister:payment:create"}), frozenset({"payregister:refund:approve"}), "sha256:policy")


def test_wallet_visible_metadata_contains_no_private_cashier_data():
    request = PayRegisterContextBuildRequest(role_context=role_context(), terminal_device_fingerprint="sha256:device", amount_msat=1000, order_reference="9231", store_display_name="Store 12", terminal_display_name="Terminal 3", receipt_operator_label="Counter A", public_lightning_identifier="store-12@payregister.bitcoin-bastion.com")
    metadata = build_wallet_visible_payregister_metadata(request)
    dumped = str(metadata).lower()
    assert ["text/plain", "Payment to Store 12"] in metadata
    assert "cashier" not in dumped
    assert "principal" not in dumped
    assert "hmac-sha256" not in dumped
    assert compute_payregister_metadata_hash(metadata).startswith("sha256:")


def test_private_operator_labels_are_sanitized():
    request = PayRegisterContextBuildRequest(role_context=role_context(), terminal_device_fingerprint="sha256:device", amount_msat=1000, receipt_operator_label="alice@example.com", public_lightning_identifier="store@payregister.bitcoin-bastion.com")
    metadata = build_wallet_visible_payregister_metadata(request)
    assert "alice@example.com" not in str(metadata)
