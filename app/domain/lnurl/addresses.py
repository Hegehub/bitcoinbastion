"""Lightning Address routing domain objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class LightningAddressPurpose(StrEnum):
    PRODUCT_SUBSCRIPTION = "product_subscription"
    MERCHANT_PAYMENT = "merchant_payment"
    PAYREGISTER_STORE = "payregister_store"
    PAYREGISTER_TERMINAL = "payregister_terminal"
    CASHIER = "cashier"
    DONATION = "donation"
    CUSTOM_BUSINESS = "custom_business"


class LightningAddressStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    PENDING_DOMAIN_VERIFICATION = "pending_domain_verification"
    RETIRED = "retired"


@dataclass(frozen=True, slots=True)
class LightningAddressDescriptor:
    local_part: str
    domain: str
    purpose: LightningAddressPurpose
    status: LightningAddressStatus
    domain_policy_version: int
    product_code: str | None = None
    merchant_hash: str | None = None
    terminal_hash: str | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.local_part.strip():
            raise ValueError("lightning_address_local_part_required")
        if not self.domain.strip():
            raise ValueError("lightning_address_domain_required")
        if self.domain_policy_version < 1:
            raise ValueError("lightning_address_domain_policy_version_required")


LightningAddressType = LightningAddressPurpose
