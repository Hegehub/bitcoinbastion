"""Business Merchant Lightning Address management endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.domain.lnurl.merchant_addresses import MerchantAddressSettlementMode, MerchantAddressTargetType, MerchantDomainVerificationMethod
from app.schemas.merchant_lightning_address import MerchantLightningAddressCreate, MerchantLightningDomainCreate
from app.services.lnurl.merchant_address_service import MerchantAddressService
from app.services.lnurl.merchant_domain_service import MerchantDomainService

router = APIRouter(prefix="/business", tags=["Merchant Lightning Address"])
_domain_service = MerchantDomainService()
_address_service = MerchantAddressService(domain_service=_domain_service)


def _domain_response(domain: Any) -> dict[str, Any]:
    return {
        "domain_id": domain.domain_id,
        "normalized_domain": domain.normalized_domain,
        "workspace_id_hash": domain.workspace_id_hash,
        "status": domain.status.value,
        "verification_method": domain.verification_method.value,
        "verified_at": domain.verified_at.isoformat() if domain.verified_at else None,
        "verification_expires_at": domain.verification_expires_at.isoformat() if domain.verification_expires_at else None,
    }


def _address_response(address: Any) -> dict[str, Any]:
    return {
        "address_id": address.address_id,
        "normalized_address": address.normalized_address,
        "workspace_id_hash": address.workspace_id_hash,
        "target_type": address.target_type.value,
        "status": address.status.value,
        "visibility": address.visibility.value,
        "settlement_mode": address.settlement_mode.value,
        "min_sendable_msat": address.min_sendable_msat,
        "max_sendable_msat": address.max_sendable_msat,
        "comment_allowed": address.comment_allowed,
    }


@router.post("/lightning-domains")
def create_domain(payload: MerchantLightningDomainCreate) -> dict[str, Any]:
    domain = _domain_service.create_domain(normalized_domain=payload.normalized_domain, workspace_id_hash=payload.workspace_id_hash, verification_method=MerchantDomainVerificationMethod(payload.verification_method), bastion_managed_domains=frozenset({"payregister.bitcoin-bastion.com", "merchant.bitcoin-bastion.com", "pay.bitcoin-bastion.com"}))
    return _domain_response(domain)


@router.get("/lightning-domains")
def list_domains() -> dict[str, Any]:
    return {"items": [_domain_response(domain) for domain in _domain_service.repository.list()]}


@router.get("/lightning-domains/{domain_id}")
def get_domain(domain_id: str) -> dict[str, Any]:
    return _domain_response(_domain_service._domain(domain_id))


@router.post("/lightning-domains/{domain_id}/verify")
def start_domain_verification(domain_id: str, method: str = "dns_txt") -> dict[str, Any]:
    challenge = _domain_service.start_verification(domain_id, MerchantDomainVerificationMethod(method))
    return {"dns_name": challenge.dns_name, "expected_value": challenge.expected_value, "expires_at": challenge.expires_at.isoformat(), "method": challenge.method.value}


@router.post("/lightning-domains/{domain_id}/recheck")
def recheck_domain(domain_id: str) -> dict[str, Any]:
    return _domain_response(_domain_service.mark_verified(domain_id))


@router.delete("/lightning-domains/{domain_id}")
def revoke_domain(domain_id: str) -> dict[str, Any]:
    return _domain_response(_domain_service.revoke_domain(domain_id))


@router.post("/lightning-addresses")
def create_address(payload: MerchantLightningAddressCreate) -> dict[str, Any]:
    address = _address_service.create_merchant_address(domain_id=payload.domain_id, local_part=payload.local_part, workspace_id_hash=payload.workspace_id_hash, target_type=MerchantAddressTargetType(payload.target_type), target_id_hash=payload.target_id_hash, settlement_mode=MerchantAddressSettlementMode(payload.settlement_mode), min_sendable_msat=payload.min_sendable_msat, max_sendable_msat=payload.max_sendable_msat, comment_allowed=payload.comment_allowed, display_label=payload.display_label, description=payload.description)
    return _address_response(address)


@router.get("/lightning-addresses")
def list_addresses() -> dict[str, Any]:
    return {"items": [_address_response(address) for address in _address_service.list_merchant_addresses()]}


@router.get("/lightning-addresses/{address_id}")
def get_address(address_id: str) -> dict[str, Any]:
    return _address_response(_address_service.get_merchant_address(address_id))


@router.post("/lightning-addresses/{address_id}/activate")
def activate_address(address_id: str) -> dict[str, Any]:
    return _address_response(_address_service.activate_merchant_address(address_id))


@router.post("/lightning-addresses/{address_id}/suspend")
def suspend_address(address_id: str) -> dict[str, Any]:
    return _address_response(_address_service.suspend_merchant_address(address_id))


@router.delete("/lightning-addresses/{address_id}")
def revoke_address(address_id: str) -> dict[str, Any]:
    return _address_response(_address_service.revoke_merchant_address(address_id))


__all__ = ["router", "_domain_service", "_address_service"]
