"""Lightning Principal domain primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.lnurl.security import LNURLSecurityLevel


class LightningPrincipalType(StrEnum):
    LNURL_AUTH_PRINCIPAL = "lnurl_auth_principal"
    PAYERDATA_AUTH_PRINCIPAL = "payerdata_auth_principal"
    LINKED_WALLET_PRINCIPAL = "linked_wallet_principal"
    BUSINESS_LIGHTNING_PRINCIPAL = "business_lightning_principal"
    PAYREGISTER_OWNER_PRINCIPAL = "payregister_owner_principal"
    PAYREGISTER_OPERATOR_PRINCIPAL = "payregister_operator_principal"


class LightningPrincipalStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    RECOVERY_LOCKED = "recovery_locked"


@dataclass(frozen=True, slots=True)
class LightningPrincipalIdentity:
    principal_hash: str
    lnurl_key_hash: str
    auth_domain_hash: str
    principal_type: LightningPrincipalType
    verification_strength: LNURLSecurityLevel
    status: LightningPrincipalStatus
    product_pseudonym: str | None = None
    created_at: datetime | None = None
    last_verified_at: datetime | None = None

    def __post_init__(self) -> None:
        for field_name in ("principal_hash", "lnurl_key_hash", "auth_domain_hash"):
            if not getattr(self, field_name).startswith(("hmac-sha256:", "sha256:")):
                raise ValueError(f"{field_name}_must_be_hash")
