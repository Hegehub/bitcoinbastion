from tests.unit.test_payregister_metadata_builder import role_context
from app.services.payregister.lnurl_context import PayRegisterContextBuildRequest, build_wallet_visible_payregister_metadata


def test_wallet_visible_metadata_excludes_private_cashier_and_principal_data():
    request = PayRegisterContextBuildRequest(role_context=role_context(), terminal_device_fingerprint="sha256:device", amount_msat=1000, store_display_name="Store 12", terminal_display_name="Terminal 3", receipt_operator_label="Shift operator", public_lightning_identifier="store-12@payregister.bitcoin-bastion.com")
    dumped = str(build_wallet_visible_payregister_metadata(request)).lower()
    for forbidden in ("cashier email", "principal_hash", "hmac:role", "session", "access_pass", "seed", "private_key"):
        assert forbidden not in dumped
