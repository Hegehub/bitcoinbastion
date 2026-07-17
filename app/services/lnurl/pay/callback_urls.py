"""Trusted LNURL-pay callback URL construction."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import ParseResult, urljoin, urlparse

from app.services.access.crypto.hashing import sha256_prefixed
from app.services.lnurl.pay.errors import LNURLPayUnsafeCallbackError


@dataclass(frozen=True, slots=True)
class LNURLPayCallbackURLConfig:
    public_base_url: str
    callback_path_prefix: str = "/v1/lnurl/pay/callback"
    allow_onion_http: bool = False


class LNURLPayCallbackURLBuilder:
    def __init__(self, config: LNURLPayCallbackURLConfig) -> None:
        self.config = config
        self._parsed_base = _validate_base_url(config.public_base_url, allow_onion_http=config.allow_onion_http)

    def build_callback_url(self, opaque_request_reference: str) -> str:
        if not opaque_request_reference or "/" in opaque_request_reference or ".." in opaque_request_reference:
            raise LNURLPayUnsafeCallbackError("Unsafe LNURL-pay request reference")
        prefix = "/" + self.config.callback_path_prefix.strip("/")
        path = f"{prefix}/{opaque_request_reference}"
        if ".." in path or "//" in path:
            raise LNURLPayUnsafeCallbackError("Unsafe LNURL-pay callback path")
        base = self._parsed_base.geturl().rstrip("/")
        callback = urljoin(base + "/", path.lstrip("/"))
        parsed = urlparse(callback)
        if parsed.fragment or parsed.username or parsed.password or parsed.netloc != self._parsed_base.netloc:
            raise LNURLPayUnsafeCallbackError("Unsafe LNURL-pay callback URL")
        return callback

    def callback_hash(self, callback_url: str) -> str:
        return sha256_prefixed(callback_url)


def _validate_base_url(base_url: str, *, allow_onion_http: bool) -> ParseResult:
    parsed = urlparse(base_url)
    if parsed.fragment or parsed.params or parsed.query:
        raise LNURLPayUnsafeCallbackError("LNURL-pay public base URL must not contain params, query, or fragment")
    if parsed.username or parsed.password:
        raise LNURLPayUnsafeCallbackError("LNURL-pay public base URL must not contain credentials")
    if not parsed.hostname:
        raise LNURLPayUnsafeCallbackError("LNURL-pay public base URL host is required")
    if parsed.scheme != "https":
        if not (allow_onion_http and parsed.scheme == "http" and parsed.hostname.endswith(".onion")):
            raise LNURLPayUnsafeCallbackError("LNURL-pay public base URL must use HTTPS")
    return parsed
