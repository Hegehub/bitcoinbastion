from __future__ import annotations

import copy

import pytest

from app.services.lnurl.product_addresses import ProductAddressConfigError, ProductLightningAddressRegistry


def base_config() -> dict:
    products = {}
    for name, plan in {
        "lite": "lite_pass",
        "basic": "basic_pass",
        "plus": "plus_pass",
        "pro": "pro_pass",
        "business": "business_pass",
        "enterprise": "enterprise_pass",
    }.items():
        products[name] = {
            "enabled": name != "enterprise",
            "status": "contract_only" if name == "enterprise" else "active",
            "canonical_name": name,
            "aliases": [],
            "plan_code": plan,
            "billing_period": "custom" if name == "enterprise" else "monthly",
            "amount_msat": None if name == "enterprise" else 1000,
            "currency": "BTC",
            "metadata": {"short_description": f"{name} short", "long_description": f"{name} long"},
            "payer_data": {"auth": "optional", "identifier": "disabled", "name": "disabled", "email": "disabled"},
            "success_action": {"type": "url", "description": "Open"},
        }
    return {"version": 1, "domain": "bitcoin-bastion.com", "products": products}


def test_default_config_loads_and_has_stable_hashes() -> None:
    registry = ProductLightningAddressRegistry.load_default()
    assert registry.version == 1
    assert registry.products["basic"].plan_code.value == "basic_pass"
    assert registry.products["basic"].product_configuration_hash == ProductLightningAddressRegistry.load_default().products["basic"].product_configuration_hash


def test_alias_collision_fails_configuration_validation() -> None:
    raw = base_config()
    raw["products"]["pro"]["aliases"] = ["basic"]
    with pytest.raises(ProductAddressConfigError):
        ProductLightningAddressRegistry.from_mapping(raw)


def test_unknown_plan_and_missing_amount_fail_closed() -> None:
    raw = base_config()
    raw["products"]["basic"]["plan_code"] = "base_pass"
    with pytest.raises(Exception):
        ProductLightningAddressRegistry.from_mapping(raw)
    raw = base_config()
    raw["products"]["basic"]["amount_msat"] = None
    with pytest.raises(ProductAddressConfigError):
        ProductLightningAddressRegistry.from_mapping(raw)


def test_enterprise_cannot_be_active_in_default_registry() -> None:
    raw = base_config()
    raw["products"]["enterprise"]["enabled"] = True
    raw["products"]["enterprise"]["status"] = "active"
    raw["products"]["enterprise"]["amount_msat"] = 1000
    with pytest.raises(ProductAddressConfigError):
        ProductLightningAddressRegistry.from_mapping(raw)


def test_email_and_name_cannot_be_required() -> None:
    for field in ("email", "name"):
        raw = copy.deepcopy(base_config())
        raw["products"]["basic"]["payer_data"][field] = "required"
        with pytest.raises(ProductAddressConfigError):
            ProductLightningAddressRegistry.from_mapping(raw)
