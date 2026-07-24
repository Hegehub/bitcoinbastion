"""Merchant Lightning Address management service."""
from __future__ import annotations

import secrets
from dataclasses import replace
from datetime import UTC, datetime

from app.domain.lnurl.merchant_addresses import (
    MerchantAddressSettlementMode,
    MerchantAddressTargetType,
    MerchantAddressVisibility,
    MerchantDomainStatus,
    MerchantLightningAddress,
    MerchantLightningAddressStatus,
    normalize_merchant_local_part,
)
from app.services.access.crypto.hashing import hmac_sha256_prefixed
from app.services.lnurl.merchant_address_audit import InMemoryMerchantAddressAudit
from app.services.lnurl.merchant_address_policy import AllowMerchantAddressPolicy, MerchantAddressPolicyHook
from app.services.lnurl.merchant_domain_service import MerchantDomainService


class MerchantAddressError(ValueError):
    reason_code = "merchant_address_error"


class MerchantAddressUnavailable(MerchantAddressError):
    reason_code = "merchant_address_unavailable"


class MerchantAddressConflict(MerchantAddressError):
    reason_code = "merchant_address_conflict"


class MerchantAddressPolicyDenied(MerchantAddressError):
    reason_code = "merchant_address_policy_denied"


class MerchantAddressRepository:
    def __init__(self) -> None:
        self.addresses_by_id: dict[str, MerchantLightningAddress] = {}
        self.address_id_by_domain_local: dict[tuple[str, str], str] = {}

    def create(self, address: MerchantLightningAddress) -> MerchantLightningAddress:
        key = (address.domain_id, address.normalized_local_part)
        if key in self.address_id_by_domain_local:
            raise MerchantAddressConflict("Merchant Lightning Address already exists")
        self.addresses_by_id[address.address_id] = address
        self.address_id_by_domain_local[key] = address.address_id
        return address

    def save(self, address: MerchantLightningAddress) -> MerchantLightningAddress:
        self.addresses_by_id[address.address_id] = address
        self.address_id_by_domain_local[(address.domain_id, address.normalized_local_part)] = address.address_id
        return address

    def get(self, address_id: str) -> MerchantLightningAddress | None:
        return self.addresses_by_id.get(address_id)

    def get_by_domain_local(self, domain_id: str, local_part: str) -> MerchantLightningAddress | None:
        address_id = self.address_id_by_domain_local.get((domain_id, local_part))
        return self.addresses_by_id.get(address_id) if address_id else None

    def list(self) -> list[MerchantLightningAddress]:
        return list(self.addresses_by_id.values())


