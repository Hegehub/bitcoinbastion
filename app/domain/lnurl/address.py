"""Lightning Address domain enums."""

from __future__ import annotations

from enum import StrEnum


class LightningAddressType(StrEnum):
    PRODUCT = "product"
    MERCHANT = "merchant"
    PAYREGISTER_STORE = "payregister_store"
    PAYREGISTER_TERMINAL = "payregister_terminal"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"
    CUSTOM_DOMAIN = "custom_domain"


class LightningAddressStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    DOMAIN_PENDING = "domain_pending"
    DOMAIN_VERIFIED = "domain_verified"
