"""Product Lightning Address registry for Bitcoin Bastion subscriptions.

Product Lightning Addresses are payment-routing aliases only. They are not
identity, authentication, authorization, recovery factors, or entitlement proof.
"""
from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from app.domain.access.plans import PlanCode, normalize_plan_code
from app.domain.lnurl.lightning_address import LightningAddressInvalidError, build_lightning_address, normalize_local_part
from app.services.access.crypto.hashing import hash_canonical_json_prefixed
from app.services.lnurl.pay.metadata_provider import LNURLPayMetadataResult

_PRODUCT_NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9_-]{0,62}[a-z0-9])?$")
SAFE_PRODUCT_ERROR = {"status": "ERROR", "reason": "Lightning Address product is unavailable."}


class ProductAddressError(ValueError):
    reason_code = "lnurl_product_address_error"


class ProductAddressConfigError(ProductAddressError):
    reason_code = "lnurl_product_address_config_invalid"


class ProductAddressUnavailableError(ProductAddressError):
    reason_code = "lnurl_product_address_unavailable"


class ProductBillingPeriod(StrEnum):
    ONE_TIME = "one_time"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    CUSTOM = "custom"


class ProductAddressStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"
    SUSPENDED = "suspended"
    DEPRECATED = "deprecated"
    CONTRACT_ONLY = "contract_only"


@dataclass(frozen=True, slots=True)
class ProductLightningAddressAlias:
    alias: str
    canonical_name: str
    deprecated: bool = False


@dataclass(frozen=True, slots=True)
class ProductPaymentConfiguration:
    amount_msat: int | None
    currency: str
    billing_period: ProductBillingPeriod
    pricing_version: str
    product_configuration_hash: str


@dataclass(frozen=True, slots=True)
class ProductLightningAddress:
    schema_version: int
    canonical_name: str
    domain: str
    plan_code: PlanCode
    billing_period: ProductBillingPeriod
    amount_msat: int | None
    currency: str
    short_description: str
    long_description: str
    payer_data_policy: Mapping[str, str]
    success_action_policy: Mapping[str, str]
    comment_allowed: int
    status: ProductAddressStatus
    aliases: tuple[ProductLightningAddressAlias, ...]
    product_catalog_epoch: int
    policy_identifier: str
    product_configuration_hash: str

    @property
    def enabled(self) -> bool:
        return self.status is ProductAddressStatus.ACTIVE

    @property
    def normalized_address(self) -> str:
        return build_lightning_address(self.canonical_name, self.domain)

    @property
    def plan_code_value(self) -> str:
        return self.plan_code.value

    def payment_configuration(self) -> ProductPaymentConfiguration:
        return ProductPaymentConfiguration(
            amount_msat=self.amount_msat,
            currency=self.currency,
            billing_period=self.billing_period,
            pricing_version=f"product-catalog-{self.product_catalog_epoch}",
            product_configuration_hash=self.product_configuration_hash,
        )

    def payer_data_declaration(self) -> dict[str, Any] | None:
        auth = self.payer_data_policy.get("auth", "disabled")
        if auth == "disabled":
            return None
        return {"auth": {"mandatory": auth == "required"}}

    def metadata_result(self) -> LNURLPayMetadataResult:
        entries = [
            ["text/plain", f"{self.short_description} — {self._billing_label()}"],
            ["text/long-desc", self.long_description],
            ["text/identifier", self.normalized_address],
        ]
        canonical = json.dumps(entries, ensure_ascii=False, separators=(",", ":"))
        return LNURLPayMetadataResult(
            metadata=canonical,
            metadata_hash=hash_canonical_json_prefixed(entries),
            text_plain=entries[0][1],
        )

    def _billing_label(self) -> str:
        return {
            ProductBillingPeriod.ONE_TIME: "one-time",
            ProductBillingPeriod.MONTHLY: "1 month",
            ProductBillingPeriod.QUARTERLY: "3 months",
            ProductBillingPeriod.ANNUAL: "1 year",
            ProductBillingPeriod.CUSTOM: "custom term",
        }[self.billing_period]


@dataclass(slots=True)
class ProductAddressMetrics:
    resolutions_total: dict[str, int] = field(default_factory=dict)
    resolution_failures_total: dict[str, int] = field(default_factory=dict)

    def record_resolution(self, *, product: str, result: str) -> None:
        key = f"{product}:{result}"
        self.resolutions_total[key] = self.resolutions_total.get(key, 0) + 1

    def record_failure(self, *, reason_category: str) -> None:
        self.resolution_failures_total[reason_category] = self.resolution_failures_total.get(reason_category, 0) + 1


