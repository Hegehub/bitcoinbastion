"""Static PayRegister LNURL-pay endpoint registry and checkout lifecycle."""
from __future__ import annotations

import re
import secrets
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

from app.services.access.crypto.hashing import hash_canonical_json_prefixed, hmac_sha256_prefixed, sha256_prefixed
from app.services.lnurl.pay.subscription_request_service import LNURLPayRequestResult
from app.services.payregister.lnurl.errors import (
    PayRegisterLNURLContextExpired,
    PayRegisterLNURLContextReplaced,
    PayRegisterLNURLEndpointDisabled,
    PayRegisterLNURLEndpointNotFound,
    PayRegisterLNURLEndpointRevoked,
    PayRegisterLNURLInvalidAmount,
    PayRegisterLNURLNoActiveCheckout,
    PayRegisterLNURLPolicyDenied,
)
from app.services.payregister.lnurl.metadata import build_payregister_lnurl_metadata
from app.domain.payregister_lnurl.contexts import PayRegisterCanonicalContext
from app.services.payregister.lnurl.nfc_payload import PayRegisterLNURLNFCPayload, build_nfc_lnurl_payload, validate_nfc_payload
from app.services.payregister.lnurl.payment_context import (
    PayRegisterLNURLAmountMode,
    PayRegisterLNURLContextStatus,
    PayRegisterLNURLPaymentContext,
    PayRegisterLNULEndpointMode,
)
from app.services.payregister.lnurl.policy import (
    AllowPayRegisterLNURLPolicy,
    NoopPayRegisterLNURLRevocationChecker,
    POLICY_ACTIONS,
    PayRegisterLNURLPolicyHook,
    PayRegisterLNURLRevocationChecker,
)
from app.services.payregister.lnurl.qr_payload import PayRegisterLNURLQRPayload, build_qr_payload, validate_qr_payload

_ALIAS_RE = re.compile(r"^[a-z0-9](?:[a-z0-9_-]{0,62}[a-z0-9])?$")
_RESERVED = {"admin", "api", "auth", "callback", "internal", "lnurl", "lnurlp", "metrics", "root", "status", "support", "system"}


class PayRegisterLNURLEndpointStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DISABLED = "disabled"
    REVOKED = "revoked"


@dataclass(frozen=True, slots=True)
class PayRegisterLNURLStaticEndpoint:
    endpoint_id: str
    public_alias: str
    public_alias_hash: str
    endpoint_mode: PayRegisterLNULEndpointMode
    store_hash: str
    enabled: bool
    min_sendable_msat: int
    max_sendable_msat: int
    allowed_metadata_template: str
    success_action_policy: str
    payer_data_policy: dict[str, Any]
    comment_allowed: int
    risk_profile: str
    display_label: str
    merchant_description: str | None
    created_at: datetime
    updated_at: datetime
    merchant_workspace_hash: str
    terminal_hash: str | None = None
    status: PayRegisterLNURLEndpointStatus = PayRegisterLNURLEndpointStatus.DRAFT
    revoked_at: datetime | None = None


