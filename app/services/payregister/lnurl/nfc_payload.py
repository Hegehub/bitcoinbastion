"""NFC payload helpers for static PayRegister LNURL endpoints."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.services.payregister.lnurl.payment_context import PayRegisterLNULEndpointMode
from app.services.payregister.lnurl.qr_payload import build_static_lnurl_url, encode_lnurl_bech32


@dataclass(frozen=True, slots=True)
class PayRegisterLNURLNFCPayload:
    lnurl_text: str
    https_url: str
    ndef_records: tuple[dict[str, str], ...]
    public_alias: str
    endpoint_mode: str
    expires_at: datetime | None


def build_nfc_lnurl_payload(
    *,
    base_url: str,
    public_alias: str,
    endpoint_mode: PayRegisterLNULEndpointMode,
    expires_at: datetime | None = None,
) -> PayRegisterLNURLNFCPayload:
    url = build_static_lnurl_url(base_url=base_url, public_alias=public_alias)
    lnurl = encode_lnurl_bech32(url)
    return PayRegisterLNURLNFCPayload(
        lnurl_text=lnurl,
        https_url=url,
        ndef_records=({"type": "text/plain", "value": lnurl}, {"type": "uri", "value": url}),
        public_alias=public_alias,
        endpoint_mode=endpoint_mode.value,
        expires_at=expires_at,
    )


def validate_nfc_payload(payload: PayRegisterLNURLNFCPayload) -> None:
    lowered = (payload.https_url + payload.lnurl_text).lower()
    if any(value in lowered for value in ("bolt11", "access_pass", "session_token", "private_key", "seed", "callback_token")):
        raise ValueError("NFC payload contains forbidden secret material")