class ProductLightningAddressRegistry:
    def __init__(self, *, version: int, domain: str, products: Mapping[str, ProductLightningAddress], aliases: Mapping[str, str], product_catalog_epoch: int = 1, metrics: ProductAddressMetrics | None = None) -> None:
        self.version = version
        self.domain = domain
        self.products = dict(products)
        self.aliases = dict(aliases)
        self.product_catalog_epoch = product_catalog_epoch
        self.metrics = metrics or ProductAddressMetrics()

    @classmethod
    def load_default(cls, path: str | Path = "config/lnurl_product_addresses.yaml") -> "ProductLightningAddressRegistry":
        return cls.from_yaml(Path(path).read_text(encoding="utf-8"))

    @classmethod
    def from_yaml(cls, text: str) -> "ProductLightningAddressRegistry":
        raw = yaml.safe_load(text) or {}
        if not isinstance(raw, dict):
            raise ProductAddressConfigError("product address config must be an object")
        return cls.from_mapping(raw)

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "ProductLightningAddressRegistry":
        version = _positive_int(raw.get("version"), "version")
        domain = str(raw.get("domain") or "").strip().lower()
        if not domain:
            raise ProductAddressConfigError("domain is required")
        product_catalog_epoch = _positive_int(raw.get("product_catalog_epoch", 1), "product_catalog_epoch")
        raw_products = raw.get("products")
        if not isinstance(raw_products, Mapping):
            raise ProductAddressConfigError("products must be a mapping")
        products: dict[str, ProductLightningAddress] = {}
        aliases: dict[str, str] = {}
        for key, value in raw_products.items():
            if not isinstance(value, Mapping):
                raise ProductAddressConfigError("product must be an object")
            product = cls._product_from_mapping(
                schema_version=version,
                domain=domain,
                key=str(key),
                raw=value,
                product_catalog_epoch=product_catalog_epoch,
            )
            if product.canonical_name in products:
                raise ProductAddressConfigError("duplicate product canonical name")
            if product.canonical_name in aliases:
                raise ProductAddressConfigError("canonical name collides with alias")
            products[product.canonical_name] = product
            for alias in product.aliases:
                if alias.alias in products or alias.alias in aliases:
                    raise ProductAddressConfigError("product alias collision")
                aliases[alias.alias] = product.canonical_name
        for required in ("lite", "basic", "plus", "pro", "business", "enterprise"):
            if required not in products:
                raise ProductAddressConfigError(f"missing product {required}")
        return cls(version=version, domain=domain, products=products, aliases=aliases, product_catalog_epoch=product_catalog_epoch)

    @classmethod
    def _product_from_mapping(
        cls,
        *,
        schema_version: int,
        domain: str,
        key: str,
        raw: Mapping[str, Any],
        product_catalog_epoch: int,
    ) -> ProductLightningAddress:
        canonical = validate_product_address_name(str(raw.get("canonical_name") or key))
        if canonical != validate_product_address_name(key):
            raise ProductAddressConfigError("product key must match canonical name")
        plan = normalize_plan_code(raw.get("plan_code", ""))
        billing_period = ProductBillingPeriod(str(raw.get("billing_period") or "monthly"))
        amount = raw.get("amount_msat")
        enabled = bool(raw.get("enabled", False))
        status_raw = str(raw.get("status") or ("active" if enabled else "disabled"))
        status = ProductAddressStatus(status_raw)
        if enabled and status is not ProductAddressStatus.ACTIVE:
            raise ProductAddressConfigError("enabled product must be active")
        if status is ProductAddressStatus.ACTIVE and (not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0):
            raise ProductAddressConfigError("active product amount_msat must be positive integer")
        if plan is PlanCode.ENTERPRISE and status is ProductAddressStatus.ACTIVE:
            raise ProductAddressConfigError("enterprise public payment must be explicitly disabled by default")
        metadata = raw.get("metadata")
        if not isinstance(metadata, Mapping):
            raise ProductAddressConfigError("metadata is required")
        short_description = str(metadata.get("short_description") or "").strip()
        long_description = str(metadata.get("long_description") or "").strip()
        if not short_description or not long_description:
            raise ProductAddressConfigError("metadata descriptions are required")
        payer_data = raw.get("payer_data") or {}
        if not isinstance(payer_data, Mapping):
            raise ProductAddressConfigError("payer_data must be a mapping")
        normalized_payer_data = _validate_payer_data_policy(payer_data)
        success_action = raw.get("success_action") or {}
        if not isinstance(success_action, Mapping):
            raise ProductAddressConfigError("success_action must be a mapping")
        comment_allowed = _non_negative_int(raw.get("comment_allowed", 0), "comment_allowed")
        alias_values = raw.get("aliases") or []
        if not isinstance(alias_values, list):
            raise ProductAddressConfigError("aliases must be a list")
        aliases = tuple(ProductLightningAddressAlias(validate_product_address_name(str(alias)), canonical) for alias in alias_values)
        fingerprint_payload = {
            "version": schema_version,
            "canonical_name": canonical,
            "domain": domain,
            "plan_code": plan.value,
            "billing_period": billing_period.value,
            "amount_msat": amount,
            "currency": str(raw.get("currency") or "BTC"),
            "metadata": {"short_description": short_description, "long_description": long_description},
            "payer_data": normalized_payer_data,
            "success_action": dict(success_action),
            "comment_allowed": comment_allowed,
            "status": status.value,
            "product_catalog_epoch": product_catalog_epoch,
        }
        return ProductLightningAddress(
            schema_version=schema_version,
            canonical_name=canonical,
            domain=domain,
            plan_code=plan,
            billing_period=billing_period,
            amount_msat=amount if isinstance(amount, int) else None,
            currency=str(raw.get("currency") or "BTC"),
            short_description=short_description,
            long_description=long_description,
            payer_data_policy=normalized_payer_data,
            success_action_policy={str(k): str(v) for k, v in success_action.items()},
            comment_allowed=comment_allowed,
            status=status,
            aliases=aliases,
            product_catalog_epoch=product_catalog_epoch,
            policy_identifier=f"lnurl_product_address_{canonical}_v{product_catalog_epoch}",
            product_configuration_hash=hash_canonical_json_prefixed(fingerprint_payload),
        )

    def resolve_product_lightning_address(self, name: str) -> ProductLightningAddress:
        local = validate_product_address_name(name)
        canonical = self.aliases.get(local, local)
        product = self.products.get(canonical)
        if product is None or not product.enabled:
            self.metrics.record_failure(reason_category="unavailable")
            raise ProductAddressUnavailableError("Lightning Address product is unavailable")
        if product.amount_msat is None or product.amount_msat <= 0:
            self.metrics.record_failure(reason_category="amount_unavailable")
            raise ProductAddressUnavailableError("Lightning Address product is unavailable")
        self.metrics.record_resolution(product=product.canonical_name, result="resolved")
        return product

    def get_any_product(self, name: str) -> ProductLightningAddress | None:
        local = validate_product_address_name(name)
        return self.products.get(self.aliases.get(local, local))

    def active_products(self) -> tuple[ProductLightningAddress, ...]:
        return tuple(product for product in self.products.values() if product.enabled)

    def pricing_map(self) -> dict[PlanCode, int]:
        return {product.plan_code: product.amount_msat for product in self.products.values() if product.enabled and product.amount_msat is not None}

    def disabled_plans(self) -> set[PlanCode]:
        return {product.plan_code for product in self.products.values() if not product.enabled}