class InMemoryPayRegisterLNURLRepository:
    def __init__(self) -> None:
        self.endpoints_by_id: dict[str, PayRegisterLNURLStaticEndpoint] = {}
        self.endpoint_id_by_alias_hash: dict[str, str] = {}
        self.contexts_by_id: dict[str, PayRegisterLNURLPaymentContext] = {}
        self.active_context_by_endpoint_id: dict[str, str] = {}
        self.audit_events: list[dict[str, Any]] = []

    def create_endpoint(self, endpoint: PayRegisterLNURLStaticEndpoint) -> PayRegisterLNURLStaticEndpoint:
        existing_id = self.endpoint_id_by_alias_hash.get(endpoint.public_alias_hash)
        if existing_id:
            existing = self.endpoints_by_id[existing_id]
            if existing.public_alias == endpoint.public_alias:
                return existing
            raise PayRegisterLNURLPolicyDenied("Public alias is already reserved")
        self.endpoints_by_id[endpoint.endpoint_id] = endpoint
        self.endpoint_id_by_alias_hash[endpoint.public_alias_hash] = endpoint.endpoint_id
        return endpoint

    def update_endpoint(self, endpoint: PayRegisterLNURLStaticEndpoint) -> None:
        self.endpoints_by_id[endpoint.endpoint_id] = endpoint
        self.endpoint_id_by_alias_hash[endpoint.public_alias_hash] = endpoint.endpoint_id

    def get_endpoint(self, endpoint_id: str) -> PayRegisterLNURLStaticEndpoint | None:
        return self.endpoints_by_id.get(endpoint_id)

    def get_endpoint_by_alias_hash(self, alias_hash: str) -> PayRegisterLNURLStaticEndpoint | None:
        endpoint_id = self.endpoint_id_by_alias_hash.get(alias_hash)
        return self.endpoints_by_id.get(endpoint_id) if endpoint_id else None

    def list_endpoints(self) -> list[PayRegisterLNURLStaticEndpoint]:
        return list(self.endpoints_by_id.values())

    def save_context(self, context: PayRegisterLNURLPaymentContext) -> PayRegisterLNURLPaymentContext:
        self.contexts_by_id[context.payment_context_id] = context
        if context.status in {PayRegisterLNURLContextStatus.ACTIVE, PayRegisterLNURLContextStatus.RESOLVED}:
            self.active_context_by_endpoint_id[context.public_endpoint_hash] = context.payment_context_id
        return context

    def get_context(self, context_id: str) -> PayRegisterLNURLPaymentContext | None:
        return self.contexts_by_id.get(context_id)

    def get_active_context(self, endpoint: PayRegisterLNURLStaticEndpoint) -> PayRegisterLNURLPaymentContext | None:
        context_id = self.active_context_by_endpoint_id.get(endpoint.public_alias_hash)
        return self.contexts_by_id.get(context_id) if context_id else None

    def append_audit(self, event_type: str, payload: dict[str, Any]) -> str:
        event_hash = hash_canonical_json_prefixed({"event_type": event_type, **payload, "index": len(self.audit_events)})
        self.audit_events.append({"event_type": event_type, "event_hash": event_hash, **payload})
        return event_hash


@dataclass(frozen=True, slots=True)
class PayRegisterLNURLConfig:
    public_base_url: str = "https://payregister.bitcoin-bastion.com"
    callback_base_url: str = "https://payregister.bitcoin-bastion.com"
    alias_pepper: str = "dev-payregister-lnurl-alias-pepper-change-me"
    context_pepper: str = "dev-payregister-lnurl-context-pepper-change-me"
    callback_token_pepper: str = "dev-payregister-lnurl-callback-pepper-change-me"
    context_ttl_seconds: int = 300
    comment_allowed_default: int = 0
    payer_data_policy_default: dict[str, Any] | None = None


