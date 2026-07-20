"""Host-aware Merchant Lightning Address resolver."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol
from urllib.parse import urlparse

from app.domain.lnurl.merchant_addresses import MerchantAddressTargetType, MerchantDomainStatus, MerchantLightningAddress, MerchantLightningAddressStatus, normalize_merchant_domain, normalize_merchant_local_part
from app.services.access.crypto.hashing import sha256_prefixed
from app.services.lnurl.merchant_address_audit import InMemoryMerchantAddressAudit
from app.services.lnurl.merchant_address_policy import AllowMerchantAddressPolicy, MerchantAddressPolicyHook
from app.services.lnurl.merchant_address_service import MerchantAddressService
from app.services.lnurl.merchant_metadata import build_merchant_metadata
from app.services.lnurl.pay.subscription_request_service import LNURLPayRequestResult


class MerchantAddressRevocationChecker(Protocol):
    def is_revoked(self, target_type: str, target_hash: str) -> bool: ...


class MerchantSettlementHealthChecker(Protocol):
    def is_healthy(self, settlement_mode: str, target_hash: str) -> bool: ...


class NoopMerchantRevocationChecker:
    def is_revoked(self, target_type: str, target_hash: str) -> bool:
        return False


class HealthySettlementChecker:
    def is_healthy(self, settlement_mode: str, target_hash: str) -> bool:
        return True


@dataclass(frozen=True, slots=True)
class MerchantAddressResolverConfig:
    callback_base_url: str = "https://payregister.bitcoin-bastion.com"
    allowed_hosts: frozenset[str] = frozenset({"payregister.bitcoin-bastion.com"})
    cache_ttl_seconds: int = 60


class MerchantAddressResolutionError(ValueError):
    reason_code = "merchant_address_resolution_failed"


class MerchantAddressResolver:
    def __init__(self, *, address_service: MerchantAddressService, policy_hook: MerchantAddressPolicyHook | None = None, revocation_checker: MerchantAddressRevocationChecker | None = None, settlement_health: MerchantSettlementHealthChecker | None = None, audit: InMemoryMerchantAddressAudit | None = None, config: MerchantAddressResolverConfig | None = None) -> None:
        self.address_service = address_service
        self.policy_hook = policy_hook or AllowMerchantAddressPolicy()
        self.revocation_checker = revocation_checker or NoopMerchantRevocationChecker()
        self.settlement_health = settlement_health or HealthySettlementChecker()
        self.audit = audit or address_service.audit
        self.config = config or MerchantAddressResolverConfig()

    def resolve_host_local_part(self, *, host: str, local_part: str) -> LNURLPayRequestResult:
        domain = normalize_merchant_domain(_clean_host(host))
        if self.config.allowed_hosts and domain not in self.config.allowed_hosts:
            self.audit.emit("merchant_ln_address_resolution_failed", {"domain_hash": sha256_prefixed(domain), "reason_code": "unknown_host"})
            raise MerchantAddressResolutionError("Merchant Lightning Address unavailable")
        merchant_domain = self.address_service.domain_service.repository.get_by_domain(domain, self.address_service.domain_service.pepper)
        if merchant_domain is None or merchant_domain.status != MerchantDomainStatus.ACTIVE:
            self.audit.emit("merchant_ln_address_resolution_failed", {"domain_hash": sha256_prefixed(domain), "reason_code": "domain_not_active"})
            raise MerchantAddressResolutionError("Merchant Lightning Address unavailable")
        address = self.address_service.repository.get_by_domain_local(merchant_domain.domain_id, normalize_merchant_local_part(local_part))
        if address is None:
            self.audit.emit("merchant_ln_address_resolution_failed", {"domain_hash": merchant_domain.domain_hash, "reason_code": "alias_not_found"})
            raise MerchantAddressResolutionError("Merchant Lightning Address unavailable")
        self._validate_address(address)
        metadata = build_merchant_metadata(address)
        callback_ref = sha256_prefixed(f"merchant:{address.address_id}:{metadata.metadata_hash}")
        callback = f"{self._trusted_callback_base()}/api/v1/payregister/lnurl/pay/callback/{callback_ref.split(':', 1)[1][:32]}"
        self.audit.emit("merchant_ln_address_resolved", {"address_hash": address.local_part_hash, "domain_hash": merchant_domain.domain_hash, "workspace_hash": address.workspace_id_hash, "target_type": address.target_type.value})
        return LNURLPayRequestResult(
            request_id=callback_ref,
            tag="payRequest",
            callback=callback,
            min_sendable_msat=address.min_sendable_msat,
            max_sendable_msat=address.max_sendable_msat,
            metadata=metadata.canonical_json,
            expires_at=datetime.now(UTC) + timedelta(seconds=self.config.cache_ttl_seconds),
            status="resolved",
            comment_allowed=address.comment_allowed,
            payer_data={"auth": {"mandatory": False}} if address.payer_data_policy_id else None,
            product_code="merchant_lightning_address",
            plan_code=address.target_type.value,
            payment_context_hash=sha256_prefixed(address.address_id),
            metadata_hash=metadata.metadata_hash,
        )

    def _validate_address(self, address: MerchantLightningAddress) -> None:
        now = datetime.now(UTC)
        if address.status != MerchantLightningAddressStatus.ACTIVE or address.revoked_at is not None or (address.expires_at and address.expires_at <= now):
            raise MerchantAddressResolutionError("Merchant Lightning Address unavailable")
        if self.revocation_checker.is_revoked("merchant_lightning_address", address.local_part_hash):
            raise MerchantAddressResolutionError("Merchant Lightning Address unavailable")
        if self.revocation_checker.is_revoked("merchant_address_target", address.target_id_hash):
            raise MerchantAddressResolutionError("Merchant Lightning Address unavailable")
        if address.target_type == MerchantAddressTargetType.CASHIER_SHIFT and address.expires_at and address.expires_at <= now:
            raise MerchantAddressResolutionError("Merchant Lightning Address unavailable")
        if not self.settlement_health.is_healthy(address.settlement_mode.value, address.target_id_hash):
            raise MerchantAddressResolutionError("Payment endpoint temporarily unavailable")
        decision = self.policy_hook.evaluate("merchant_address:resolve", {"workspace_hash": address.workspace_id_hash, "target_type": address.target_type.value, "status": address.status.value})
        if not decision.allowed:
            raise MerchantAddressResolutionError("Merchant Lightning Address unavailable")

    def _trusted_callback_base(self) -> str:
        parsed = urlparse(self.config.callback_base_url)
        if parsed.scheme != "https" or not parsed.hostname or (self.config.allowed_hosts and parsed.hostname.lower() not in self.config.allowed_hosts):
            raise MerchantAddressResolutionError("Merchant callback host unavailable")
        return self.config.callback_base_url.rstrip("/")


def _clean_host(host: str) -> str:
    raw_host = (host or "").strip().lower()
    if "," in raw_host:
        raise MerchantAddressResolutionError("Merchant host unavailable")
    first = raw_host.split(":", 1)[0]
    if not first or any(ch in first for ch in ("/", "\\", "@", "?", "#")):
        raise MerchantAddressResolutionError("Merchant host unavailable")
    return first
