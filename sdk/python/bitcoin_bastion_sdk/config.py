from __future__ import annotations

from dataclasses import dataclass


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

    def __post_init__(self) -> None:
        object.__setattr__(self, "base_url", normalize_base_url(self.base_url))
        object.__setattr__(self, "api_prefix", normalize_api_prefix(self.api_prefix))
