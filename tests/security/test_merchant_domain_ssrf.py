import pytest

from app.domain.lnurl.merchant_addresses import MerchantDomainInvalidError
from app.services.lnurl.merchant_domain_verification import MerchantDomainVerificationService


class RedirectHTTP:
    def __init__(self, final): self.final = final
    def get_text(self, url, *, max_redirects, max_bytes): return self.final, "token"


def test_http_redirect_to_private_ip_or_cross_domain_fails():
    svc = MerchantDomainVerificationService()
    with pytest.raises(MerchantDomainInvalidError):
        svc.verify_http_well_known(domain="merchant.com", expected_token="token", http_client=RedirectHTTP("https://127.0.0.1/.well-known/bastion-lnurl-verification"))
    with pytest.raises(MerchantDomainInvalidError):
        svc.verify_http_well_known(domain="merchant.com", expected_token="token", http_client=RedirectHTTP("https://attacker.example/.well-known/bastion-lnurl-verification"))


def test_localhost_domain_fails_before_http_request():
    with pytest.raises(Exception):
        MerchantDomainVerificationService().verify_http_well_known(domain="localhost", expected_token="token", http_client=RedirectHTTP("https://localhost/.well-known/bastion-lnurl-verification"))