class MerchantAddressService:
    def __init__(self, *, repository: MerchantAddressRepository | None = None, domain_service: MerchantDomainService | None = None, policy_hook: MerchantAddressPolicyHook | None = None, audit: InMemoryMerchantAddressAudit | None = None, pepper: str = "dev-merchant-ln-address-pepper-change-me") -> None:
        self.repository = repository or MerchantAddressRepository()
        self.domain_service = domain_service or MerchantDomainService()
        self.policy_hook = policy_hook or AllowMerchantAddressPolicy()
        self.audit = audit or self.domain_service.audit
        self.pepper = pepper

    def create_merchant_address(self, *, domain_id: str, local_part: str, workspace_id_hash: str, target_type: MerchantAddressTargetType, target_id_hash: str, settlement_mode: MerchantAddressSettlementMode = MerchantAddressSettlementMode.PAYREGISTER_NODE, min_sendable_msat: int = 1_000, max_sendable_msat: int = 100_000_000, comment_allowed: int = 0, visibility: MerchantAddressVisibility = MerchantAddressVisibility.PUBLIC, display_label: str = "Merchant", description: str | None = None, expires_at: datetime | None = None) -> MerchantLightningAddress:
        domain = self.domain_service._domain(domain_id)
        local = normalize_merchant_local_part(local_part)
        if domain.workspace_id_hash != workspace_id_hash:
            raise MerchantAddressPolicyDenied("Cross-workspace merchant address binding denied")
        if domain.status not in {MerchantDomainStatus.ACTIVE, MerchantDomainStatus.VERIFIED}:
            raise MerchantAddressPolicyDenied("Merchant domain must be verified before address creation")
        if min_sendable_msat <= 0 or max_sendable_msat < min_sendable_msat:
            raise MerchantAddressPolicyDenied("Invalid amount policy")
        decision = self.policy_hook.evaluate("merchant_address:create", {"workspace_hash": workspace_id_hash, "domain_hash": domain.domain_hash, "target_type": target_type.value, "settlement_mode": settlement_mode.value})
        if not decision.allowed:
            raise MerchantAddressPolicyDenied(decision.reason_code)
        now = datetime.now(UTC)
        address = MerchantLightningAddress(
            address_id=f"mla_{secrets.token_urlsafe(18)}",
            domain_id=domain_id,
            local_part_hash=hmac_sha256_prefixed(self.pepper, f"{domain.normalized_domain}:{local}"),
            normalized_local_part=local,
            normalized_domain=domain.normalized_domain,
            workspace_id_hash=workspace_id_hash,
            target_type=target_type,
            target_id_hash=target_id_hash,
            status=MerchantLightningAddressStatus.PENDING,
            visibility=visibility,
            settlement_mode=settlement_mode,
            lnurl_pay_profile_id="merchant_lnurl_pay_v1",
            metadata_template_id="merchant_lightning_address_v1",
            min_sendable_msat=min_sendable_msat,
            max_sendable_msat=max_sendable_msat,
            comment_allowed=comment_allowed,
            payer_data_policy_id="payerdata_auth_optional_no_pii_v1",
            success_action_policy_id="merchant_receipt_url_v1",
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
            display_label=display_label,
            description=description,
        )
        persisted = self.repository.create(address)
        self.audit.emit("merchant_ln_address_created", {"address_hash": persisted.local_part_hash, "domain_hash": domain.domain_hash, "workspace_hash": workspace_id_hash, "target_type": target_type.value})
        return persisted

    def activate_merchant_address(self, address_id: str) -> MerchantLightningAddress:
        address = self._address(address_id)
        domain = self.domain_service._domain(address.domain_id)
        if domain.status != MerchantDomainStatus.ACTIVE:
            raise MerchantAddressPolicyDenied("Merchant domain is not active")
        return self._save_status(address, MerchantLightningAddressStatus.ACTIVE, "merchant_ln_address_activated")

    def suspend_merchant_address(self, address_id: str) -> MerchantLightningAddress:
        return self._save_status(self._address(address_id), MerchantLightningAddressStatus.SUSPENDED, "merchant_ln_address_suspended")

    def revoke_merchant_address(self, address_id: str) -> MerchantLightningAddress:
        now = datetime.now(UTC)
        address = replace(self._address(address_id), status=MerchantLightningAddressStatus.REVOKED, revoked_at=now, updated_at=now)
        self.repository.save(address)
        self.audit.emit("merchant_ln_address_revoked", {"address_hash": address.local_part_hash})
        return address

    def rotate_merchant_address_target(self, address_id: str, *, target_type: MerchantAddressTargetType, target_id_hash: str) -> MerchantLightningAddress:
        address = self._address(address_id)
        updated = replace(address, target_type=target_type, target_id_hash=target_id_hash, updated_at=datetime.now(UTC))
        self.repository.save(updated)
        self.audit.emit("merchant_ln_address_target_rotated", {"address_hash": address.local_part_hash, "target_type": target_type.value})
        return updated

    def check_address_availability(self, *, domain_id: str, local_part: str) -> bool:
        return self.repository.get_by_domain_local(domain_id, normalize_merchant_local_part(local_part)) is None

    def get_merchant_address(self, address_id: str) -> MerchantLightningAddress:
        return self._address(address_id)

    def list_merchant_addresses(self) -> list[MerchantLightningAddress]:
        return self.repository.list()

    def _save_status(self, address: MerchantLightningAddress, status: MerchantLightningAddressStatus, event: str) -> MerchantLightningAddress:
        updated = replace(address, status=status, updated_at=datetime.now(UTC))
        self.repository.save(updated)
        self.audit.emit(event, {"address_hash": address.local_part_hash})
        return updated

    def _address(self, address_id: str) -> MerchantLightningAddress:
        address = self.repository.get(address_id)
        if address is None:
            raise MerchantAddressUnavailable("Merchant Lightning Address unavailable")
        return address