class PayRegisterLNURLStaticEndpointService:
    def __init__(
        self,
        *,
        repository: InMemoryPayRegisterLNURLRepository | None = None,
        policy_hook: PayRegisterLNURLPolicyHook | None = None,
        revocation_checker: PayRegisterLNURLRevocationChecker | None = None,
        config: PayRegisterLNURLConfig | None = None,
        clock: Any | None = None,
    ) -> None:
        self.repository = repository or InMemoryPayRegisterLNURLRepository()
        self.policy_hook = policy_hook or AllowPayRegisterLNURLPolicy()
        self.revocation_checker = revocation_checker or NoopPayRegisterLNURLRevocationChecker()
        self.config = config or PayRegisterLNURLConfig()
        self.clock = clock or (lambda: datetime.now(UTC))

    def create_static_endpoint(
        self,
        *,
        public_alias: str,
        endpoint_mode: PayRegisterLNULEndpointMode,
        merchant_workspace_hash: str,
        store_hash: str,
        terminal_hash: str | None = None,
        min_sendable_msat: int = 1_000,
        max_sendable_msat: int = 100_000_000,
        display_label: str = "PayRegister payment",
        merchant_description: str | None = None,
        comment_allowed: int | None = None,
        payer_data_policy: dict[str, Any] | None = None,
        success_action_policy: str = "payregister_receipt_url_v1",
        risk_profile: str = "standard",
    ) -> PayRegisterLNURLStaticEndpoint:
        alias = normalize_public_alias(public_alias)
        if min_sendable_msat <= 0 or max_sendable_msat < min_sendable_msat:
            raise PayRegisterLNURLInvalidAmount("Invalid endpoint amount bounds")
        self._require_policy(POLICY_ACTIONS["endpoint_create"], {"alias_hash": self._alias_hash(alias), "mode": endpoint_mode.value})
        now = self.clock()
        endpoint = PayRegisterLNURLStaticEndpoint(
            endpoint_id=f"pre_{secrets.token_urlsafe(18)}",
            public_alias=alias,
            public_alias_hash=self._alias_hash(alias),
            endpoint_mode=endpoint_mode,
            store_hash=store_hash,
            enabled=False,
            min_sendable_msat=min_sendable_msat,
            max_sendable_msat=max_sendable_msat,
            allowed_metadata_template="payregister_lnurl_static_v1",
            success_action_policy=success_action_policy,
            payer_data_policy=payer_data_policy or self.config.payer_data_policy_default or {"auth": {"mandatory": False}, "identifier": {"mandatory": False}},
            comment_allowed=self.config.comment_allowed_default if comment_allowed is None else comment_allowed,
            risk_profile=risk_profile,
            display_label=display_label,
            merchant_description=merchant_description,
            created_at=now,
            updated_at=now,
            merchant_workspace_hash=merchant_workspace_hash,
            terminal_hash=terminal_hash,
        )
        persisted = self.repository.create_endpoint(endpoint)
        self.repository.append_audit("payregister_lnurl_endpoint_created", {"public_alias_hash": persisted.public_alias_hash, "mode": endpoint_mode.value})
        return persisted

    def activate_static_endpoint(self, endpoint_id: str) -> PayRegisterLNURLStaticEndpoint:
        endpoint = self._endpoint(endpoint_id)
        updated = replace(endpoint, enabled=True, status=PayRegisterLNURLEndpointStatus.ACTIVE, updated_at=self.clock())
        self.repository.update_endpoint(updated)
        self.repository.append_audit("payregister_lnurl_endpoint_activated", {"public_alias_hash": updated.public_alias_hash})
        return updated

    def suspend_static_endpoint(self, endpoint_id: str, reason: str = "operator_request") -> PayRegisterLNURLStaticEndpoint:
        endpoint = self._endpoint(endpoint_id)
        updated = replace(endpoint, enabled=False, status=PayRegisterLNURLEndpointStatus.SUSPENDED, updated_at=self.clock())
        self.repository.update_endpoint(updated)
        self.repository.append_audit("payregister_lnurl_endpoint_suspended", {"public_alias_hash": updated.public_alias_hash, "reason_code": reason})
        return updated

    def revoke_static_endpoint(self, endpoint_id: str, reason: str = "revoked") -> PayRegisterLNURLStaticEndpoint:
        endpoint = self._endpoint(endpoint_id)
        now = self.clock()
        updated = replace(endpoint, enabled=False, status=PayRegisterLNURLEndpointStatus.REVOKED, revoked_at=now, updated_at=now)
        self.repository.update_endpoint(updated)
        self.repository.append_audit("payregister_lnurl_endpoint_revoked", {"public_alias_hash": updated.public_alias_hash, "reason_code": reason})
        return updated

    def rotate_public_alias(self, endpoint_id: str, new_public_alias: str) -> PayRegisterLNURLStaticEndpoint:
        endpoint = self._endpoint(endpoint_id)
        alias = normalize_public_alias(new_public_alias)
        updated = replace(endpoint, public_alias=alias, public_alias_hash=self._alias_hash(alias), updated_at=self.clock())
        self.repository.update_endpoint(updated)
        self.repository.append_audit("payregister_lnurl_endpoint_alias_rotated", {"public_alias_hash": updated.public_alias_hash})
        return updated

    def publish_checkout_context(
        self,
        *,
        endpoint_id: str,
        amount_msat: int | None,
        description: str,
        order_reference: str | None = None,
        context_version: int | None = None,
        ttl_seconds: int | None = None,
        cashier_context: PayRegisterCanonicalContext | None = None,
    ) -> PayRegisterLNURLPaymentContext:
        endpoint = self._active_endpoint(endpoint_id)
        self._require_policy(POLICY_ACTIONS["checkout_publish"], {"endpoint_hash": endpoint.public_alias_hash, "mode": endpoint.endpoint_mode.value})
        now = self.clock()
        active = self.repository.get_active_context(endpoint)
        if active and active.status in {PayRegisterLNURLContextStatus.ACTIVE, PayRegisterLNURLContextStatus.RESOLVED}:
            self.repository.save_context(replace(active, status=PayRegisterLNURLContextStatus.REPLACED))
            self.repository.append_audit("payregister_lnurl_context_replaced", {"public_alias_hash": endpoint.public_alias_hash, "context_hash": sha256_prefixed(active.payment_context_id)})
        amount_mode = PayRegisterLNURLAmountMode.OPEN if endpoint.endpoint_mode == PayRegisterLNULEndpointMode.STORE_OPEN_AMOUNT else PayRegisterLNURLAmountMode.EXACT
        if cashier_context is not None:
            amount_msat = cashier_context.amount_msat
        if amount_mode != PayRegisterLNURLAmountMode.OPEN:
            if amount_msat is None or amount_msat < endpoint.min_sendable_msat or amount_msat > endpoint.max_sendable_msat:
                raise PayRegisterLNURLInvalidAmount("Checkout amount is outside endpoint bounds")
            min_msat = max_msat = amount_msat
        else:
            min_msat, max_msat = endpoint.min_sendable_msat, endpoint.max_sendable_msat
        metadata = build_payregister_lnurl_metadata(
            merchant_display_name=endpoint.display_label,
            order_reference=order_reference,
            terminal_reference=endpoint.public_alias if endpoint.terminal_hash else None,
            description=description,
            lightning_identifier=f"{endpoint.public_alias}@payregister.bitcoin-bastion.com",
        )
        token = secrets.token_urlsafe(24)
        ctx_id = f"prctx_{secrets.token_urlsafe(18)}"
        context = PayRegisterLNURLPaymentContext(
            payment_context_id=ctx_id,
            public_endpoint_hash=endpoint.public_alias_hash,
            merchant_workspace_hash=endpoint.merchant_workspace_hash,
            store_hash=endpoint.store_hash,
            terminal_hash=cashier_context.terminal_hash if cashier_context is not None else endpoint.terminal_hash,
            cashier_context_hash=sha256_prefixed(cashier_context.context_id) if cashier_context is not None else None,
            shift_hash=cashier_context.shift_hash if cashier_context is not None else None,
            checkout_reference_hash=sha256_prefixed(cashier_context.context_id) if cashier_context is not None else None,
            mode=endpoint.endpoint_mode,
            context_version=context_version or 1,
            amount_mode=amount_mode,
            amount_msat=amount_msat if amount_mode != PayRegisterLNURLAmountMode.OPEN else None,
            min_sendable_msat=min_msat,
            max_sendable_msat=max_msat,
            currency="BTC",
            metadata=metadata.canonical_json,
            metadata_hash=metadata.metadata_hash,
            callback_token_hash=hmac_sha256_prefixed(self.config.callback_token_pepper, token),
            status=PayRegisterLNURLContextStatus.ACTIVE,
            created_at=now,
            expires_at=now + timedelta(seconds=ttl_seconds or self.config.context_ttl_seconds),
            order_reference_hash=sha256_prefixed(order_reference) if order_reference else None,
        )
        persisted = self.repository.save_context(context)
        self.repository.append_audit("payregister_lnurl_checkout_context_created", {"public_alias_hash": endpoint.public_alias_hash, "context_hash": sha256_prefixed(ctx_id), "metadata_hash": metadata.metadata_hash})
        return persisted

    def resolve_static_endpoint(self, public_alias: str) -> PayRegisterLNURLStaticEndpoint:
        alias_hash = self._alias_hash(normalize_public_alias(public_alias))
        endpoint = self.repository.get_endpoint_by_alias_hash(alias_hash)
        if endpoint is None:
            raise PayRegisterLNURLEndpointNotFound("Endpoint unavailable")
        if endpoint.status == PayRegisterLNURLEndpointStatus.REVOKED or endpoint.revoked_at or self.revocation_checker.is_revoked("payregister_lnurl_endpoint", endpoint.public_alias_hash):
            raise PayRegisterLNURLEndpointRevoked("Endpoint unavailable")
        if not endpoint.enabled or endpoint.status != PayRegisterLNURLEndpointStatus.ACTIVE:
            raise PayRegisterLNURLEndpointDisabled("Endpoint unavailable")
        return endpoint

    def resolve_lnurl_pay_request(self, public_alias: str) -> LNURLPayRequestResult:
        endpoint = self.resolve_static_endpoint(public_alias)
        now = self.clock()
        context = self.repository.get_active_context(endpoint)
        if context is None:
            if endpoint.endpoint_mode != PayRegisterLNULEndpointMode.STORE_OPEN_AMOUNT:
                raise PayRegisterLNURLNoActiveCheckout("No active checkout")
            context = self.publish_checkout_context(endpoint_id=endpoint.endpoint_id, amount_msat=None, description=endpoint.merchant_description or endpoint.display_label)
        if context.status == PayRegisterLNURLContextStatus.REPLACED:
            raise PayRegisterLNURLContextReplaced("Checkout was replaced")
        if context.expires_at <= now:
            self.repository.save_context(replace(context, status=PayRegisterLNURLContextStatus.EXPIRED))
            raise PayRegisterLNURLContextExpired("Checkout expired")
        callback = f"{self.config.callback_base_url.rstrip('/')}/api/v1/payregister/lnurl/pay/callback/{context.payment_context_id}"
        self.repository.append_audit("payregister_lnurl_pay_request_returned", {"public_alias_hash": endpoint.public_alias_hash, "context_hash": sha256_prefixed(context.payment_context_id)})
        return LNURLPayRequestResult(
            request_id=context.payment_context_id,
            tag="payRequest",
            callback=callback,
            min_sendable_msat=context.min_sendable_msat,
            max_sendable_msat=context.max_sendable_msat,
            metadata=context.metadata,
            expires_at=context.expires_at,
            status=context.status.value,
            comment_allowed=endpoint.comment_allowed,
            payer_data=endpoint.payer_data_policy,
            product_code="payregister_static_endpoint",
            plan_code="merchant_payment",
            payment_context_hash=sha256_prefixed(context.payment_context_id),
            metadata_hash=context.metadata_hash,
        )

    def build_qr_payload(self, endpoint_id: str) -> PayRegisterLNURLQRPayload:
        endpoint = self._endpoint(endpoint_id)
        payload = build_qr_payload(base_url=self.config.public_base_url, public_alias=endpoint.public_alias, endpoint_mode=endpoint.endpoint_mode, display_label=endpoint.display_label, safe_merchant_description=endpoint.merchant_description, expires_at=endpoint.revoked_at)
        validate_qr_payload(payload)
        return payload

    def build_nfc_payload(self, endpoint_id: str) -> PayRegisterLNURLNFCPayload:
        endpoint = self._endpoint(endpoint_id)
        payload = build_nfc_lnurl_payload(base_url=self.config.public_base_url, public_alias=endpoint.public_alias, endpoint_mode=endpoint.endpoint_mode, expires_at=endpoint.revoked_at)
        validate_nfc_payload(payload)
        return payload

    def mark_invoice_issued(self, context_id: str, *, invoice_hash: str, payment_hash: str, provider_invoice_id_hash: str) -> PayRegisterLNURLPaymentContext:
        context = self._context(context_id)
        if context.status in {PayRegisterLNURLContextStatus.INVOICE_ISSUED, PayRegisterLNURLContextStatus.PENDING_PAYMENT}:
            return context
        updated = replace(context, status=PayRegisterLNURLContextStatus.PENDING_PAYMENT, invoice_issued_at=self.clock(), invoice_hash=invoice_hash, payment_hash=payment_hash, provider_invoice_id_hash=provider_invoice_id_hash)
        self.repository.save_context(updated)
        self.repository.append_audit("payregister_lnurl_invoice_issued", {"context_hash": sha256_prefixed(context_id), "invoice_hash": invoice_hash})
        return updated

    def _endpoint(self, endpoint_id: str) -> PayRegisterLNURLStaticEndpoint:
        endpoint = self.repository.get_endpoint(endpoint_id)
        if endpoint is None:
            raise PayRegisterLNURLEndpointNotFound("Endpoint unavailable")
        return endpoint

    def _context(self, context_id: str) -> PayRegisterLNURLPaymentContext:
        context = self.repository.get_context(context_id)
        if context is None:
            raise PayRegisterLNURLNoActiveCheckout("Checkout unavailable")
        return context

    def _active_endpoint(self, endpoint_id: str) -> PayRegisterLNURLStaticEndpoint:
        endpoint = self._endpoint(endpoint_id)
        if endpoint.status == PayRegisterLNURLEndpointStatus.REVOKED or endpoint.revoked_at:
            raise PayRegisterLNURLEndpointRevoked("Endpoint unavailable")
        if not endpoint.enabled or endpoint.status != PayRegisterLNURLEndpointStatus.ACTIVE:
            raise PayRegisterLNURLEndpointDisabled("Endpoint unavailable")
        return endpoint

    def _alias_hash(self, alias: str) -> str:
        return hmac_sha256_prefixed(self.config.alias_pepper, alias)

    def _require_policy(self, action: str, context: dict[str, Any]) -> None:
        decision = self.policy_hook.evaluate(action, context)
        if not decision.allowed:
            raise PayRegisterLNURLPolicyDenied("Policy denied PayRegister LNURL operation")


def normalize_public_alias(value: str) -> str:
    alias = value.strip().lower()
    if alias in _RESERVED or not _ALIAS_RE.fullmatch(alias) or ".." in alias or "%" in alias or "/" in alias or "\\" in alias:
        raise PayRegisterLNURLEndpointNotFound("Endpoint unavailable")
    return alias


_default_service: PayRegisterLNURLStaticEndpointService | None = None


def get_default_payregister_lnurl_service() -> PayRegisterLNURLStaticEndpointService:
    global _default_service
    if _default_service is None:
        _default_service = PayRegisterLNURLStaticEndpointService()
    return _default_service