def validate_product_address_name(value: str) -> str:
    if not isinstance(value, str):
        raise ProductAddressConfigError("product address name must be a string")
    try:
        normalized = normalize_local_part(value)
    except LightningAddressInvalidError as exc:
        raise ProductAddressConfigError("product address name is invalid") from exc
    if normalized != value:
        raise ProductAddressConfigError("product address name must already be lowercase canonical ASCII")
    if _PRODUCT_NAME_RE.fullmatch(normalized) is None:
        raise ProductAddressConfigError("product address name is invalid")
    return normalized


def resolve_product_lightning_address(name: str, registry: ProductLightningAddressRegistry | None = None) -> ProductLightningAddress:
    return (registry or ProductLightningAddressRegistry.load_default()).resolve_product_lightning_address(name)


def _positive_int(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ProductAddressConfigError(f"{field} must be a positive integer")
    return value


def _non_negative_int(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ProductAddressConfigError(f"{field} must be a non-negative integer")
    return value


def _validate_payer_data_policy(raw: Mapping[str, Any]) -> dict[str, str]:
    allowed_values = {"required", "optional", "disabled"}
    normalized = {
        "auth": str(raw.get("auth", "optional")),
        "identifier": str(raw.get("identifier", "disabled")),
        "name": str(raw.get("name", "disabled")),
        "email": str(raw.get("email", "disabled")),
    }
    if any(value not in allowed_values for value in normalized.values()):
        raise ProductAddressConfigError("invalid payer_data policy")
    if normalized["email"] == "required" or normalized["name"] == "required":
        raise ProductAddressConfigError("email and name must not be mandatory")
    return normalized


class ProductAddressMetadataProvider:
    def __init__(self, registry: ProductLightningAddressRegistry) -> None:
        self.registry = registry

    def build_subscription_metadata(
        self,
        *,
        plan_code: PlanCode | str,
        product_code: str,
        billing_period: str,
        locale: str | None,
        pricing_version: str,
    ) -> LNURLPayMetadataResult:
        del billing_period, locale, pricing_version
        product = self.registry.get_any_product(product_code)
        if product is None:
            product = next((candidate for candidate in self.registry.products.values() if candidate.plan_code == normalize_plan_code(plan_code)), None)
        if product is None:
            raise ProductAddressUnavailableError("Lightning Address product is unavailable")
        return product.metadata_result()
