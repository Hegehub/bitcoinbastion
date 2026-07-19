from datetime import UTC, datetime

import pytest

from app.domain.lnurl.lightning_address import LightningAddressRecord, LightningAddressStatus, LightningAddressTargetType, LightningAddressVisibility, build_lightning_address
from app.services.access.crypto.hashing import sha256_prefixed
from app.services.lnurl.lightning_address_repository import InMemoryLightningAddressRepository, LightningAddressConflictError

NOW = datetime(2026, 7, 18, tzinfo=UTC)


def record(local="lite", domain="bitcoin-bastion.com", status=LightningAddressStatus.ACTIVE) -> LightningAddressRecord:
    normalized = build_lightning_address(local, domain)
    return LightningAddressRecord(
        address_id=sha256_prefixed(normalized),
        local_part=local,
        domain=domain,
        normalized_address=normalized,
        target_type=LightningAddressTargetType.SUBSCRIPTION_PRODUCT,
        target_reference_hash=sha256_prefixed("lite_pass"),
        status=status,
        visibility=LightningAddressVisibility.PUBLIC,
        min_sendable_msat=1_000,
        max_sendable_msat=2_000,
        metadata_template_id="subscription_product_v1",
        callback_policy_id="callback_v1",
        payer_data_policy_id="payerdata_disabled_v1",
        success_action_policy_id="success_v1",
        comment_allowed=0,
        currency="BTC",
        created_at=NOW,
        updated_at=NOW,
        expires_at=None,
        version=1,
        schema_epoch=1,
        policy_epoch=1,
        product_code="lite_pass",
    )


def test_unique_normalized_address_enforced_and_idempotent_same_record() -> None:
    repo = InMemoryLightningAddressRepository()
    item = record()
    assert repo.create_address(item) == item
    assert repo.create_address(item) == item
    with pytest.raises(LightningAddressConflictError):
        repo.create_address(record(status=LightningAddressStatus.SUSPENDED))


def test_repository_lookup_lists_and_state_transitions() -> None:
    repo = InMemoryLightningAddressRepository()
    item = repo.create_address(record())
    assert repo.address_exists(item.normalized_address)
    assert repo.get_by_local_part_and_domain("LITE", "BITCOIN-BASTION.COM") == item
    assert repo.list_by_target(LightningAddressTargetType.SUBSCRIPTION_PRODUCT, item.target_reference_hash) == (item,)
    assert repo.list_by_domain("bitcoin-bastion.com") == (item,)
    suspended = repo.suspend_address(item.address_id, "test")
    assert suspended.status is LightningAddressStatus.SUSPENDED
    reactivated = repo.reactivate_address(item.address_id)
    assert reactivated.status is LightningAddressStatus.ACTIVE
    disabled = repo.disable_address(item.address_id, "test")
    assert disabled.status is LightningAddressStatus.DISABLED
    expired = repo.expire_address(item.address_id)
    assert expired.status is LightningAddressStatus.EXPIRED


def test_reserve_and_release_local_part() -> None:
    repo = InMemoryLightningAddressRepository()
    repo.reserve_local_part("store-1", "payregister.bitcoin-bastion.com")
    with pytest.raises(LightningAddressConflictError):
        repo.reserve_local_part("store-1", "payregister.bitcoin-bastion.com")
    repo.release_local_part("store-1", "payregister.bitcoin-bastion.com")
    repo.reserve_local_part("store-1", "payregister.bitcoin-bastion.com")
