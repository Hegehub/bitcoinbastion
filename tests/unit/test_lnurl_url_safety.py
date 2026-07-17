import pytest

from app.services.lnurl.errors import (
    LNURLAuthDomainMismatchError,
    LNURLCredentialsForbiddenError,
    LNURLFragmentForbiddenError,
    LNURLInvalidHostError,
    LNURLOnionValidationError,
    LNURLPortForbiddenError,
    LNURLPrivateTargetError,
    LNURLRedirectForbiddenError,
    LNURLUnsafeURLError,
    LNURLUnsupportedSchemeError,
)
from app.services.lnurl.redaction import redact_lnurl_url
from app.services.lnurl.url_safety import LNURLURLPolicy, hostname_matches_allowlist, validate_lnurl_redirect, validate_lnurl_url

ONION = "a" * 56 + ".onion"


def test_https_public_domain_accepted_and_http_rejected() -> None:
    result = validate_lnurl_url("https://example.com/cb?token=secret", policy=LNURLURLPolicy.remote_fetch())
    assert result.ascii_hostname == "example.com"
    assert result.query == "token=secret"
    assert "secret" not in repr(result)
    with pytest.raises(LNURLUnsupportedSchemeError):
        validate_lnurl_url("http://example.com/cb", policy=LNURLURLPolicy.remote_fetch())


def test_onion_http_requires_onion_policy_and_v3_hostname() -> None:
    assert validate_lnurl_url(f"http://{ONION}/cb", policy=LNURLURLPolicy.onion()).is_onion is True
    with pytest.raises((LNURLOnionValidationError, LNURLUnsupportedSchemeError)):
        validate_lnurl_url(f"http://{ONION}/cb", policy=LNURLURLPolicy.remote_fetch())
    with pytest.raises(LNURLOnionValidationError):
        validate_lnurl_url("http://abcdefghijklmnop.onion/cb", policy=LNURLURLPolicy.onion())


@pytest.mark.parametrize("url,exc", [
    ("https:///cb", LNURLUnsafeURLError),
    ("/relative", LNURLUnsafeURLError),
    ("https://user:pass@example.com/cb", LNURLCredentialsForbiddenError),
    ("https://example.com/cb#frag", LNURLFragmentForbiddenError),
    ("https://example.com:bad/cb", LNURLPortForbiddenError),
    ("https://example.com:0/cb", LNURLPortForbiddenError),
    ("https://example.com:8443/cb", LNURLPortForbiddenError),
    ("https://example.com/%0d%0aInjected", LNURLUnsafeURLError),
    ("https://example.com/\\evil", LNURLUnsafeURLError),
])
def test_malformed_urls_rejected(url: str, exc: type[Exception]) -> None:
    with pytest.raises(exc):
        validate_lnurl_url(url, policy=LNURLURLPolicy.remote_fetch())


@pytest.mark.parametrize("url", ["https://127.0.0.1/cb", "https://localhost/cb", "https://10.0.0.1/cb", "https://[::1]/cb", "https://[fe80::1]/cb", "https://[::ffff:192.168.1.1]/cb"])
def test_loopback_private_and_link_local_rejected_by_production(url: str) -> None:
    with pytest.raises((LNURLPrivateTargetError, LNURLInvalidHostError)):
        validate_lnurl_url(url, policy=LNURLURLPolicy.remote_fetch())


def test_development_policy_allows_localhost_and_configured_ports() -> None:
    result = validate_lnurl_url("http://localhost:8000/cb", policy=LNURLURLPolicy.development(ports=(8000,)))
    assert result.hostname == "localhost"


def test_idna_and_allowlist_are_exact_not_suffix_based() -> None:
    assert validate_lnurl_url("https://bücher.example/cb", policy=LNURLURLPolicy.remote_fetch()).ascii_hostname == "xn--bcher-kva.example"
    assert hostname_matches_allowlist("bitcoin-bastion.com", ["bitcoin-bastion.com"])
    assert not hostname_matches_allowlist("evil-bitcoin-bastion.com", ["bitcoin-bastion.com"])
    assert not hostname_matches_allowlist("bitcoin-bastion.com.attacker.example", ["bitcoin-bastion.com"])
    policy = LNURLURLPolicy.service_owned_auth(domains=["auth.bitcoin-bastion.com"], stable_domain="auth.bitcoin-bastion.com")
    validate_lnurl_url("https://auth.bitcoin-bastion.com/cb", policy=policy)
    with pytest.raises(LNURLAuthDomainMismatchError):
        validate_lnurl_url("https://other.bitcoin-bastion.com/cb", policy=policy)


def test_redirect_revalidation_blocks_private_and_https_downgrade() -> None:
    source = validate_lnurl_url("https://example.com/cb", policy=LNURLURLPolicy.remote_fetch())
    with pytest.raises(LNURLRedirectForbiddenError):
        validate_lnurl_redirect(source, "https://169.254.169.254/latest", policy=LNURLURLPolicy.remote_fetch())
    with pytest.raises(LNURLRedirectForbiddenError):
        validate_lnurl_redirect(source, "http://example.com/cb", policy=LNURLURLPolicy.remote_fetch())


def test_redaction_preserves_shape_but_not_values() -> None:
    redacted = redact_lnurl_url("https://auth.example/cb?k1=raw-k1&sig=raw-sig&tag=login")
    assert "k1=%5BREDACTED%5D" in redacted
    assert "raw-k1" not in redacted and "raw-sig" not in redacted
