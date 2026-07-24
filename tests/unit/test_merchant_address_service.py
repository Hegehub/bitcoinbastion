import pytest

from app.domain.lnurl.merchant_addresses import MerchantAddressTargetType, MerchantDomainVerificationMethod
from app.services.lnurl.merchant_address_service import MerchantAddressService
from app.services.lnurl.merchant_domain_service import MerchantDomainService


def setup_services():
    domains = MerchantDomainService()
    address_service = MerchantAddressService(domain_service=domains)
    domain = domains.create_domain(normalized_domain="payregister.bitcoin-bastion.com", workspace_id_hash="hmac:workspace", verification_method=MerchantDomainVerificationMethod.BASTION_MANAGED, bastion_managed_domains=frozenset({"payregister.bitcoin-bastion.com"}))
    return domains, address_service, domain


def test_create_activate_suspend_revoke_address():
    _domains, svc, domain = setup_services()
    address = svc.create_merchant_address(domain_id=domain.domain_id, local_part="store-123", workspace_id_hash="hmac:workspace", target_type=MerchantAddressTargetType.STORE, target_id_hash="hmac:store")
    assert address.status == "pending"
    assert svc.activate_merchant_address(address.address_id).status == "active"
    assert svc.suspend_merchant_address(address.address_id).status == "suspended"
    assert svc.revoke_merchant_address(address.address_id).status == "revoked"


def test_unverified_domain_duplicate_and_cross_workspace_fail():
    domains = MerchantDomainService()
    domain = domains.create_domain(normalized_domain="merchant.com", workspace_id_hash="hmac:workspace", verification_method=MerchantDomainVerificationMethod.DNS_TXT)
    svc = MerchantAddressService(domain_service=domains)
    with pytest.raises(Exception):
        svc.create_merchant_address(domain_id=domain.domain_id, local_part="coffee", workspace_id_hash="hmac:workspace", target_type=MerchantAddressTargetType.STORE, target_id_hash="hmac:store")
    domains.mark_verified(domain.domain_id)
    with pytest.raises(Exception):
        svc.create_merchant_address(domain_id=domain.domain_id, local_part="coffee", workspace_id_hash="hmac:other", target_type=MerchantAddressTargetType.STORE, target_id_hash="hmac:store")
