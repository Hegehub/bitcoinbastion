"""Central LNURL URL normalization, policy validation, and SSRF safety boundary."""
from __future__ import annotations

import hashlib
import ipaddress
import re
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlsplit, urlunsplit

from app.services.lnurl.errors import (
    LNURLAuthDomainMismatchError,
    LNURLCredentialsForbiddenError,
    LNURLDNSResolutionError,
    LNURLFragmentForbiddenError,
    LNURLInvalidHostError,
    LNURLLinkLocalTargetError,
    LNURLLoopbackTargetError,
    LNURLOnionValidationError,
    LNURLPortForbiddenError,
    LNURLPrivateTargetError,
    LNURLRedirectForbiddenError,
    LNURLUnsafeURLError,
    LNURLUnsupportedSchemeError,
)
from app.services.lnurl.models import LNURLURLPurpose, ResolvedLNURLTarget, ValidatedLNURLURL

MAX_LNURL_URL_BYTES = 2048
MAX_LNURL_VALUE_CHARS = 4096
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_V3_ONION_RE = re.compile(r"^[a-z2-7]{56}\.onion$")
_V2_ONION_RE = re.compile(r"^[a-z2-7]{16}\.onion$")

@dataclass(frozen=True, slots=True)
class LNURLURLPolicy:
    purpose: LNURLURLPurpose
    allowed_schemes: frozenset[str]
    allowed_domains: frozenset[str] = frozenset()
    allowed_ports: frozenset[int] = frozenset()
    allow_onion_http: bool = False
    allow_private_networks: bool = False
    allow_loopback: bool = False
    allow_link_local: bool = False
    allow_custom_ports: bool = False
    allow_fragments: bool = False
    maximum_url_bytes: int = MAX_LNURL_URL_BYTES
    require_stable_auth_domain: bool = False

    @classmethod
    def remote_fetch(cls) -> "LNURLURLPolicy":
        return cls(LNURLURLPurpose.REMOTE_CALLBACK_FETCH, frozenset({"https"}), allowed_ports=frozenset({443}))

    @classmethod
    def service_owned_auth(cls, *, domains: Collection[str], stable_domain: str | None = None) -> "LNURLURLPolicy":
        allowed = frozenset(_normalize_domain(d) for d in (domains or ([stable_domain] if stable_domain else [])))
        return cls(LNURLURLPurpose.SERVICE_OWNED_AUTH, frozenset({"https"}), allowed, frozenset({443}), require_stable_auth_domain=bool(stable_domain))

    @classmethod
    def service_owned_callback(cls, *, domains: Collection[str]) -> "LNURLURLPolicy":
        return cls(LNURLURLPurpose.SERVICE_OWNED_CALLBACK, frozenset({"https"}), frozenset(_normalize_domain(d) for d in domains), frozenset({443}))

    @classmethod
    def success_action(cls) -> "LNURLURLPolicy":
        return cls(LNURLURLPurpose.SUCCESS_ACTION, frozenset({"https"}), allowed_ports=frozenset({443}))

    @classmethod
    def onion(cls) -> "LNURLURLPolicy":
        return cls(LNURLURLPurpose.ONION, frozenset({"http", "https"}), allowed_ports=frozenset({80, 443}), allow_onion_http=True)

    @classmethod
    def development(cls, *, ports: Collection[int] = (80, 443, 8000, 8080)) -> "LNURLURLPolicy":
        return cls(LNURLURLPurpose.DEVELOPMENT, frozenset({"http", "https"}), allowed_ports=frozenset(ports), allow_private_networks=True, allow_loopback=True, allow_link_local=True, allow_custom_ports=True)

class LNURLResolver(Protocol):
    async def resolve(self, hostname: str, port: int) -> Sequence[str]: ...

def _normalize_domain(hostname: str) -> str:
    host = hostname.rstrip(".").lower()
    try:
        ipaddress.ip_address(host)
        return host
    except ValueError:
        pass
    try:
        return host.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise LNURLInvalidHostError() from exc

def hostname_matches_allowlist(hostname: str, allowed_domains: Collection[str]) -> bool:
    host = _normalize_domain(hostname)
    return any(host == _normalize_domain(domain) for domain in allowed_domains)

