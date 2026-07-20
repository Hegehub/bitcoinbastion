"""Merchant domain verification helpers with SSRF-safe HTTP seams."""
from __future__ import annotations

import ipaddress
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol
from urllib.parse import urlparse

from app.domain.lnurl.merchant_addresses import MerchantDomainInvalidError, MerchantDomainVerificationMethod, normalize_merchant_domain
from app.services.access.crypto.hashing import hmac_sha256_prefixed


class MerchantDNSResolver(Protocol):
    def txt_records(self, name: str) -> tuple[str, ...]: ...


class MerchantHTTPClient(Protocol):
    def get_text(self, url: str, *, max_redirects: int, max_bytes: int) -> tuple[str, str]: ...


@dataclass(frozen=True, slots=True)
class MerchantDomainVerificationChallenge:
    token: str
    token_hash: str
    method: MerchantDomainVerificationMethod
    expires_at: datetime
    dns_name: str
    expected_value: str


class MerchantDomainVerificationService:
    def __init__(self, *, pepper: str = "dev-merchant-ln-domain-verify-pepper-change-me", ttl_seconds: int = 900, http_max_redirects: int = 2, http_max_bytes: int = 4096) -> None:
        self.pepper = pepper
        self.ttl_seconds = ttl_seconds
        self.http_max_redirects = http_max_redirects
        self.http_max_bytes = http_max_bytes

    def create_challenge(self, domain: str, method: MerchantDomainVerificationMethod) -> MerchantDomainVerificationChallenge:
        normalized = normalize_merchant_domain(domain)
        token = secrets.token_urlsafe(32)
        return MerchantDomainVerificationChallenge(
            token=token,
            token_hash=hmac_sha256_prefixed(self.pepper, token),
            method=method,
            expires_at=datetime.now(UTC) + timedelta(seconds=self.ttl_seconds),
            dns_name=f"_bastion-lnurl.{normalized}",
            expected_value=f"bastion-lnurl-verification={token}",
        )

    def verify_dns_txt(self, *, domain: str, expected_token: str, resolver: MerchantDNSResolver, now: datetime | None = None, expires_at: datetime | None = None) -> bool:
        if expires_at is not None and (now or datetime.now(UTC)) >= expires_at:
            return False
        normalized = normalize_merchant_domain(domain)
        return f"bastion-lnurl-verification={expected_token}" in resolver.txt_records(f"_bastion-lnurl.{normalized}")

    def verify_http_well_known(self, *, domain: str, expected_token: str, http_client: MerchantHTTPClient) -> bool:
        normalized = normalize_merchant_domain(domain)
        url = f"https://{normalized}/.well-known/bastion-lnurl-verification"
        _validate_http_verification_url(url, expected_host=normalized)
        final_url, body = http_client.get_text(url, max_redirects=self.http_max_redirects, max_bytes=self.http_max_bytes)
        _validate_http_verification_url(final_url, expected_host=normalized)
        if len(body.encode("utf-8")) > self.http_max_bytes:
            return False
        return expected_token in body


def _validate_http_verification_url(url: str, *, expected_host: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.hostname.lower() != expected_host:
        raise MerchantDomainInvalidError("merchant_http_verification_host_invalid")
    host = parsed.hostname.lower()
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
        raise MerchantDomainInvalidError("merchant_http_verification_ssrf_blocked")
