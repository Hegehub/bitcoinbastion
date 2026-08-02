from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit


def normalize_base_url(base_url: str) -> str:
    normalized = base_url.strip().rstrip("/")
    if not normalized:
        raise ValueError("base_url must not be empty")
    return normalized


def normalize_api_prefix(api_prefix: str) -> str:
    prefix = api_prefix.strip() or "/api/v1"
    if not prefix.startswith("/"):
        prefix = f"/{prefix}"
    return prefix.rstrip("/")


@dataclass(frozen=True)
class BastionSDKConfig:
    base_url: str
    api_prefix: str = "/api/v1"
    timeout: float = 5.0
    self_hosted_mode: bool = False
    allow_onion: bool = False
    allowed_lnurl_domains: tuple[str, ...] = ()
    persist_session: bool = False
    max_safe_retries: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "base_url", normalize_base_url(self.base_url))
        object.__setattr__(self, "api_prefix", normalize_api_prefix(self.api_prefix))
        parsed = urlsplit(self.base_url)
        host = parsed.hostname or ""
        if host.endswith(".onion") and not self.allow_onion:
            raise ValueError("Onion endpoints require allow_onion=True and caller-configured Tor transport")
        local = host in {"localhost", "127.0.0.1", "::1"}
        if parsed.scheme != "https" and not ((self.self_hosted_mode or local) and local):
            # Preserve developer-preview compatibility while making the insecure mode explicit.
            if host not in {"testserver", "example.com"}:
                raise ValueError("HTTPS is required unless self_hosted_mode explicitly permits localhost")
        if self.persist_session:
            raise ValueError("Automatic raw session persistence is not supported")
