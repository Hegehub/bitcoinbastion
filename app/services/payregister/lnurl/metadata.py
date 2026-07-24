"""Canonical wallet-visible PayRegister LNURL metadata."""
from __future__ import annotations

from dataclasses import dataclass

from app.services.lnurl.pay_metadata import LNURLPayMetadataBuilder


@dataclass(frozen=True, slots=True)
class PayRegisterLNURLMetadata:
    canonical_json: str
    metadata_hash: str
    plain_text: str
    identifier: str | None


def build_payregister_lnurl_metadata(
    *,
    merchant_display_name: str,
    order_reference: str | None,
    terminal_reference: str | None,
    description: str | None,
    lightning_identifier: str | None = None,
) -> PayRegisterLNURLMetadata:
    result = LNURLPayMetadataBuilder().build_payregister_metadata(
        merchant_display_name=merchant_display_name,
        order_reference=order_reference,
        terminal_reference=terminal_reference,
        description=description,
        lightning_identifier=lightning_identifier,
    )
    return PayRegisterLNURLMetadata(result.canonical_json, result.metadata_hash, result.plain_text, result.identifier)
