
from app.domain.lnurl.merchant_addresses import MerchantAddressTargetType, MerchantDomainVerificationMethod
from app.services.lnurl.merchant_address_service import MerchantAddressService
from app.services.lnurl.merchant_domain_service import MerchantDomainService
from app.services.lnurl.merchant_metadata import build_merchant_metadata


def test_merchant_metadata_deterministic_and_private():
    domains = MerchantDomainService()
    domain = domains.create_domain(normalized_domain="merchant.com", workspace_id_hash="hmac:workspace", verification_method=MerchantDomainVerificationMethod.BASTION_MANAGED, bastion_managed_domains=frozenset({"merchant.com"}))
    svc = MerchantAddressService(domain_service=domains)
    address = svc.create_merchant_address(domain_id=domain.domain_id, local_part="coffee", workspace_id_hash="hmac:workspace", target_type=MerchantAddressTargetType.STORE, target_id_hash="hmac:store", display_label="Coffee Bastion", description="PayRegister payment for Store Amsterdam #1")
    first = build_merchant_metadata(address)
    second = build_merchant_metadata(address)
    assert first.canonical_json == second.canonical_json
    assert "hmac:store" not in first.canonical_json
    assert "principal_hash" not in first.canonical_json
