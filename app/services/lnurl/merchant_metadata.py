"""Merchant Lightning Address LNURL-pay metadata builder."""
from __future__ import annotations

from dataclasses import dataclass

from app.domain.lnurl.merchant_addresses import MerchantLightningAddress
from app.services.lnurl.pay_metadata import LNURLPayMetadataBuilder


@dataclass(frozen=True, slots=True)
class MerchantAddressMetadata:
    canonical_json: str
    metadata_hash: str
    identifier: str


def build_merchant_metadata(address: MerchantLightningAddress) -> MerchantAddressMetadata:
    label = _safe_text(address.display_label or "Merchant payment")
    desc = _safe_text(address.description or f"Lightning payment for {address.target_type.value}.")
    identifier = address.normalized_address
    result = LNURLPayMetadataBuilder().build_custom_metadata(plain_text=f"Payment to {label}", long_description=desc, identifier=identifier)
    lowered = result.canonical_json.lower()
    forbidden = ("workspace_id", "device_secret", "policy", "session", "access_pass", "principal_hash", "cashier email", "private_key", "seed")
    if any(value in lowered for value in forbidden):
        raise ValueError("Merchant metadata contains forbidden private context")
    return MerchantAddressMetadata(result.canonical_json, result.metadata_hash, identifier)


def _safe_text(value: str) -> str:
    normalized = " ".join(str(value).replace("<", " ").replace(">", " ").split())[:256]
    if not normalized:
        return "Merchant payment"
    return normalized
