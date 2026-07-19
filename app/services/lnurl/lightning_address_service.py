"""Lightning Address service for internal LNURL-pay descriptor routing.

This module intentionally does not expose ``/.well-known/lnurlp`` routes and
never issues invoices, sessions, principals, Payment Proofs, or entitlements at
address-resolution time.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol, cast

from app.domain.access.plans import PlanCode
from app.domain.lnurl.lightning_address import (
    LightningAddressRecord,
    LightningAddressStatus,
    LightningAddressTargetType,
    LightningAddressVisibility,
    build_lightning_address,
    normalize_lightning_address,
    resolve_product_code,
)
from app.services.access.crypto.hashing import hash_canonical_json_prefixed, hmac_sha256_prefixed, sha256_prefixed
from app.services.lnurl.comment_allowed import LNURLCommentConfig, LNURLCommentContext, LNURLCommentService
from app.services.lnurl.lightning_address_domain_policy import LightningAddressDomainDecision, LightningAddressDomainPolicy, LightningAddressDomainPolicyConfig
from app.services.lnurl.lightning_address_repository import InMemoryLightningAddressRepository, LightningAddressRepository
from app.services.lnurl.pay.pricing import StaticSubscriptionPricingResolver
from app.services.lnurl.pay.subscription_request_service import LNURLPayRequestResult, LNURLPaySubscriptionRequestConfig, LNURLPaySubscriptionRequestService
from app.services.lnurl.pay_metadata import LNURLPayMetadataBuilder
from app.services.lnurl.product_addresses import (
    ProductAddressMetadataProvider,
    ProductAddressUnavailableError,
    ProductLightningAddressRegistry,
)


class LightningAddressServiceError(ValueError):
    reason_code = "lightning_address_error"


class LightningAddressNotFoundError(LightningAddressServiceError):
    reason_code = "lightning_address_not_found"


class LightningAddressSuspendedError(LightningAddressServiceError):
    reason_code = "lightning_address_suspended"


class LightningAddressDisabledError(LightningAddressServiceError):
    reason_code = "lightning_address_disabled"


class LightningAddressExpiredError(LightningAddressServiceError):
    reason_code = "lightning_address_expired"


class LightningAddressDomainNotVerifiedError(LightningAddressServiceError):
    reason_code = "lightning_address_domain_not_verified"


class LightningAddressTargetInactiveError(LightningAddressServiceError):
    reason_code = "lightning_address_target_inactive"


class LightningAddressPolicyDeniedError(LightningAddressServiceError):
    reason_code = "lightning_address_policy_denied"


class LightningAddressAmountPolicyError(LightningAddressServiceError):
    reason_code = "lightning_address_amount_policy_error"


@dataclass(frozen=True, slots=True)
class LightningAddressServiceConfig:
    enabled: bool = True
    primary_domain: str = "bitcoin-bastion.com"
    payregister_domain: str = "payregister.bitcoin-bastion.com"
    allowed_custom_domains: frozenset[str] = frozenset()
    allow_onion_addresses: bool = False
    default_min_msat: int = 1_000
    default_max_msat: int = 10_000_000
    cache_ttl_seconds: int = 120
    address_pepper: str = "dev-lnurl-lightning-address-pepper-change-me"
    callback_reference_pepper: str = "dev-lnurl-lightning-callback-pepper-change-me"
    max_comment_chars: int = 256
    product_addresses_enabled: bool = True
    product_config_path: str = "config/lnurl_product_addresses.yaml"
    schema_epoch: int = 1
    policy_epoch: int = 1


@dataclass(frozen=True, slots=True)
class LightningAddressResolution:
    normalized_address: str
    target_type: str
    public_target_alias: str
    domain_class: str
    min_sendable_msat: int
    max_sendable_msat: int
    metadata: str
    metadata_hash: str
    callback_reference: str
    comment_allowed: int | None
    payer_data_policy: dict[str, Any] | None
    success_action_policy: str | None
    address_version: int
    policy_hash: str
    resolved_at: datetime
    expires_at: datetime | None
    tag: str = "payRequest"
    limitations: tuple[str, ...] = (
        "lightning_address_is_not_identity",
        "resolution_does_not_issue_invoice_or_entitlement",
    )

    def to_internal_descriptor(self) -> dict[str, Any]:
        descriptor = {
            "tag": self.tag,
            "callback_reference": self.callback_reference,
            "minSendable": self.min_sendable_msat,
            "maxSendable": self.max_sendable_msat,
            "metadata": self.metadata,
            "metadata_hash": self.metadata_hash,
            "target_type": self.target_type,
            "domain_class": self.domain_class,
            "address_version": self.address_version,
            "policy_hash": self.policy_hash,
        }
        if self.comment_allowed and self.comment_allowed > 0:
            descriptor["commentAllowed"] = self.comment_allowed
        if self.payer_data_policy:
            descriptor["payerData"] = self.payer_data_policy
        return descriptor


class LightningAddressPolicyHook(Protocol):
    def evaluate_lightning_address(self, context: Mapping[str, Any]) -> Mapping[str, Any]: ...


class LightningAddressRevocationChecker(Protocol):
    def is_revoked(self, *, target_type: str, target_hash: str) -> bool: ...


AuditEmitter = Callable[[str, Mapping[str, Any]], None]


class LightningAddressService:
    def __init__(
        self,
        *,
        repository: LightningAddressRepository | None = None,
        pay_request_service: LNURLPaySubscriptionRequestService | None = None,
        metadata_builder: LNURLPayMetadataBuilder | None = None,
        domain_policy: LightningAddressDomainPolicy | None = None,
        policy_hook: LightningAddressPolicyHook | None = None,
        revocation_checker: LightningAddressRevocationChecker | None = None,
        audit_emitter: AuditEmitter | None = None,
        config: LightningAddressServiceConfig | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.config = config or LightningAddressServiceConfig()
        self.clock = clock or (lambda: datetime.now(UTC))
        self.repository = repository or InMemoryLightningAddressRepository()
        self.product_registry = (
            ProductLightningAddressRegistry.load_default(self.config.product_config_path)
            if self.config.product_addresses_enabled
            else None
        )
        self.domain_policy = domain_policy or LightningAddressDomainPolicy(
            LightningAddressDomainPolicyConfig(
                primary_domain=self.config.primary_domain,
                first_party_domains=frozenset({self.config.primary_domain}),
                payregister_domains=frozenset({self.config.payregister_domain}),
                verified_custom_domains=self.config.allowed_custom_domains,
                allow_onion_addresses=self.config.allow_onion_addresses,
            )
        )
        pricing_resolver = (
            StaticSubscriptionPricingResolver(
                prices_msat=cast(Mapping[PlanCode | str, int], self.product_registry.pricing_map()),
                disabled_plans=cast(set[PlanCode | str], self.product_registry.disabled_plans()),
                billing_period="monthly",
                pricing_version=f"product-catalog-{self.product_registry.product_catalog_epoch}",
                quote_ttl_seconds=max(180, min(600, self.config.cache_ttl_seconds + 180)),
                clock=self.clock,
            )
            if self.product_registry is not None
            else None
        )
        metadata_provider = ProductAddressMetadataProvider(self.product_registry) if self.product_registry is not None else None
        self.pay_request_service = pay_request_service or LNURLPaySubscriptionRequestService(
            config=LNURLPaySubscriptionRequestConfig(
                public_base_url=f"https://{self.config.primary_domain}",
                request_ttl_seconds=min(120, self.config.cache_ttl_seconds),
                payerdata_auth_enabled=True,
            ),
            pricing_resolver=pricing_resolver,
            metadata_provider=metadata_provider,
            clock=self.clock,
        )
        self.metadata_builder = metadata_builder or LNURLPayMetadataBuilder()
        self.comment_service = LNURLCommentService(LNURLCommentConfig(global_max_chars=self.config.max_comment_chars))
        self.policy_hook = policy_hook
        self.revocation_checker = revocation_checker
        self.audit_emitter = audit_emitter
        self._cache: dict[str, tuple[datetime, LightningAddressResolution]] = {}

    def create_product_address(self, *, local_part: str, domain: str | None = None, comment_allowed: int = 0, visibility: LightningAddressVisibility = LightningAddressVisibility.PUBLIC) -> LightningAddressRecord:
        product = self.product_registry.resolve_product_lightning_address(local_part) if self.product_registry else None
        product_code = product.plan_code.value if product else resolve_product_code(local_part)
        effective_comment = product.comment_allowed if product is not None else comment_allowed
        payer_data_policy_id = (
            "payerdata_auth_optional_v1"
            if product is not None and product.payer_data_policy.get("auth") == "optional"
            else "payerdata_disabled_v1"
        )
        if product is not None and product.payer_data_policy.get("auth") == "required":
            payer_data_policy_id = "payerdata_auth_required_v1"
        return self._create_address(
            local_part=local_part,
            domain=domain or (product.domain if product is not None else self.config.primary_domain),
            target_type=LightningAddressTargetType.SUBSCRIPTION_PRODUCT,
            target_reference_hash=sha256_prefixed(product.product_configuration_hash if product is not None else product_code),
            product_code=product_code,
            metadata_template_id="subscription_product_v1",
            callback_policy_id="lnurl_pay_subscription_callback_v1",
            payer_data_policy_id=payer_data_policy_id,
            success_action_policy_id="subscription_activation_v1",
            comment_allowed=effective_comment,
            visibility=visibility,
            min_sendable_msat=product.amount_msat if product is not None else None,
            max_sendable_msat=product.amount_msat if product is not None else None,
            description=product.product_configuration_hash if product is not None else None,
        )

    def install_product_addresses(self) -> tuple[LightningAddressRecord, ...]:
        if self.product_registry is None:
            return ()
        records = []
        for product in self.product_registry.active_products():
            records.append(self.create_product_address(local_part=product.canonical_name, domain=product.domain))
            for alias in product.aliases:
                records.append(self.create_product_address(local_part=alias.alias, domain=product.domain))
        return tuple(records)

    def create_merchant_address(self, *, local_part: str, domain: str, merchant_reference_hash: str, display_label: str, min_sendable_msat: int | None = None, max_sendable_msat: int | None = None, comment_allowed: int = 0) -> LightningAddressRecord:
        return self._create_address(local_part=local_part, domain=domain, target_type=LightningAddressTargetType.MERCHANT, target_reference_hash=merchant_reference_hash, metadata_template_id="merchant_v1", callback_policy_id="merchant_callback_v1", payer_data_policy_id="payerdata_minimal_v1", success_action_policy_id="merchant_receipt_v1", comment_allowed=comment_allowed, display_label=display_label, min_sendable_msat=min_sendable_msat, max_sendable_msat=max_sendable_msat)

    def create_payregister_store_address(self, *, local_part: str, store_reference_hash: str, display_label: str, domain: str | None = None, comment_allowed: int = 120) -> LightningAddressRecord:
        return self._create_address(local_part=local_part, domain=domain or self.config.payregister_domain, target_type=LightningAddressTargetType.PAYREGISTER_STORE, target_reference_hash=store_reference_hash, payregister_store_hash=store_reference_hash, metadata_template_id="payregister_store_v1", callback_policy_id="payregister_store_callback_v1", payer_data_policy_id="payerdata_minimal_v1", success_action_policy_id="payregister_receipt_v1", comment_allowed=comment_allowed, display_label=display_label)

    def create_payregister_terminal_address(self, *, local_part: str, store_reference_hash: str, terminal_reference_hash: str, display_label: str, domain: str | None = None, comment_allowed: int = 120) -> LightningAddressRecord:
        return self._create_address(local_part=local_part, domain=domain or self.config.payregister_domain, target_type=LightningAddressTargetType.PAYREGISTER_TERMINAL, target_reference_hash=terminal_reference_hash, payregister_store_hash=store_reference_hash, payregister_terminal_hash=terminal_reference_hash, metadata_template_id="payregister_terminal_v1", callback_policy_id="payregister_terminal_callback_v1", payer_data_policy_id="payerdata_minimal_v1", success_action_policy_id="payregister_receipt_v1", comment_allowed=comment_allowed, display_label=display_label)

    def create_donation_address(self, *, local_part: str, domain: str | None = None, donation_reference_hash: str, display_label: str, comment_allowed: int = 120) -> LightningAddressRecord:
        return self._create_address(local_part=local_part, domain=domain or self.config.primary_domain, target_type=LightningAddressTargetType.DONATION, target_reference_hash=donation_reference_hash, metadata_template_id="donation_v1", callback_policy_id="donation_callback_v1", payer_data_policy_id="payerdata_disabled_v1", success_action_policy_id="payment_receipt_v1", comment_allowed=comment_allowed, display_label=display_label)

    def create_business_invoice_address(self, *, local_part: str, domain: str, invoice_reference_hash: str, business_workspace_hash: str, expires_at: datetime, display_label: str) -> LightningAddressRecord:
        return self._create_address(local_part=local_part, domain=domain, target_type=LightningAddressTargetType.BUSINESS_INVOICE, target_reference_hash=invoice_reference_hash, business_workspace_hash=business_workspace_hash, metadata_template_id="business_invoice_v1", callback_policy_id="business_invoice_callback_v1", payer_data_policy_id="payerdata_auth_required_v1", success_action_policy_id="business_onboarding_v1", comment_allowed=0, display_label=display_label, expires_at=expires_at)

    def resolve_address(self, address: str) -> LightningAddressResolution:
        normalized = normalize_lightning_address(address)
        cached = self._cache.get(sha256_prefixed(normalized))
        now = self._now()
        if cached and cached[0] > now:
            return cached[1]
        record = self.repository.get_by_address(normalized)
        if record is None or record.visibility is not LightningAddressVisibility.PUBLIC:
            self._audit("lightning_address_resolution_failed", address_hash=sha256_prefixed(normalized), reason_code="not_found")
            raise LightningAddressNotFoundError("lightning_address_not_found")
        resolution = self._resolve_record(record)
        if record.status is LightningAddressStatus.ACTIVE and record.visibility is LightningAddressVisibility.PUBLIC:
            self._cache[sha256_prefixed(normalized)] = (now + timedelta(seconds=self.config.cache_ttl_seconds), resolution)
        return resolution

    def suspend_address(self, address_id: str, reason: str = "operator_suspended") -> LightningAddressRecord:
        record = self.repository.suspend_address(address_id, reason)
        self._invalidate(record.normalized_address)
        self._audit_record("lightning_address_suspended", record, reason)
        return record

    def reactivate_address(self, address_id: str) -> LightningAddressRecord:
        record = self.repository.reactivate_address(address_id)
        self._invalidate(record.normalized_address)
        self._audit_record("lightning_address_reactivated", record, "reactivated")
        return record

    def disable_address(self, address_id: str, reason: str = "operator_disabled") -> LightningAddressRecord:
        record = self.repository.disable_address(address_id, reason)
        self._invalidate(record.normalized_address)
        self._audit_record("lightning_address_disabled", record, reason)
        return record

    def rotate_callback_policy(self, address_id: str, callback_policy_id: str) -> LightningAddressRecord:
        record = self.repository.update_address(address_id, {"callback_policy_id": callback_policy_id})
        self._invalidate(record.normalized_address)
        self._audit_record("lightning_address_policy_updated", record, "callback_policy_rotated")
        return record

    def update_metadata_policy(self, address_id: str, metadata_template_id: str) -> LightningAddressRecord:
        record = self.repository.update_address(address_id, {"metadata_template_id": metadata_template_id})
        self._invalidate(record.normalized_address)
        self._audit_record("lightning_address_policy_updated", record, "metadata_policy_updated")
        return record

    def update_amount_limits(self, address_id: str, *, min_sendable_msat: int, max_sendable_msat: int) -> LightningAddressRecord:
        if min_sendable_msat <= 0 or max_sendable_msat < min_sendable_msat:
            raise LightningAddressAmountPolicyError("amount_not_allowed")
        record = self.repository.update_address(address_id, {"min_sendable_msat": min_sendable_msat, "max_sendable_msat": max_sendable_msat})
        self._invalidate(record.normalized_address)
        self._audit_record("lightning_address_amount_limits_updated", record, "amount_limits_updated")
        return record

    def verify_custom_domain_binding(self, domain: str) -> LightningAddressDomainDecision:
        decision = self.domain_policy.require_active(domain)
        self._audit("lightning_address_domain_verified", address_hash=sha256_prefixed(decision.domain), reason_code="domain_verified", domain_class=decision.domain_class.value)
        return decision

    def get_product_payment_configuration(self, product_code: str) -> Mapping[str, Any]:
        return {"product_code": product_code, "pricing_source": "LNURLPaySubscriptionRequestService", "price_hardcoded": False}

    def build_product_lightning_address(self, product_code: str) -> str:
        reverse = {value: key for key, value in {
            "lite": "lite_pass",
            "basic": "basic_pass",
            "plus": "plus_pass",
            "pro": "pro_pass",
            "business": "business_pass",
            "enterprise": "enterprise_pass",
        }.items()}
        try:
            return build_lightning_address(reverse[product_code], self.config.primary_domain)
        except KeyError as exc:
            raise LightningAddressNotFoundError("lightning_address_product_unknown") from exc

    def _create_address(self, *, local_part: str, domain: str, target_type: LightningAddressTargetType, target_reference_hash: str, metadata_template_id: str, callback_policy_id: str, payer_data_policy_id: str, success_action_policy_id: str, comment_allowed: int, visibility: LightningAddressVisibility = LightningAddressVisibility.PUBLIC, min_sendable_msat: int | None = None, max_sendable_msat: int | None = None, expires_at: datetime | None = None, principal_hash: str | None = None, business_workspace_hash: str | None = None, payregister_store_hash: str | None = None, payregister_terminal_hash: str | None = None, product_code: str | None = None, display_label: str | None = None, description: str | None = None) -> LightningAddressRecord:
        if not self.config.enabled:
            raise LightningAddressPolicyDeniedError("lightning_address_disabled")
        normalized = build_lightning_address(local_part, domain)
        local, normalized_domain = normalized.split("@", 1)
        self.domain_policy.require_active(normalized_domain)
        effective_comment = self.comment_service.resolve_comment_limit(LNURLCommentContext(flow_type=target_type.value, product_max_chars=self.config.max_comment_chars, merchant_max_chars=self.config.max_comment_chars, terminal_max_chars=self.config.max_comment_chars, request_max_chars=comment_allowed)) if comment_allowed else 0
        now = self._now()
        min_msat = min_sendable_msat or self.config.default_min_msat
        max_msat = max_sendable_msat or self.config.default_max_msat
        record = LightningAddressRecord(address_id=hmac_sha256_prefixed(self.config.address_pepper, normalized), local_part=local, domain=normalized_domain, normalized_address=normalized, target_type=target_type, target_reference_hash=target_reference_hash, status=LightningAddressStatus.ACTIVE, visibility=visibility, min_sendable_msat=min_msat, max_sendable_msat=max_msat, metadata_template_id=metadata_template_id, callback_policy_id=callback_policy_id, payer_data_policy_id=payer_data_policy_id, success_action_policy_id=success_action_policy_id, comment_allowed=effective_comment, currency="BTC", created_at=now, updated_at=now, expires_at=expires_at, version=1, schema_epoch=self.config.schema_epoch, policy_epoch=self.config.policy_epoch, principal_hash=principal_hash, business_workspace_hash=business_workspace_hash, payregister_store_hash=payregister_store_hash, payregister_terminal_hash=payregister_terminal_hash, product_code=product_code, display_label=display_label, description=description)
        record = self.repository.create_address(record)
        self._audit_record("lightning_address_created", record, "created")
        return record

    def _resolve_record(self, record: LightningAddressRecord) -> LightningAddressResolution:
        now = self._now()
        self._require_resolvable(record, now)
        domain_decision = self.domain_policy.require_active(record.domain)
        self._check_revocations(record)
        policy_hash = self._policy(record, domain_decision)
        if record.target_type is LightningAddressTargetType.SUBSCRIPTION_PRODUCT:
            pay_request = self._build_subscription_pay_request(record)
            resolution = self._resolution_from_pay_request(record, pay_request, domain_decision, policy_hash, now)
        else:
            resolution = self._build_non_subscription_resolution(record, domain_decision, policy_hash, now)
        self._audit_record("lightning_address_resolved", record, "resolved")
        return resolution

    def _build_subscription_pay_request(self, record: LightningAddressRecord) -> LNURLPayRequestResult:
        if not record.product_code:
            raise LightningAddressTargetInactiveError("target_inactive")
        product = self.product_registry.get_any_product(record.local_part) if self.product_registry is not None else None
        if self.product_registry is not None and product is None:
            raise LightningAddressTargetInactiveError("target_inactive")
        if product is not None and not product.enabled:
            raise ProductAddressUnavailableError("Lightning Address product is unavailable")
        plan = PlanCode(record.product_code)
        result = self.pay_request_service.create_subscription_request(
            plan_code=plan,
            principal_hash=None,
            actor_type=None,
            product_code=product.canonical_name if product is not None else record.product_code,
            requested_amount_msat=product.amount_msat if product is not None else None,
            comment_allowed=record.comment_allowed,
            payer_data_mode=None,
            success_action_mode="url",
            request_context={
                "lightning_address_hash": sha256_prefixed(record.normalized_address),
                "source": "product_lightning_address",
                "product_configuration_hash": product.product_configuration_hash if product is not None else None,
            },
        )
        if product is not None:
            self._audit(
                "lnurl_product_payment_intent_created",
                address_hash=sha256_prefixed(record.normalized_address),
                reason_code="created",
                product=product.canonical_name,
                plan_code=product.plan_code.value,
                product_configuration_hash=product.product_configuration_hash,
            )
        return result

    def _resolution_from_pay_request(self, record: LightningAddressRecord, pay_request: LNURLPayRequestResult, domain_decision: LightningAddressDomainDecision, policy_hash: str, now: datetime) -> LightningAddressResolution:
        product = self.product_registry.get_any_product(record.local_part) if self.product_registry is not None else None
        payer_data = product.payer_data_declaration() if product is not None else pay_request.payer_data
        metadata = product.metadata_result() if product is not None else None
        if product is not None:
            self._audit(
                "lnurl_product_address_resolved",
                address_hash=sha256_prefixed(record.normalized_address),
                reason_code="resolved",
                product=product.canonical_name,
                plan_code=product.plan_code.value,
                product_configuration_hash=product.product_configuration_hash,
            )
        return LightningAddressResolution(
            record.normalized_address,
            record.target_type.value,
            product.canonical_name if product is not None else record.local_part,
            domain_decision.domain_class.value,
            pay_request.min_sendable_msat,
            pay_request.max_sendable_msat,
            metadata.metadata if metadata is not None else pay_request.metadata,
            metadata.metadata_hash if metadata is not None else pay_request.metadata_hash or hash_canonical_json_prefixed(pay_request.metadata),
            pay_request.payment_context_hash or self._callback_reference(record),
            pay_request.comment_allowed,
            payer_data,
            record.success_action_policy_id,
            record.version,
            product.product_configuration_hash if product is not None else policy_hash,
            now,
            record.expires_at,
        )

    def _build_non_subscription_resolution(self, record: LightningAddressRecord, domain_decision: LightningAddressDomainDecision, policy_hash: str, now: datetime) -> LightningAddressResolution:
        if record.target_type in {LightningAddressTargetType.PAYREGISTER_STORE, LightningAddressTargetType.PAYREGISTER_TERMINAL, LightningAddressTargetType.MERCHANT}:
            metadata = self.metadata_builder.build_payregister_metadata(merchant_display_name=record.display_label or "Bastion merchant", order_reference=None, terminal_reference=record.local_part if record.target_type is LightningAddressTargetType.PAYREGISTER_TERMINAL else None, description=record.description or "Lightning Address payment", lightning_identifier=record.normalized_address)
        elif record.target_type is LightningAddressTargetType.DONATION:
            metadata = self.metadata_builder.build_custom_metadata(plain_text=f"Donation to {record.display_label or 'Bitcoin Bastion'}", long_description=record.description or "Voluntary contribution", identifier=record.normalized_address)
        else:
            metadata = self.metadata_builder.build_custom_metadata(plain_text=record.display_label or "Bastion Lightning payment", long_description=record.description, identifier=record.normalized_address)
        return LightningAddressResolution(record.normalized_address, record.target_type.value, record.local_part, domain_decision.domain_class.value, record.min_sendable_msat, record.max_sendable_msat, metadata.canonical_json, metadata.metadata_hash, self._callback_reference(record), record.comment_allowed if record.comment_allowed > 0 else None, self._payer_data_policy(record), record.success_action_policy_id, record.version, policy_hash, now, record.expires_at)

    def _require_resolvable(self, record: LightningAddressRecord, now: datetime) -> None:
        if record.status is LightningAddressStatus.SUSPENDED:
            raise LightningAddressSuspendedError("address_suspended")
        if record.status is LightningAddressStatus.DISABLED:
            raise LightningAddressDisabledError("address_disabled")
        if record.status is LightningAddressStatus.EXPIRED or (record.expires_at and record.expires_at <= now):
            raise LightningAddressExpiredError("address_expired")
        if record.status is not LightningAddressStatus.ACTIVE:
            raise LightningAddressDomainNotVerifiedError("domain_not_verified")

    def _check_revocations(self, record: LightningAddressRecord) -> None:
        if self.revocation_checker is None:
            return
        checks = (("lightning_address", sha256_prefixed(record.normalized_address)), ("lightning_address_domain", sha256_prefixed(record.domain)), (record.target_type.value, record.target_reference_hash), ("callback_policy", sha256_prefixed(record.callback_policy_id)), ("payer_data_policy", sha256_prefixed(record.payer_data_policy_id)), ("success_action_policy", sha256_prefixed(record.success_action_policy_id)))
        for target_type, target_hash in checks:
            if self.revocation_checker.is_revoked(target_type=target_type, target_hash=target_hash):
                raise LightningAddressPolicyDeniedError("revoked")

    def _policy(self, record: LightningAddressRecord, domain_decision: LightningAddressDomainDecision) -> str:
        context = {"action": "resolve_lightning_address", "target_type": record.target_type.value, "address_status": record.status.value, "domain_status": domain_decision.status.value, "domain_class": domain_decision.domain_class.value, "min_sendable_msat": record.min_sendable_msat, "max_sendable_msat": record.max_sendable_msat, "payer_data_policy_id": record.payer_data_policy_id, "comment_allowed": record.comment_allowed, "success_action_policy_id": record.success_action_policy_id}
        policy_hash = hash_canonical_json_prefixed(context)
        if self.policy_hook is not None:
            decision = self.policy_hook.evaluate_lightning_address(context)
            if decision.get("decision") not in {"allow", None} and not decision.get("allowed", False):
                raise LightningAddressPolicyDeniedError(str(decision.get("reason_code", "policy_denied")))
            policy_hash = str(decision.get("policy_hash") or policy_hash)
        return policy_hash

    def _payer_data_policy(self, record: LightningAddressRecord) -> dict[str, Any] | None:
        if record.payer_data_policy_id == "payerdata_auth_optional_v1":
            return {"auth": {"mandatory": False}}
        if record.payer_data_policy_id == "payerdata_auth_required_v1":
            return {"auth": {"mandatory": True}}
        return None

    def _callback_reference(self, record: LightningAddressRecord) -> str:
        return hmac_sha256_prefixed(self.config.callback_reference_pepper, f"{record.normalized_address}:{record.version}:{record.target_reference_hash}")

    def _invalidate(self, normalized_address: str) -> None:
        self._cache.pop(sha256_prefixed(normalized_address), None)

    def _audit_record(self, event_type: str, record: LightningAddressRecord, reason_code: str) -> None:
        self._audit(event_type, address_hash=sha256_prefixed(record.normalized_address), local_part_hash=sha256_prefixed(record.local_part), domain_hash=sha256_prefixed(record.domain), target_type=record.target_type.value, target_reference_hash=record.target_reference_hash, policy_hash=hash_canonical_json_prefixed({"policy_epoch": record.policy_epoch, "callback_policy_id": record.callback_policy_id}), reason_code=reason_code)

    def _audit(self, event_type: str, **payload: Any) -> None:
        if self.audit_emitter is None:
            return
        self.audit_emitter(event_type, {"timestamp": self._now().isoformat(), **payload})

    def _now(self) -> datetime:
        value = self.clock()
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


__all__ = [
    "LightningAddressService",
    "LightningAddressServiceConfig",
    "LightningAddressResolution",
    "LightningAddressServiceError",
    "LightningAddressNotFoundError",
    "LightningAddressSuspendedError",
    "LightningAddressDisabledError",
    "LightningAddressExpiredError",
    "LightningAddressDomainNotVerifiedError",
    "LightningAddressTargetInactiveError",
    "LightningAddressPolicyDeniedError",
    "LightningAddressAmountPolicyError",
]
