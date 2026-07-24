import json

from app.services.payregister.lnurl.metadata import build_payregister_lnurl_metadata


def test_payregister_metadata_is_canonical_and_stable():
    first = build_payregister_lnurl_metadata(merchant_display_name="Coffee Shop", order_reference="A-100", terminal_reference="counter", description="Latte", lightning_identifier="counter@payregister.bitcoin-bastion.com")
    second = build_payregister_lnurl_metadata(merchant_display_name="Coffee Shop", order_reference="A-100", terminal_reference="counter", description="Latte", lightning_identifier="counter@payregister.bitcoin-bastion.com")
    assert first.canonical_json == second.canonical_json
    assert first.metadata_hash == second.metadata_hash
    metadata = json.loads(first.canonical_json)
    assert ["text/plain", "Payment to Coffee Shop — Order A-100"] in metadata
    assert ["text/identifier", "counter@payregister.bitcoin-bastion.com"] in metadata


def test_metadata_rejects_secret_patterns():
    try:
        build_payregister_lnurl_metadata(merchant_display_name="Coffee Shop", order_reference="A-100", terminal_reference="counter", description="session_token=secret")
    except Exception as exc:
        assert exc.__class__.__name__ in {"UnsafeMetadataContentError", "LNURLMetadataError"}
    else:  # pragma: no cover
        raise AssertionError("secret-bearing metadata accepted")
