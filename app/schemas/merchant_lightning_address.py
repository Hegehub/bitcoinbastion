"""OpenAPI-safe merchant Lightning Address schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MerchantLightningDomainCreate(BaseModel):
    normalized_domain: str = Field(description="Merchant domain to verify; not an auth identity.")
    workspace_id_hash: str
    verification_method: Literal["dns_txt", "http_well_known", "bastion_managed"] = "dns_txt"


class MerchantLightningDomainResponse(BaseModel):
    domain_id: str
    normalized_domain: str
    workspace_id_hash: str
    status: str
    verification_method: str
    verified_at: datetime | None = None
    verification_expires_at: datetime | None = None


class MerchantLightningAddressCreate(BaseModel):
    domain_id: str
    local_part: str
    workspace_id_hash: str
    target_type: Literal["workspace", "store", "terminal", "cashier_shift", "campaign", "donation", "subscription", "custom"]
    target_id_hash: str
    settlement_mode: Literal["merchant_node", "payregister_node", "btcpay", "bastion_proxy", "external_provider"] = "payregister_node"
    min_sendable_msat: int = 1000
    max_sendable_msat: int = 100_000_000
    comment_allowed: int = 0
    display_label: str = "Merchant"
    description: str | None = None


class MerchantLightningAddressResponse(BaseModel):
    address_id: str
    normalized_address: str
    workspace_id_hash: str
    target_type: str
    status: str
    visibility: str
    settlement_mode: str
    min_sendable_msat: int
    max_sendable_msat: int
    comment_allowed: int
