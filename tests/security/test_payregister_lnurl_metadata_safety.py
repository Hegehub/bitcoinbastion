
from app.services.payregister.lnurl_context import PayRegisterContextBuildRequest, build_wallet_visible_payregister_metadata
from tests.unit.test_payregister_metadata_builder import role_context


def test_metadata_rejects_or_sanitizes_html_and_secrets():
    request = PayRegisterContextBuildRequest(role_context=role_context(), terminal_device_fingerprint="sha256:device", amount_msat=1000, store_display_name="<script>alert(1)</script>", terminal_display_name="Terminal 3", receipt_operator_label="principal_hash:abc", public_lightning_identifier="store@payregister.bitcoin-bastion.com")
    metadata = build_wallet_visible_payregister_metadata(request)
    dumped = str(metadata).lower()
    assert "<script>" not in dumped
    assert "principal_hash" not in dumped


def test_no_seed_or_private_key_inputs_exist_in_context_request():
    fields = PayRegisterContextBuildRequest.__dataclass_fields__
    assert "seed" not in fields
    assert "private_key" not in fields
    assert "wallet_address" not in fields
