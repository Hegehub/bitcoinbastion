"""Lightning Address domain primitives for LNURL-pay routing.

A Lightning Address is human-readable payment routing UX. It is not identity,
authorization, wallet proof, settlement evidence, a principal, or a session.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

MAX_LIGHTNING_ADDRESS_LENGTH = 320
MAX_LIGHTNING_LOCAL_PART_LENGTH = 64
MAX_LIGHTNING_DOMAIN_LENGTH = 253
RESERVED_LIGHTNING_LOCAL_PARTS = frozenset(
    {
        "admin",
        "administrator",
        "root",
        "api",
        "auth",
        "login",
        "register",
        "support",
        "security",
        "system",
        "status",
        "health",
        "metrics",
        "internal",
        "private",
        "well-known",
        "lnurl",
        "lnurlp",
        "callback",
        "verify",
        "withdraw",
        "recovery",
        "lockdown",
        "sovereign",
    }
)
PRODUCT_LIGHTNING_LOCAL_PARTS = {
    "lite": "lite_pass",
    "basic": "basic_pass",
    "plus": "plus_pass",
    "pro": "pro_pass",
    "business": "business_pass",
    "enterprise": "enterprise_pass",
}
_LOCAL_PART_RE = re.compile(r"^[a-z0-9](?:[a-z0-9_-]{0,62}[a-z0-9])?$")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_UNSAFE_ENCODED_RE = re.compile(r"%(?:00|2f|5c)", re.IGNORECASE)


class LightningAddressInvalidError(ValueError):
    reason_code = "lightning_address_invalid"


class LightningAddressReservedError(LightningAddressInvalidError):
    reason_code = "lightning_address_reserved"


class LightningAddressDomainInvalidError(LightningAddressInvalidError):
    reason_code = "lightning_address_domain_invalid"


class LightningAddressTargetType(StrEnum):
    SUBSCRIPTION_PRODUCT = "subscription_product"
    MERCHANT = "merchant"
    PAYREGISTER_STORE = "payregister_store"
    PAYREGISTER_TERMINAL = "payregister_terminal"
    DONATION = "donation"
    BUSINESS_INVOICE = "business_invoice"
    CUSTOM = "custom"


class LightningAddressStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DISABLED = "disabled"
    EXPIRED = "expired"
    PENDING_VERIFICATION = "pending_verification"


class LightningAddressDomainStatus(StrEnum):
    ACTIVE = "active"
    PENDING_VERIFICATION = "pending_verification"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class LightningAddressVisibility(StrEnum):
    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"


class LightningAddressDomainClass(StrEnum):
    BASTION_PRODUCT_DOMAIN = "bastion_product_domain"
    BASTION_PAYREGISTER_DOMAIN = "bastion_payregister_domain"
    VERIFIED_MERCHANT_DOMAIN = "verified_merchant_domain"
    ONION_PRIVACY_DOMAIN = "onion_privacy_domain"
    UNSUPPORTED_DOMAIN = "unsupported_domain"


@dataclass(frozen=True, slots=True)
class LightningAddressRecord:
    address_id: str
    local_part: str
    domain: str
    normalized_address: str
    target_type: LightningAddressTargetType
    target_reference_hash: str
    status: LightningAddressStatus
    visibility: LightningAddressVisibility
    min_sendable_msat: int
    max_sendable_msat: int
    metadata_template_id: str
    callback_policy_id: str
    payer_data_policy_id: str
    success_action_policy_id: str
    comment_allowed: int
    currency: str
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None
    version: int
    schema_epoch: int
    policy_epoch: int
    principal_hash: str | None = None
    business_workspace_hash: str | None = None
    payregister_store_hash: str | None = None
    payregister_terminal_hash: str | None = None
    product_code: str | None = None
    custom_domain_id: str | None = None
    display_label: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        expected = build_lightning_address(self.local_part, self.domain)
        if self.normalized_address != expected:
            raise LightningAddressInvalidError("lightning_address_normalization_mismatch")
        if self.min_sendable_msat <= 0 or self.max_sendable_msat < self.min_sendable_msat:
            raise LightningAddressInvalidError("lightning_address_amount_policy_invalid")
        if self.comment_allowed < 0:
            raise LightningAddressInvalidError("lightning_address_comment_policy_invalid")
        if self.version < 1 or self.schema_epoch < 1 or self.policy_epoch < 1:
            raise LightningAddressInvalidError("lightning_address_version_invalid")


def normalize_lightning_address(value: str) -> str:
    local_part, domain = split_lightning_address(value)
    return build_lightning_address(local_part, domain)


def split_lightning_address(value: str) -> tuple[str, str]:
    if not isinstance(value, str):
        raise LightningAddressInvalidError("lightning_address_invalid")
    raw = value.strip()
    if raw != value or not raw or len(raw) > MAX_LIGHTNING_ADDRESS_LENGTH:
        raise LightningAddressInvalidError("lightning_address_invalid")
    if _CONTROL_RE.search(raw) or any(ch.isspace() for ch in raw):
        raise LightningAddressInvalidError("lightning_address_invalid")
    if raw.count("@") != 1:
        raise LightningAddressInvalidError("lightning_address_invalid")
    if any(part in raw for part in ("/", "\\", "?", "#")) or _UNSAFE_ENCODED_RE.search(raw):
        raise LightningAddressInvalidError("lightning_address_invalid")
    local_part, domain = raw.split("@", 1)
    return normalize_local_part(local_part), normalize_lightning_domain(domain)


def normalize_local_part(value: str) -> str:
    if not isinstance(value, str):
        raise LightningAddressInvalidError("lightning_address_local_part_invalid")
    local = unicodedata.normalize("NFC", value.strip()).lower()
    if not local or len(local) > MAX_LIGHTNING_LOCAL_PART_LENGTH:
        raise LightningAddressInvalidError("lightning_address_local_part_invalid")
    validate_lightning_address_local_part(local)
    return local


def normalize_lightning_domain(value: str) -> str:
    if not isinstance(value, str):
        raise LightningAddressDomainInvalidError("lightning_address_domain_invalid")
    domain = unicodedata.normalize("NFC", value.strip()).rstrip(".").lower()
    if not domain or len(domain) > MAX_LIGHTNING_DOMAIN_LENGTH:
        raise LightningAddressDomainInvalidError("lightning_address_domain_invalid")
    if _CONTROL_RE.search(domain) or any(ch.isspace() for ch in domain):
        raise LightningAddressDomainInvalidError("lightning_address_domain_invalid")
    try:
        labels = domain.split(".")
        if any(not label or len(label) > 63 for label in labels):
            raise UnicodeError
        ascii_domain = ".".join(label.encode("idna").decode("ascii") for label in labels)
    except UnicodeError as exc:
        raise LightningAddressDomainInvalidError("lightning_address_domain_invalid") from exc
    if any(label.startswith("-") or label.endswith("-") for label in ascii_domain.split(".")):
        raise LightningAddressDomainInvalidError("lightning_address_domain_invalid")
    return ascii_domain


def build_lightning_address(local_part: str, domain: str) -> str:
    return f"{normalize_local_part(local_part)}@{normalize_lightning_domain(domain)}"


def validate_lightning_address_local_part(value: str) -> None:
    if _CONTROL_RE.search(value) or any(ch.isspace() for ch in value):
        raise LightningAddressInvalidError("lightning_address_local_part_invalid")
    if value in {".", ".."} or ".." in value or value.startswith((".", "-", "_")) or value.endswith((".", "-", "_")):
        raise LightningAddressInvalidError("lightning_address_local_part_invalid")
    if any(token in value for token in ("/", "\\", "%2f", "%5c", "~")):
        raise LightningAddressInvalidError("lightning_address_local_part_invalid")
    if is_reserved_lightning_local_part(value):
        raise LightningAddressReservedError("lightning_address_reserved")
    if _LOCAL_PART_RE.fullmatch(value) is None:
        raise LightningAddressInvalidError("lightning_address_local_part_invalid")


def is_reserved_lightning_local_part(value: str) -> bool:
    normalized = unicodedata.normalize("NFC", value.strip()).lower()
    return normalized in RESERVED_LIGHTNING_LOCAL_PARTS or normalized.startswith(("admin-", "system-", "internal-"))


def is_valid_product_local_part(value: str) -> bool:
    try:
        return normalize_local_part(value) in PRODUCT_LIGHTNING_LOCAL_PARTS
    except LightningAddressInvalidError:
        return False


def resolve_product_code(local_part: str) -> str:
    normalized = normalize_local_part(local_part)
    try:
        return PRODUCT_LIGHTNING_LOCAL_PARTS[normalized]
    except KeyError as exc:
        raise LightningAddressInvalidError("lightning_address_product_unknown") from exc


__all__ = [
    "LightningAddressTargetType",
    "LightningAddressStatus",
    "LightningAddressDomainStatus",
    "LightningAddressVisibility",
    "LightningAddressDomainClass",
    "LightningAddressRecord",
    "LightningAddressInvalidError",
    "LightningAddressReservedError",
    "LightningAddressDomainInvalidError",
    "normalize_lightning_address",
    "normalize_local_part",
    "normalize_lightning_domain",
    "split_lightning_address",
    "build_lightning_address",
    "validate_lightning_address_local_part",
    "is_reserved_lightning_local_part",
    "is_valid_product_local_part",
    "resolve_product_code",
]
