"""Domain policy for Lightning Address resolution."""
from __future__ import annotations

from dataclasses import dataclass

from app.domain.lnurl.lightning_address import LightningAddressDomainClass, LightningAddressDomainInvalidError, LightningAddressDomainStatus, normalize_lightning_domain


@dataclass(frozen=True, slots=True)
class LightningAddressDomainPolicyConfig:
    primary_domain: str = "bitcoin-bastion.com"
    first_party_domains: frozenset[str] = frozenset({"bitcoin-bastion.com"})
    payregister_domains: frozenset[str] = frozenset({"payregister.bitcoin-bastion.com"})
    verified_custom_domains: frozenset[str] = frozenset()
    onion_domains: frozenset[str] = frozenset()
    allow_onion_addresses: bool = False


@dataclass(frozen=True, slots=True)
class LightningAddressDomainDecision:
    domain: str
    domain_class: LightningAddressDomainClass
    status: LightningAddressDomainStatus
    https_required: bool
    reason_code: str = "allowed"


class LightningAddressDomainPolicy:
    def __init__(self, config: LightningAddressDomainPolicyConfig | None = None) -> None:
        self.config = config or LightningAddressDomainPolicyConfig()

    def classify(self, domain: str) -> LightningAddressDomainDecision:
        normalized = normalize_lightning_domain(domain)
        first_party = {normalize_lightning_domain(item) for item in self.config.first_party_domains | {self.config.primary_domain}}
        payregister = {normalize_lightning_domain(item) for item in self.config.payregister_domains}
        custom = {normalize_lightning_domain(item) for item in self.config.verified_custom_domains}
        onion = {normalize_lightning_domain(item) for item in self.config.onion_domains}
        if normalized in first_party:
            return LightningAddressDomainDecision(normalized, LightningAddressDomainClass.BASTION_PRODUCT_DOMAIN, LightningAddressDomainStatus.ACTIVE, True)
        if normalized in payregister:
            return LightningAddressDomainDecision(normalized, LightningAddressDomainClass.BASTION_PAYREGISTER_DOMAIN, LightningAddressDomainStatus.ACTIVE, True)
        if normalized in custom:
            return LightningAddressDomainDecision(normalized, LightningAddressDomainClass.VERIFIED_MERCHANT_DOMAIN, LightningAddressDomainStatus.ACTIVE, True)
        if normalized.endswith(".onion") and self.config.allow_onion_addresses and normalized in onion:
            return LightningAddressDomainDecision(normalized, LightningAddressDomainClass.ONION_PRIVACY_DOMAIN, LightningAddressDomainStatus.ACTIVE, False)
        return LightningAddressDomainDecision(normalized, LightningAddressDomainClass.UNSUPPORTED_DOMAIN, LightningAddressDomainStatus.PENDING_VERIFICATION, True, "domain_not_verified")

    def require_active(self, domain: str) -> LightningAddressDomainDecision:
        decision = self.classify(domain)
        if decision.status is not LightningAddressDomainStatus.ACTIVE or decision.domain_class is LightningAddressDomainClass.UNSUPPORTED_DOMAIN:
            raise LightningAddressDomainInvalidError(decision.reason_code)
        return decision


__all__ = ["LightningAddressDomainPolicyConfig", "LightningAddressDomainDecision", "LightningAddressDomainPolicy"]
