import pytest

from app.domain.lnurl.merchant_addresses import MerchantAddressTargetType, MerchantDomainVerificationMethod
from app.services.lnurl.merchant_address_service import MerchantAddressService
from app.services.lnurl.merchant_domain_service import MerchantDomainService


def test_cross_workspace_address_binding_denied():
    domains = MerchantDomainService()
    domain = domains.create_domain(normalized_domain="merchant.com", workspace_id_hash="hmac:workspace-a", verification_method=MerchantDomainVerificationMethod.BASTION_MANAGED, bastion_managed_domains=frozenset({"merchant.com"}))
    svc = MerchantAddressService(domain_service=domains)
    with pytest.raises(Exception):
        svc.create_merchant_address(domain_id=domain.domain_id, local_part="store", workspace_id_hash="hmac:workspace-b", target_type=MerchantAddressTargetType.STORE, target_id_hash="hmac:store-b")
