from __future__ import annotations

import json

from app.services.lnurl.product_addresses import ProductLightningAddressRegistry


def test_product_metadata_is_canonical_and_contains_identifier() -> None:
    product = ProductLightningAddressRegistry.load_default().resolve_product_lightning_address("pro")
    first = product.metadata_result()
    second = product.metadata_result()
    assert first.metadata == second.metadata
    assert first.metadata_hash == second.metadata_hash
    entries = json.loads(first.metadata)
    assert entries[0][0] == "text/plain"
    assert entries[1][0] == "text/long-desc"
    assert entries[2] == ["text/identifier", "pro@bitcoin-bastion.com"]
    assert "session" not in first.metadata.lower()
    assert "principal" not in first.metadata.lower()


def test_payerdata_and_comment_defaults_are_privacy_preserving() -> None:
    product = ProductLightningAddressRegistry.load_default().resolve_product_lightning_address("basic")
    declaration = product.payer_data_declaration()
    assert declaration == {"auth": {"mandatory": False}}
    assert product.payer_data_policy["email"] == "disabled"
    assert product.payer_data_policy["name"] == "disabled"
    assert product.comment_allowed == 0
