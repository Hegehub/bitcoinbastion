"""Merchant Lightning Address domain primitives.

Merchant Lightning Addresses are multi-tenant payment-routing UX. They are not
identity, authorization, wallet proof, settlement evidence, or user IDs.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from app.services.access.crypto.hashing import hmac_sha256_prefixed

_RESERVED = frozenset({"admin", "administrator", "api", "auth", "support", "security", "root", "system", "postmaster", "abuse", "lnurl", "lightning", "payregister", "bitcoin-bastion"})
_LOCAL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,62}[a-z0-9])?$")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


class MerchantLightningAddressError(ValueError):
    reason_code = "merchant_lightning_address_error"


class MerchantAddressInvalidError(MerchantLightningAddressError):
    reason_code = "merchant_address_invalid"


class MerchantAddressReservedError(MerchantAddressInvalidError):
    reason_code = "merchant_address_reserved"


class MerchantDomainInvalidError(MerchantLightningAddressError):
    reason_code = "merchant_domain_invalid"


class MerchantLightningAddressStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"
    DOMAIN_VERIFICATION_REQUIRED = "domain_verification_required"


class MerchantDomainStatus(StrEnum):
    PENDING_VERIFICATION = "pending_verification"
    VERIFIED = "verified"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"


class MerchantDomainVerificationMethod(StrEnum):
    DNS_TXT = "dns_txt"
    HTTP_WELL_KNOWN = "http_well_known"
    BASTION_MANAGED = "bastion_managed"
    OPERATOR_APPROVED = "operator_approved"


class MerchantAddressTargetType(StrEnum):
    WORKSPACE = "workspace"
    STORE = "store"
    TERMINAL = "terminal"
    CASHIER_SHIFT = "cashier_shift"
    CAMPAIGN = "campaign"
    DONATION = "donation"
    SUBSCRIPTION = "subscription"
    CUSTOM = "custom"


class MerchantAddressVisibility(StrEnum):
    PUBLIC = "public"
    UNLISTED = "unlisted"
    INTERNAL = "internal"


class MerchantAddressSettlementMode(StrEnum):
    MERCHANT_NODE = "merchant_node"
    PAYREGISTER_NODE = "payregister_node"
    BTCPAY = "btcpay"
    BASTION_PROXY = "bastion_proxy"
    EXTERNAL_PROVIDER = "external_provider"


@dataclass(frozen=True, slots=True)
class MerchantLightningDomain:
    domain_id: str
    domain_hash: str
    normalized_domain: str
    workspace_id_hash: str
    status: MerchantDomainStatus
    verification_method: MerchantDomainVerificationMethod
    verification_token_hash: str | None
    verified_at: datetime | None
    verification_expires_at: datetime | None
    last_checked_at: datetime | None
    tls_required: bool
    onion_domain: bool
    created_at: datetime
    updated_at: datetime
    revoked_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class MerchantLightningAddress:
    address_id: str
    domain_id: str
    local_part_hash: str
    normalized_local_part: str
    normalized_domain: str
    workspace_id_hash: str
    target_type: MerchantAddressTargetType
    target_id_hash: str
    status: MerchantLightningAddressStatus
    visibility: MerchantAddressVisibility
    settlement_mode: MerchantAddressSettlementMode
    lnurl_pay_profile_id: str
    metadata_template_id: str
    min_sendable_msat: int
    max_sendable_msat: int
    comment_allowed: int
    payer_data_policy_id: str
    success_action_policy_id: str
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None
    revoked_at: datetime | None = None
    display_label: str = "Merchant payment"
    description: str | None = None

    @property
    def normalized_address(self) -> str:
        return f"{self.normalized_local_part}@{self.normalized_domain}"


def normalize_merchant_domain(value: str, *, allow_ip_literals: bool = False, production: bool = True) -> str:
    if not isinstance(value, str):
        raise MerchantDomainInvalidError("merchant_domain_invalid")
    raw = unicodedata.normalize("NFC", value.strip()).rstrip(".").lower()
    if not raw or len(raw) > 253 or _CONTROL_RE.search(raw) or any(ch.isspace() for ch in raw):
        raise MerchantDomainInvalidError("merchant_domain_invalid")
    if any(token in raw for token in ("/", "\\", "?", "#", "@")):
        raise MerchantDomainInvalidError("merchant_domain_invalid")
    if raw in {"localhost", "127.0.0.1", "::1"} and production:
        raise MerchantDomainInvalidError("merchant_domain_invalid")
    if not allow_ip_literals and re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", raw):
        raise MerchantDomainInvalidError("merchant_domain_invalid")
    try:
        labels = raw.split(".")
        if any(not label or len(label) > 63 for label in labels):
            raise UnicodeError
        ascii_domain = ".".join(label.encode("idna").decode("ascii") for label in labels)
    except UnicodeError as exc:
        raise MerchantDomainInvalidError("merchant_domain_invalid") from exc
    if "." not in ascii_domain and not ascii_domain.endswith(".onion"):
        raise MerchantDomainInvalidError("merchant_domain_invalid")
    return ascii_domain


def normalize_merchant_local_part(value: str) -> str:
    if not isinstance(value, str):
        raise MerchantAddressInvalidError("merchant_local_part_invalid")
    local = unicodedata.normalize("NFC", value.strip()).lower()
    if not local or len(local) > 64 or _CONTROL_RE.search(local) or any(ch.isspace() for ch in local):
        raise MerchantAddressInvalidError("merchant_local_part_invalid")
    if local in _RESERVED:
        raise MerchantAddressReservedError("merchant_address_reserved")
    if any(token in local for token in ("/", "\\", "%", "..", "?", "#", "@")) or _LOCAL_RE.fullmatch(local) is None:
        raise MerchantAddressInvalidError("merchant_local_part_invalid")
    return local


def merchant_address_hash(pepper: str, local_part: str, domain: str) -> str:
    return hmac_sha256_prefixed(pepper, f"{normalize_merchant_local_part(local_part)}@{normalize_merchant_domain(domain)}")


def now_utc() -> datetime:
    return datetime.now(UTC)
