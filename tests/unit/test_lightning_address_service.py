from datetime import UTC, datetime, timedelta

import pytest

from app.domain.lnurl.lightning_address import (
    LightningAddressInvalidError,
    LightningAddressReservedError,
    LightningAddressTargetType,
    normalize_lightning_address,
    resolve_product_code,
)
from app.services.access.crypto.hashing import sha256_prefixed
from app.services.lnurl.lightning_address_domain_policy import LightningAddressDomainPolicy, LightningAddressDomainPolicyConfig
from app.services.lnurl.lightning_address_service import (
    LightningAddressDisabledError,
    LightningAddressPolicyDeniedError,
    LightningAddressService,
    LightningAddressServiceConfig,
    LightningAddressSuspendedError,
)

NOW = datetime(2026, 7, 18, tzinfo=UTC)


class Revocations:
    def __init__(self) -> None:
        self.revoked: set[tuple[str, str]] = set()
    def is_revoked(self, *, target_type: str, target_hash: str) -> bool:
        return (target_type, target_hash) in self.revoked


def service(**kwargs) -> LightningAddressService:
    return LightningAddressService(config=LightningAddressServiceConfig(**kwargs), clock=lambda: NOW)


@pytest.mark.parametrize(
    ("raw", "normalized"),
    [("lite@BITCOIN-BASTION.COM", "lite@bitcoin-bastion.com"), ("Pro@bitcoin-bastion.com.", "pro@bitcoin-bastion.com")],
)
def test_valid_addresses_normalize(raw: str, normalized: str) -> None:
    assert normalize_lightning_address(raw) == normalized


@pytest.mark.parametrize("raw", ["@bitcoin-bastion.com", "lite@", "lite@@bitcoin-bastion.com", "lite @bitcoin-bastion.com", "../x@bitcoin-bastion.com", "lite/path@bitcoin-bastion.com", "lite@bad..domain", "a" * 65 + "@bitcoin-bastion.com", "admin@bitcoin-bastion.com", "lnurlp@bitcoin-bastion.com", "sovereign@bitcoin-bastion.com"])
def test_invalid_and_reserved_addresses_rejected(raw: str) -> None:
    with pytest.raises((LightningAddressInvalidError, LightningAddressReservedError)):
        normalize_lightning_address(raw)


def test_product_mappings_use_basic_pass_not_base_pass() -> None:
    assert resolve_product_code("lite") == "lite_pass"
    assert resolve_product_code("basic") == "basic_pass"
    assert resolve_product_code("plus") == "plus_pass"
    assert resolve_product_code("pro") == "pro_pass"
    assert resolve_product_code("business") == "business_pass"
    assert resolve_product_code("enterprise") == "enterprise_pass"


def test_product_resolution_reuses_lnurl_pay_request_service_and_issues_no_invoice_or_entitlement() -> None:
    svc = service(primary_domain="bitcoin-bastion.com")
    record = svc.create_product_address(local_part="pro")
    result = svc.resolve_address("pro@bitcoin-bastion.com")
    descriptor = result.to_internal_descriptor()
    assert descriptor["tag"] == "payRequest"
    assert descriptor["minSendable"] > 0
    assert descriptor["maxSendable"] >= descriptor["minSendable"]
    assert result.metadata_hash.startswith("sha256:")
    assert result.callback_reference.startswith("hmac-sha256:")
    assert "pr" not in descriptor
    assert "session" not in str(descriptor).lower()
    assert record.product_code == "pro_pass"
    assert svc.pay_request_service.repository.count_invoices() == 0
    assert svc.pay_request_service.repository.count_entitlements() == 0


def test_suspended_disabled_expired_and_revoked_addresses_fail_closed() -> None:
    svc = service()
    record = svc.create_product_address(local_part="lite")
    svc.suspend_address(record.address_id)
    with pytest.raises(LightningAddressSuspendedError):
        svc.resolve_address("lite@bitcoin-bastion.com")
    svc.reactivate_address(record.address_id)
    svc.disable_address(record.address_id)
    with pytest.raises(LightningAddressDisabledError):
        svc.resolve_address("lite@bitcoin-bastion.com")
    expiring = svc.create_business_invoice_address(local_part="invoice-1", domain="bitcoin-bastion.com", invoice_reference_hash=sha256_prefixed("invoice"), business_workspace_hash=sha256_prefixed("workspace"), expires_at=NOW - timedelta(seconds=1), display_label="Invoice")
    with pytest.raises(Exception):
        svc.resolve_address(expiring.normalized_address)


def test_revoked_domain_and_policy_denial_fail_closed() -> None:
    revocations = Revocations()
    svc = LightningAddressService(revocation_checker=revocations, config=LightningAddressServiceConfig(), clock=lambda: NOW)
    record = svc.create_product_address(local_part="plus")
    revocations.revoked.add(("lightning_address_domain", sha256_prefixed(record.domain)))
    with pytest.raises(LightningAddressPolicyDeniedError):
        svc.resolve_address(record.normalized_address)


def test_payregister_and_verified_custom_merchant_resolution_safe() -> None:
    domain_policy = LightningAddressDomainPolicy(LightningAddressDomainPolicyConfig(verified_custom_domains=frozenset({"merchant.example"})))
    svc = LightningAddressService(domain_policy=domain_policy, config=LightningAddressServiceConfig(allowed_custom_domains=frozenset({"merchant.example"})), clock=lambda: NOW)
    store = svc.create_payregister_store_address(local_part="store-123", store_reference_hash=sha256_prefixed("store-db-id"), display_label="Store")
    merchant = svc.create_merchant_address(local_part="terminal-03", domain="merchant.example", merchant_reference_hash=sha256_prefixed("merchant-db-id"), display_label="Merchant")
    store_descriptor = svc.resolve_address(store.normalized_address).to_internal_descriptor()
    merchant_descriptor = svc.resolve_address(merchant.normalized_address).to_internal_descriptor()
    assert store.target_type is LightningAddressTargetType.PAYREGISTER_STORE
    assert "store-db-id" not in str(store_descriptor)
    assert "merchant-db-id" not in str(merchant_descriptor)
    assert store_descriptor["commentAllowed"] == 120
    assert merchant_descriptor["target_type"] == "merchant"
