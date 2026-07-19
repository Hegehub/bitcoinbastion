import json
import pytest

from app.domain.lnurl.merchant_addresses import MerchantAddressTargetType, MerchantDomainVerificationMethod
from app.services.lnurl.merchant_address_resolver import MerchantAddressResolutionError, MerchantAddressResolver, MerchantAddressResolverConfig
from app.services.lnurl.merchant_address_service import MerchantAddressService
from app.services.lnurl.merchant_domain_service import MerchantDomainService


def active_resolver():
    domains = MerchantDomainService()
    address_service = MerchantAddressService(domain_service=domains)
    domain = domains.create_domain(normalized_domain="merchant.com", workspace_id_hash="hmac:workspace", verification_method=MerchantDomainVerificationMethod.BASTION_MANAGED, bastion_managed_domains=frozenset({"merchant.com"}))
    address = address_service.create_merchant_address(domain_id=domain.domain_id, local_part="coffee", workspace_id_hash="hmac:workspace", target_type=MerchantAddressTargetType.STORE, target_id_hash="hmac:store", min_sendable_msat=1000, max_sendable_msat=2000, display_label="Coffee Bastion")
    address_service.activate_merchant_address(address.address_id)
    return MerchantAddressResolver(address_service=address_service, config=MerchantAddressResolverConfig(callback_base_url="https://merchant.com", allowed_hosts=frozenset({"merchant.com"})))


def test_active_verified_address_resolves_to_pay_request():
    result = active_resolver().resolve_host_local_part(host="merchant.com", local_part="coffee")
    response = result.to_lnurl_response()
    assert response["tag"] == "payRequest"
    assert response["minSendable"] == 1000
    assert response["maxSendable"] == 2000
    metadata = json.loads(response["metadata"])
    assert any(item[0] == "text/identifier" and item[1] == "coffee@merchant.com" for item in metadata)
    assert response["callback"].startswith("https://merchant.com/")


def test_unknown_host_and_alias_fail_without_tenant_fallback():
    resolver = active_resolver()
    with pytest.raises(MerchantAddressResolutionError):
        resolver.resolve_host_local_part(host="attacker.example", local_part="coffee")
    with pytest.raises(MerchantAddressResolutionError):
        resolver.resolve_host_local_part(host="merchant.com", local_part="unknown")
