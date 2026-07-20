import pytest

from app.domain.lnurl.merchant_addresses import normalize_merchant_domain, normalize_merchant_local_part


def test_domain_and_local_part_normalization():
    assert normalize_merchant_domain("Merchant.COM.") == "merchant.com"
    assert normalize_merchant_local_part("Coffee-01") == "coffee-01"


def test_malformed_domain_and_reserved_alias_fail():
    with pytest.raises(Exception):
        normalize_merchant_domain("http://merchant.com/path")
    with pytest.raises(Exception):
        normalize_merchant_domain("localhost")
    with pytest.raises(Exception):
        normalize_merchant_local_part("admin")
    with pytest.raises(Exception):
        normalize_merchant_local_part("../coffee")
