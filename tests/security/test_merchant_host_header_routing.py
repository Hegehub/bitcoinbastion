import pytest

from tests.unit.test_merchant_address_resolver import active_resolver


def test_host_header_injection_and_untrusted_forwarded_host_do_not_resolve():
    resolver = active_resolver()
    with pytest.raises(Exception):
        resolver.resolve_host_local_part(host="merchant.com,attacker.example", local_part="coffee")
    with pytest.raises(Exception):
        resolver.resolve_host_local_part(host="attacker.example", local_part="coffee")
