from datetime import UTC, datetime, timedelta

from app.domain.lnurl.merchant_addresses import MerchantDomainVerificationMethod
from app.services.lnurl.merchant_domain_verification import MerchantDomainVerificationService


class DNS:
    def __init__(self, records): self.records = records
    def txt_records(self, name): return self.records


class HTTP:
    def __init__(self, final_url, body): self.final_url, self.body = final_url, body
    def get_text(self, url, *, max_redirects, max_bytes): return self.final_url, self.body


def test_valid_dns_txt_proof_succeeds_and_invalid_or_expired_fails():
    svc = MerchantDomainVerificationService()
    challenge = svc.create_challenge("merchant.com", MerchantDomainVerificationMethod.DNS_TXT)
    assert svc.verify_dns_txt(domain="merchant.com", expected_token=challenge.token, resolver=DNS((challenge.expected_value,)))
    assert not svc.verify_dns_txt(domain="merchant.com", expected_token="wrong", resolver=DNS((challenge.expected_value,)))
    assert not svc.verify_dns_txt(domain="merchant.com", expected_token=challenge.token, resolver=DNS((challenge.expected_value,)), now=datetime.now(UTC), expires_at=datetime.now(UTC) - timedelta(seconds=1))


def test_http_well_known_proof_succeeds():
    svc = MerchantDomainVerificationService()
    assert svc.verify_http_well_known(domain="merchant.com", expected_token="abc", http_client=HTTP("https://merchant.com/.well-known/bastion-lnurl-verification", "bastion-lnurl-verification=abc"))
