"""Pure LNURL security vocabulary and policy-hint types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.lnurl.auth import BastionLNURLIntentAction


class LNURLSecurityLevel(StrEnum):
    COMPATIBILITY = "compatibility"
    STANDARD = "standard"
    HIGH_ASSURANCE = "high_assurance"
    BUSINESS = "business"
    SOVEREIGN = "sovereign"


class LNURLRiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


LNURL_LOW_RISK_ACTIONS = frozenset(
    {
        BastionLNURLIntentAction.PRINCIPAL_REGISTER,
        BastionLNURLIntentAction.PRINCIPAL_LOGIN,
        BastionLNURLIntentAction.PRINCIPAL_LINK,
        BastionLNURLIntentAction.SESSION_CREATE,
    }
)
LNURL_HIGH_RISK_ACTIONS = frozenset(
    {
        BastionLNURLIntentAction.DEVICE_ADD,
        BastionLNURLIntentAction.CREATE_API_KEY,
        BastionLNURLIntentAction.INCREASE_SCOPE,
        BastionLNURLIntentAction.RECOVERY_COMPLETE,
        BastionLNURLIntentAction.LOCKDOWN_RELEASE,
    }
)
LNURL_CRITICAL_ACTIONS = frozenset(
    {
        BastionLNURLIntentAction.BUSINESS_ROLE_CHANGE,
        BastionLNURLIntentAction.PAYREGISTER_OWNER_ACTION,
        BastionLNURLIntentAction.PAYREGISTER_ADMIN_ENABLE,
        BastionLNURLIntentAction.ENTERPRISE_POLICY_CHANGE,
        BastionLNURLIntentAction.EXPORT_DATA,
        BastionLNURLIntentAction.CREATE_DELEGATED_PASS,
        BastionLNURLIntentAction.TREASURY_POLICY_CHANGE,
        BastionLNURLIntentAction.RECOVERY_CHANGE,
        BastionLNURLIntentAction.DEVICE_REVOKE,
        BastionLNURLIntentAction.BUSINESS_ROLE_ASSIGNMENT,
        BastionLNURLIntentAction.PAYREGISTER_DEVICE_ENROLL,
        BastionLNURLIntentAction.OFFLINE_PACK_ISSUE,
        BastionLNURLIntentAction.REFUND_APPROVE,
        BastionLNURLIntentAction.PAYOUT_APPROVE,
    }
)


class LNURLTransportScheme(StrEnum):
    HTTPS = "https"
    HTTP_ONION = "http_onion"


class LNURLDomainClass(StrEnum):
    BASTION_AUTH = "bastion_auth"
    BASTION_PAYMENT = "bastion_payment"
    PAYREGISTER = "payregister"
    MERCHANT_CUSTOM = "merchant_custom"
    ONION_SERVICE = "onion_service"
    DEVELOPMENT = "development"


class LNURLDomainStatus(StrEnum):
    ACTIVE = "active"
    MIGRATION_PENDING = "migration_pending"
    DEPRECATED = "deprecated"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


@dataclass(frozen=True, slots=True)
class LNURLDomainPolicy:
    domain: str
    domain_class: LNURLDomainClass
    status: LNURLDomainStatus
    allowed_schemes: tuple[LNURLTransportScheme, ...]
    allow_cors_get: bool
    stable_auth_domain: bool
    policy_version: int
    migration_target: str | None = None

    def __post_init__(self) -> None:
        if not self.domain.strip():
            raise ValueError("lnurl_domain_required")
        if self.policy_version < 1:
            raise ValueError("lnurl_policy_version_required")
        if LNURLTransportScheme.HTTP_ONION in self.allowed_schemes and self.domain_class is not LNURLDomainClass.ONION_SERVICE:
            raise ValueError("lnurl_http_onion_requires_onion_domain_class")


def is_high_risk_lnurl_action(action: BastionLNURLIntentAction | str) -> bool:
    normalized = BastionLNURLIntentAction(action)
    return normalized in LNURL_HIGH_RISK_ACTIONS or normalized in LNURL_CRITICAL_ACTIONS


def lnurl_action_risk_level(action: BastionLNURLIntentAction | str) -> LNURLRiskLevel:
    normalized = BastionLNURLIntentAction(action)
    if normalized in LNURL_CRITICAL_ACTIONS:
        return LNURLRiskLevel.CRITICAL
    if normalized in LNURL_HIGH_RISK_ACTIONS:
        return LNURLRiskLevel.HIGH
    return LNURLRiskLevel.LOW
