"""QR payload helpers for static PayRegister LNURL endpoints."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote

from app.services.lnurl.encoding import encode_lnurl
from app.services.lnurl.url_safety import LNURLURLPolicy
from app.services.payregister.lnurl.payment_context import PayRegisterLNULEndpointMode


@dataclass(frozen=True, slots=True)
class PayRegisterLNURLQRPayload:
    raw_discovery_url: str
    lnurl: str
    public_alias: str
    endpoint_mode: str
    expires_at: datetime | None
    display_label: str
    safe_merchant_description: str | None


def build_static_lnurl_url(*, base_url: str, public_alias: str) -> str:
    return f"{base_url.rstrip('/')}/.well-known/lnurlp/{quote(public_alias, safe='')}"


def encode_lnurl_bech32(url: str) -> str:
    return encode_lnurl(url, policy=LNURLURLPolicy.remote_fetch())


def build_qr_payload(
    *,
    base_url: str,
    public_alias: str,
    endpoint_mode: PayRegisterLNULEndpointMode,
    display_label: str,
    safe_merchant_description: str | None = None,
    expires_at: datetime | None = None,
) -> PayRegisterLNURLQRPayload:
    raw = build_static_lnurl_url(base_url=base_url, public_alias=public_alias)
    return PayRegisterLNURLQRPayload(raw, encode_lnurl_bech32(raw), public_alias, endpoint_mode.value, expires_at, display_label, safe_merchant_description)


def validate_qr_payload(payload: PayRegisterLNURLQRPayload) -> None:
    lowered = (payload.raw_discovery_url + payload.lnurl).lower()
    forbidden = ("bolt11", "access_pass", "session_token", "private_key", "seed", "workspace_", "callback_token")
    if any(value in lowered for value in forbidden):
        raise ValueError("Static QR payload contains forbidden secret material")
