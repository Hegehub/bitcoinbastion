from app.domain.lnurl.merchant_addresses import MerchantAddressTargetType, MerchantDomainVerificationMethod
from app.services.lnurl.merchant_address_resolver import MerchantAddressResolver, MerchantAddressResolverConfig
from app.services.lnurl.merchant_address_service import MerchantAddressService
from app.services.lnurl.merchant_domain_service import MerchantDomainService


def test_merchant_address_to_lnurl_pay_response_flow_and_provider_failure_hook():
    domains = MerchantDomainService()
    domain = domains.create_domain(normalized_domain="merchant.com", workspace_id_hash="hmac:workspace", verification_method=MerchantDomainVerificationMethod.BASTION_MANAGED, bastion_managed_domains=frozenset({"merchant.com"}))
    addresses = MerchantAddressService(domain_service=domains)
    address = addresses.create_merchant_address(domain_id=domain.domain_id, local_part="terminal-01", workspace_id_hash="hmac:workspace", target_type=MerchantAddressTargetType.TERMINAL, target_id_hash="hmac:terminal", min_sendable_msat=50_000, max_sendable_msat=50_000, display_label="Coffee Terminal")
    addresses.activate_merchant_address(address.address_id)
    resolver = MerchantAddressResolver(address_service=addresses, config=MerchantAddressResolverConfig(callback_base_url="https://merchant.com", allowed_hosts=frozenset({"merchant.com"})))
    result = resolver.resolve_host_local_part(host="merchant.com", local_part="terminal-01")
    response = result.to_lnurl_response()
    assert response["tag"] == "payRequest"
    assert response["callback"].startswith("https://merchant.com/")
    assert response["minSendable"] == response["maxSendable"] == 50_000
    assert result.metadata_hash.startswith("sha256:")
    assert domains.audit.events[-1]["event_type"] == "merchant_ln_address_resolved"
