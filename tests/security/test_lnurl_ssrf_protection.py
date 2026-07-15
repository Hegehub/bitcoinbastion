import asyncio

import pytest

from app.services.lnurl.errors import LNURLDNSResolutionError, LNURLPrivateTargetError, LNURLRedirectForbiddenError
from app.services.lnurl.url_safety import LNURLURLPolicy, resolve_and_validate_lnurl_target, validate_lnurl_redirect, validate_lnurl_url

class Resolver:
    def __init__(self, values=None, error=False):
        self.values = values or []
        self.error = error
        self.calls = 0
    async def resolve(self, hostname: str, port: int):
        self.calls += 1
        if self.error:
            raise RuntimeError("dns down with k1=secret")
        return self.values

def _run(awaitable):
    return asyncio.run(awaitable)

def test_public_dns_result_accepted_and_duplicates_deduplicated() -> None:
    v = validate_lnurl_url("https://example.com/cb?k1=secret", policy=LNURLURLPolicy.remote_fetch())
    resolved = _run(resolve_and_validate_lnurl_target(v, resolver=Resolver(["93.184.216.34", "93.184.216.34"]), policy=LNURLURLPolicy.remote_fetch()))
    assert resolved.addresses == ("93.184.216.34",)
    assert resolved.address_fingerprints[0].startswith("sha256:")

@pytest.mark.parametrize("addresses", [["10.0.0.1"], ["93.184.216.34", "192.168.1.5"], ["::1"], ["fe80::1"]])
def test_any_unsafe_dns_result_fails_closed(addresses) -> None:
    v = validate_lnurl_url("https://example.com/cb?k1=secret", policy=LNURLURLPolicy.remote_fetch())
    with pytest.raises(LNURLPrivateTargetError):
        _run(resolve_and_validate_lnurl_target(v, resolver=Resolver(addresses), policy=LNURLURLPolicy.remote_fetch()))

def test_empty_and_error_dns_results_fail_closed_without_secret_leakage() -> None:
    v = validate_lnurl_url("https://example.com/cb?k1=secret", policy=LNURLURLPolicy.remote_fetch())
    with pytest.raises(LNURLDNSResolutionError) as empty:
        _run(resolve_and_validate_lnurl_target(v, resolver=Resolver([]), policy=LNURLURLPolicy.remote_fetch()))
    assert "secret" not in str(empty.value)
    with pytest.raises(LNURLDNSResolutionError) as errored:
        _run(resolve_and_validate_lnurl_target(v, resolver=Resolver(error=True), policy=LNURLURLPolicy.remote_fetch()))
    assert "secret" not in str(errored.value)

def test_dns_rebinding_requires_revalidation_each_time() -> None:
    v = validate_lnurl_url("https://example.com/cb", policy=LNURLURLPolicy.remote_fetch())
    _run(resolve_and_validate_lnurl_target(v, resolver=Resolver(["93.184.216.34"]), policy=LNURLURLPolicy.remote_fetch()))
    with pytest.raises(LNURLPrivateTargetError):
        _run(resolve_and_validate_lnurl_target(v, resolver=Resolver(["127.0.0.1"]), policy=LNURLURLPolicy.remote_fetch()))

def test_redirects_to_metadata_localhost_and_private_ipv6_rejected() -> None:
    source = validate_lnurl_url("https://example.com/cb", policy=LNURLURLPolicy.remote_fetch())
    for url in ["https://169.254.169.254/latest", "https://localhost/cb", "https://[fd00::1]/cb"]:
        with pytest.raises(LNURLRedirectForbiddenError):
            validate_lnurl_redirect(source, url, policy=LNURLURLPolicy.remote_fetch())

def test_onion_does_not_invoke_public_dns_resolver() -> None:
    onion = "a" * 56 + ".onion"
    v = validate_lnurl_url(f"http://{onion}/cb", policy=LNURLURLPolicy.onion())
    resolver = Resolver(["127.0.0.1"])
    resolved = _run(resolve_and_validate_lnurl_target(v, resolver=resolver, policy=LNURLURLPolicy.onion()))
    assert resolver.calls == 0
    assert resolved.addresses == tuple()