def validate_lnurl_url(url: str, *, policy: LNURLURLPolicy) -> ValidatedLNURLURL:
    if not url or not isinstance(url, str):
        raise LNURLUnsafeURLError("URL is required.")
    if len(url.encode("utf-8", "surrogatepass")) > policy.maximum_url_bytes:
        from app.services.lnurl.errors import LNURLInputTooLargeError
        raise LNURLInputTooLargeError()
    if url.strip() != url or _CONTROL_RE.search(url) or any(c.isspace() for c in url):
        raise LNURLUnsafeURLError("URL contains unsafe characters.")
    if "\\" in url:
        raise LNURLUnsafeURLError("URL contains unsafe path separators.")
    if re.search(r"%(?![0-9a-fA-F]{2})", url):
        raise LNURLUnsafeURLError("URL contains invalid percent encoding.")
    if re.search(r"%0d|%0a", url, re.IGNORECASE):
        raise LNURLUnsafeURLError("URL contains encoded CR/LF characters.")
    parsed = urlsplit(url)
    if not parsed.scheme or not parsed.netloc:
        raise LNURLUnsafeURLError("URL must be absolute.")
    scheme = parsed.scheme.lower()
    if scheme not in policy.allowed_schemes:
        raise LNURLUnsupportedSchemeError()
    if parsed.username or parsed.password:
        raise LNURLCredentialsForbiddenError()
    if parsed.fragment and not policy.allow_fragments:
        raise LNURLFragmentForbiddenError()
    if not parsed.hostname:
        raise LNURLInvalidHostError()
    raw_host = parsed.hostname
    if "%" in raw_host:
        raise LNURLInvalidHostError()
    ascii_host = _normalize_domain(raw_host)
    if ascii_host == "localhost" and not policy.allow_loopback:
        raise LNURLLoopbackTargetError()
    if ":" not in ascii_host:
        _validate_hostname_shape(ascii_host)
    is_onion = ascii_host.endswith(".onion")
    if is_onion:
        _validate_onion(ascii_host, scheme, policy)
    elif scheme == "http" and policy.purpose is not LNURLURLPurpose.DEVELOPMENT:
        raise LNURLUnsupportedSchemeError()
    try:
        port = parsed.port  # urlsplit raises ValueError for malformed/out-of-range ports
    except ValueError as exc:
        raise LNURLPortForbiddenError() from exc
    if port == 0:
        raise LNURLPortForbiddenError()
    _validate_port(scheme, port, is_onion, policy)
    if policy.allowed_domains and not hostname_matches_allowlist(ascii_host, policy.allowed_domains):
        error = LNURLAuthDomainMismatchError if policy.require_stable_auth_domain else LNURLInvalidHostError
        raise error()
    if policy.require_stable_auth_domain and policy.allowed_domains and ascii_host not in {_normalize_domain(d) for d in policy.allowed_domains}:
        raise LNURLAuthDomainMismatchError()
    ip_flags = _classify_host_ip(ascii_host, policy)
    netloc = ascii_host
    if port is not None:
        netloc = f"{netloc}:{port}"
    normalized = urlunsplit((scheme, netloc, parsed.path or "/", parsed.query, ""))
    return ValidatedLNURLURL(normalized, scheme, ascii_host, ascii_host, port, parsed.path or "/", parsed.query, is_onion, ip_flags["loopback"], ip_flags["private"], policy.purpose)

def _validate_hostname_shape(host: str) -> None:
    if not host or len(host) > 253 or ".." in host:
        raise LNURLInvalidHostError()
    for label in host.split("."):
        if not label or len(label) > 63:
            raise LNURLInvalidHostError()

def _validate_onion(host: str, scheme: str, policy: LNURLURLPolicy) -> None:
    if _V2_ONION_RE.match(host) or not _V3_ONION_RE.match(host):
        raise LNURLOnionValidationError()
    if scheme == "http" and not policy.allow_onion_http:
        raise LNURLOnionValidationError()

def _validate_port(scheme: str, port: int | None, is_onion: bool, policy: LNURLURLPolicy) -> None:
    effective = port or (80 if scheme == "http" else 443)
    if effective < 1 or effective > 65535:
        raise LNURLPortForbiddenError()
    defaults = {"https": 443, "http": 80}
    if policy.allowed_ports and effective not in policy.allowed_ports:
        raise LNURLPortForbiddenError()
    if not policy.allow_custom_ports and effective != defaults.get(scheme):
        raise LNURLPortForbiddenError()
    if is_onion and scheme == "http" and effective != 80 and not policy.allow_custom_ports:
        raise LNURLPortForbiddenError()

def _classify_host_ip(host: str, policy: LNURLURLPolicy) -> dict[str, bool]:
    try:
        ip = ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        return {"loopback": False, "private": False}
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    if ip.is_loopback and not policy.allow_loopback:
        raise LNURLLoopbackTargetError()
    if ip.is_link_local and not policy.allow_link_local:
        raise LNURLLinkLocalTargetError()
    unsafe = ip.is_private or ip.is_multicast or ip.is_unspecified or ip.is_reserved or ip.is_loopback or ip.is_link_local
    if unsafe and not policy.allow_private_networks:
        raise LNURLPrivateTargetError()
    return {"loopback": ip.is_loopback, "private": unsafe}

async def resolve_and_validate_lnurl_target(validated_url: ValidatedLNURLURL, *, resolver: LNURLResolver, policy: LNURLURLPolicy) -> ResolvedLNURLTarget:
    if validated_url.is_onion:
        return ResolvedLNURLTarget(validated_url, tuple(), tuple())
    port = validated_url.port or (443 if validated_url.scheme == "https" else 80)
    try:
        resolved = tuple(dict.fromkeys(await resolver.resolve(validated_url.ascii_hostname, port)))
    except Exception as exc:
        raise LNURLDNSResolutionError() from exc
    if not resolved:
        raise LNURLDNSResolutionError()
    for addr in resolved:
        _classify_host_ip(addr, policy)
    fps = tuple(f"sha256:{hashlib.sha256(addr.encode()).hexdigest()}" for addr in resolved)
    return ResolvedLNURLTarget(validated_url, resolved, fps)

def validate_lnurl_redirect(source: ValidatedLNURLURL, redirect_url: str, *, policy: LNURLURLPolicy) -> ValidatedLNURLURL:
    try:
        target = validate_lnurl_url(redirect_url, policy=policy)
    except LNURLUnsafeURLError as exc:
        raise LNURLRedirectForbiddenError() from exc
    if source.purpose is LNURLURLPurpose.SERVICE_OWNED_AUTH and (target.ascii_hostname != source.ascii_hostname or target.scheme != source.scheme or target.port != source.port):
        raise LNURLRedirectForbiddenError()
    if source.scheme == "https" and target.scheme == "http" and not target.is_onion:
        raise LNURLRedirectForbiddenError()
    return target

__all__ = ["LNURLURLPolicy", "LNURLResolver", "validate_lnurl_url", "resolve_and_validate_lnurl_target", "validate_lnurl_redirect", "hostname_matches_allowlist", "MAX_LNURL_URL_BYTES", "MAX_LNURL_VALUE_CHARS"]
