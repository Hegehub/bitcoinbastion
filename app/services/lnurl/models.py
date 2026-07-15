"""Immutable LNURL service-layer value objects with safe repr output."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

class LNURLURLPurpose(str, Enum):
    SERVICE_OWNED_AUTH = "service_owned_auth"
    SERVICE_OWNED_CALLBACK = "service_owned_callback"
    SERVICE_OWNED_PAY = "service_owned_pay"
    SERVICE_OWNED_WITHDRAW = "service_owned_withdraw"
    LIGHTNING_ADDRESS_DISCOVERY = "lightning_address_discovery"
    REMOTE_CALLBACK_FETCH = "remote_callback_fetch"
    REMOTE_VERIFY_FETCH = "remote_verify_fetch"
    SUCCESS_ACTION = "success_action"
    DEVELOPMENT = "development"
    ONION = "onion"

@dataclass(frozen=True, slots=True)
class DecodedLNURL:
    encoded_fingerprint: str
    normalized_url: str = field(repr=False)
    scheme: str
    hostname: str
    port: int | None
    path: str
    has_query: bool
    is_onion: bool
    safety_class: str

    def __str__(self) -> str:
        return f"DecodedLNURL(hostname={self.hostname}, path={self.path}, has_query={self.has_query})"

@dataclass(frozen=True, slots=True)
class ValidatedLNURLURL:
    normalized_url: str = field(repr=False)
    scheme: str
    hostname: str
    ascii_hostname: str
    port: int | None
    path: str
    query: str = field(repr=False)
    is_onion: bool
    is_loopback: bool
    is_private_target: bool
    purpose: LNURLURLPurpose

    def __str__(self) -> str:
        return f"ValidatedLNURLURL(scheme={self.scheme}, host={self.ascii_hostname}, path={self.path}, has_query={bool(self.query)})"

@dataclass(frozen=True, slots=True)
class ResolvedLNURLTarget:
    validated_url: ValidatedLNURLURL
    addresses: tuple[str, ...]
    address_fingerprints: tuple[str, ...]
