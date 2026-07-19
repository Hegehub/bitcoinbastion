from __future__ import annotations

import pytest

from app.domain.access.plans import PlanCode
from app.services.lnurl.product_addresses import (
    ProductAddressConfigError,
    ProductAddressUnavailableError,
    ProductLightningAddressRegistry,
    validate_product_address_name,
)


def registry() -> ProductLightningAddressRegistry:
    return ProductLightningAddressRegistry.load_default()


@pytest.mark.parametrize(
    ("name", "plan"),
    [
        ("lite", PlanCode.LITE),
        ("basic", PlanCode.BASIC),
        ("plus", PlanCode.PLUS),
        ("pro", PlanCode.PRO),
        ("business", PlanCode.BUSINESS),
    ],
)
def test_product_addresses_resolve_to_canonical_plans(name: str, plan: PlanCode) -> None:
    product = registry().resolve_product_lightning_address(name)
    assert product.plan_code is plan
    assert product.normalized_address == f"{name}@bitcoin-bastion.com"
    assert product.payment_configuration().amount_msat == product.amount_msat
    assert product.product_configuration_hash.startswith("sha256:")


def test_enterprise_is_contract_only_and_unavailable_by_default() -> None:
    with pytest.raises(ProductAddressUnavailableError):
        registry().resolve_product_lightning_address("enterprise")
    enterprise = registry().products["enterprise"]
    assert enterprise.plan_code is PlanCode.ENTERPRISE
    assert enterprise.enabled is False
    assert enterprise.status.value == "contract_only"


def test_aliases_resolve_to_canonical_product() -> None:
    raw = {
        "version": 1,
        "domain": "bitcoin-bastion.com",
        "products": {
            **{k: _product(k, v) for k, v in {"lite": "lite_pass", "basic": "basic_pass", "plus": "plus_pass", "pro": "pro_pass", "business": "business_pass"}.items()},
            "enterprise": _product("enterprise", "enterprise_pass", enabled=False, status="contract_only", amount=None, billing="custom"),
        },
    }
    raw["products"]["pro"]["aliases"] = ["professional"]
    reg = ProductLightningAddressRegistry.from_mapping(raw)
    product = reg.resolve_product_lightning_address("professional")
    assert product.canonical_name == "pro"
    assert product.plan_code is PlanCode.PRO


def test_product_name_safety_rejects_dangerous_inputs() -> None:
    for value in ("../pro", "%2e%2e/pro", "Pro", "pro@example", "pro/annual", "рro", "business admin"):
        with pytest.raises(ProductAddressConfigError):
            validate_product_address_name(value)


def _product(name: str, plan: str, *, enabled: bool = True, status: str | None = None, amount: int | None = 1000, billing: str = "monthly") -> dict:
    return {
        "enabled": enabled,
        "status": status or ("active" if enabled else "disabled"),
        "canonical_name": name,
        "aliases": [],
        "plan_code": plan,
        "billing_period": billing,
        "amount_msat": amount,
        "currency": "BTC",
        "metadata": {"short_description": f"{name} short", "long_description": f"{name} long"},
        "payer_data": {"auth": "optional", "identifier": "disabled", "name": "disabled", "email": "disabled"},
        "success_action": {"type": "url", "description": "Open"},
    }
