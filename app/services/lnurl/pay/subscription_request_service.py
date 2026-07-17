"""LNURL-pay subscription request service.

This service creates the first-phase LNURL-pay ``payRequest`` for Bastion
subscriptions.  It validates plan/pricing policy, builds an opaque trusted
callback URL, persists a pending request, and emits audit evidence.  It does not
create BOLT-11 invoices, verify settlement, issue Payment Proofs, create
Subscription Entitlements, activate API access, issue Access Certificates, or
process untrusted payerData/comment values.

All payment amounts are integer millisatoshis.  Comments and payerData are only
capability declarations in this phase and are never authorization.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any, Callable, Protocol

from app.domain.access.errors import InvalidPlanCodeError
from app.domain.access.plans import PlanCode, normalize_plan_code
from app.domain.lnurl.tags import LNURLTag
from app.services.access.audit_chain import AccessAuditChain
from app.services.access.crypto.hashing import canonical_json, hash_canonical_json_prefixed, hmac_sha256_prefixed, sha256_prefixed
from app.services.lnurl.pay.callback_urls import LNURLPayCallbackURLBuilder, LNURLPayCallbackURLConfig
from app.services.lnurl.pay.errors import (
    LNURLPayAnonymousCheckoutDeniedError,
    LNURLPayDisabledError,
    LNURLPayIdempotencyConflictError,
    LNURLPayInvalidAmountError,
    LNURLPayInvalidRangeError,
    LNURLPayPlanUnavailableError,
    LNURLPayPolicyDeniedError,
    LNURLPayPrincipalUnavailableError,
    LNURLPayPricingExpiredError,
    LNURLPayRequestError,
    LNURLPayRequestPersistenceError,
    LNURLPayUnknownPlanError,
)
from app.services.lnurl.pay.metadata_provider import LNURLPayMetadataProvider, MinimalLNURLPayMetadataProvider
from app.services.lnurl.pay.pricing import StaticSubscriptionPricingResolver, SubscriptionPricingResolver


class LNURLPayRequestStatus(StrEnum):
    CREATED = "created"
    PENDING_CALLBACK = "pending_callback"
    INVOICE_ISSUED = "invoice_issued"
    EXPIRED = "expired"
    REVOKED = "revoked"
    FAILED = "failed"


class LNURLPayerDataMode(StrEnum):
    NONE = "none"
    AUTH_OPTIONAL = "auth_optional"
    AUTH_MANDATORY = "auth_mandatory"


class LNURLPaySuccessActionMode(StrEnum):
    NONE = "none"
    MESSAGE = "message"
    URL = "url"


@dataclass(frozen=True, slots=True)
class LNURLPayRequestRecord:
    request_id: str
    request_reference_hash: str
    product_code: str
    plan_code: str
    principal_hash: str | None
    actor_type: str | None
    pricing_version: str
    fixed_amount_msat: int | None
    min_amount_msat: int
    max_amount_msat: int
    metadata: str
    metadata_hash: str
    callback_hash: str
    payer_data_policy: dict[str, Any] | None
    payer_data_policy_hash: str | None
    comment_allowed: int | None
    success_action_mode: str
    status: LNURLPayRequestStatus
    created_at: datetime
    expires_at: datetime
    idempotency_hash: str | None
    request_fingerprint: str
    policy_hash: str
    audit_event_hash: str | None = None
    schema_epoch: int = 1
    policy_epoch: int = 1
    crypto_epoch: int = 1
    revoked_at: datetime | None = None

    @property
    def is_active(self) -> bool:
        now = datetime.now(UTC)
        return self.status == LNURLPayRequestStatus.PENDING_CALLBACK and self.expires_at > now and self.revoked_at is None


@dataclass(frozen=True, slots=True)
class LNURLPayRequestResult:
    request_id: str
    tag: str
    callback: str
    min_sendable_msat: int
    max_sendable_msat: int
    metadata: str
    expires_at: datetime
    status: str
    comment_allowed: int | None = None
    payer_data: dict[str, Any] | None = None
    allows_nostr: bool = False
    nostr_pubkey: str | None = None
    product_code: str | None = None
    plan_code: str | None = None
    payment_context_hash: str | None = None
    metadata_hash: str | None = None
    idempotency_replayed: bool = False
    audit_event_hash: str | None = None

    def to_lnurl_response(self) -> dict[str, Any]:
        response: dict[str, Any] = {
            "tag": self.tag,
            "callback": self.callback,
            "minSendable": self.min_sendable_msat,
            "maxSendable": self.max_sendable_msat,
            "metadata": self.metadata,
        }
        if self.comment_allowed is not None and self.comment_allowed > 0:
            response["commentAllowed"] = self.comment_allowed
        if self.payer_data:
            response["payerData"] = self.payer_data
        if self.allows_nostr:
            response["allowsNostr"] = True
        if self.nostr_pubkey:
            response["nostrPubkey"] = self.nostr_pubkey
        return response


@dataclass(frozen=True, slots=True)
class LNURLPaySubscriptionRequestConfig:
    enabled: bool = True
    public_base_url: str = "https://auth.bitcoin-bastion.com"
    request_ttl_seconds: int = 600
    allow_anonymous_checkout: bool = True
    max_comment_length: int = 0
    payerdata_auth_enabled: bool = False
    personal_payerdata_enabled: bool = False
    variable_amount_enabled: bool = False
    request_reference_pepper: str = "dev-lnurl-pay-reference-pepper-change-me"
    idempotency_pepper: str = "dev-lnurl-pay-idempotency-pepper-change-me"
    schema_epoch: int = 1
    policy_epoch: int = 1
    crypto_epoch: int = 1


@dataclass(frozen=True, slots=True)
class LNURLPayPolicyDecision:
    decision: str
    allowed: bool
    reason_code: str = "allowed"
    policy_hash: str | None = None


class LNURLPayPolicyHook(Protocol):
    def evaluate_lnurl_pay_request(self, context: Mapping[str, Any]) -> LNURLPayPolicyDecision: ...


class LNURLPayPrincipalStatusChecker(Protocol):
    def get_principal_status(self, principal_hash: str) -> str | None: ...


class LNURLPayRevocationChecker(Protocol):
    def is_revoked(self, target_type: str, target_hash: str) -> bool: ...


class LNURLPaySubscriptionRequestRepository(Protocol):
    def get_by_idempotency_hash(self, idempotency_hash: str) -> LNURLPayRequestRecord | None: ...

    def get_by_reference_hash(self, request_reference_hash: str) -> LNURLPayRequestRecord | None: ...

    def create(self, record: LNURLPayRequestRecord) -> LNURLPayRequestRecord: ...

    def update_audit_hash(self, request_id: str, audit_event_hash: str) -> None: ...

    def count_invoices(self) -> int: ...

    def count_payment_proofs(self) -> int: ...

    def count_entitlements(self) -> int: ...


class InMemoryLNURLPaySubscriptionRequestRepository:
    def __init__(self) -> None:
        self.records: dict[str, LNURLPayRequestRecord] = {}
        self.by_reference_hash: dict[str, str] = {}
        self.by_idempotency_hash: dict[str, str] = {}
        self.invoice_count = 0
        self.payment_proof_count = 0
        self.entitlement_count = 0

    def get_by_idempotency_hash(self, idempotency_hash: str) -> LNURLPayRequestRecord | None:
        request_id = self.by_idempotency_hash.get(idempotency_hash)
        return self.records.get(request_id) if request_id else None

    def get_by_reference_hash(self, request_reference_hash: str) -> LNURLPayRequestRecord | None:
        request_id = self.by_reference_hash.get(request_reference_hash)
        return self.records.get(request_id) if request_id else None

    def create(self, record: LNURLPayRequestRecord) -> LNURLPayRequestRecord:
        if record.request_reference_hash in self.by_reference_hash:
            raise LNURLPayRequestPersistenceError("Duplicate LNURL-pay request reference")
        if record.idempotency_hash and record.idempotency_hash in self.by_idempotency_hash:
            existing = self.records[self.by_idempotency_hash[record.idempotency_hash]]
            if existing.request_fingerprint != record.request_fingerprint:
                raise LNURLPayIdempotencyConflictError("Conflicting LNURL-pay idempotency request")
            return existing
        self.records[record.request_id] = record
        self.by_reference_hash[record.request_reference_hash] = record.request_id
        if record.idempotency_hash:
            self.by_idempotency_hash[record.idempotency_hash] = record.request_id
        return record

    def update_audit_hash(self, request_id: str, audit_event_hash: str) -> None:
        record = self.records[request_id]
        updated = replace(record, audit_event_hash=audit_event_hash)
        self.records[request_id] = updated
        self.by_reference_hash[updated.request_reference_hash] = request_id
        if updated.idempotency_hash:
            self.by_idempotency_hash[updated.idempotency_hash] = request_id

    def count_invoices(self) -> int:
        return self.invoice_count

    def count_payment_proofs(self) -> int:
        return self.payment_proof_count

    def count_entitlements(self) -> int:
        return self.entitlement_count


class AllowLNURLPayPolicy:
    def evaluate_lnurl_pay_request(self, context: Mapping[str, Any]) -> LNURLPayPolicyDecision:
        return LNURLPayPolicyDecision(
            decision="allow",
            allowed=True,
            policy_hash=hash_canonical_json_prefixed({"action": "create_lnurl_subscription_request", "context": context}),
        )


class LNURLPaySubscriptionRequestService:
    def __init__(
        self,
        *,
        repository: LNURLPaySubscriptionRequestRepository | None = None,
        pricing_resolver: SubscriptionPricingResolver | None = None,
        metadata_provider: LNURLPayMetadataProvider | None = None,
        callback_builder: LNURLPayCallbackURLBuilder | None = None,
        policy_hook: LNURLPayPolicyHook | None = None,
        audit_chain: AccessAuditChain | None = None,
        revocation_checker: LNURLPayRevocationChecker | None = None,
        principal_status_checker: LNURLPayPrincipalStatusChecker | None = None,
        config: LNURLPaySubscriptionRequestConfig | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.config = config or LNURLPaySubscriptionRequestConfig()
        self.clock = clock or (lambda: datetime.now(UTC))
        self.repository = repository or InMemoryLNURLPaySubscriptionRequestRepository()
        self.pricing_resolver = pricing_resolver or StaticSubscriptionPricingResolver(variable_amount_enabled=self.config.variable_amount_enabled, clock=self.clock)
        self.metadata_provider = metadata_provider or MinimalLNURLPayMetadataProvider()
        self.callback_builder = callback_builder or LNURLPayCallbackURLBuilder(LNURLPayCallbackURLConfig(public_base_url=self.config.public_base_url))
        self.policy_hook = policy_hook or AllowLNURLPayPolicy()
        self.audit_chain = audit_chain
        self.revocation_checker = revocation_checker
        self.principal_status_checker = principal_status_checker

    def create_subscription_request(
        self,
        *,
        plan_code: PlanCode | str,
        principal_hash: str | None,
        actor_type: str | None,
        product_code: str,
        requested_amount_msat: int | None = None,
        origin: str | None = None,
        locale: str | None = None,
        idempotency_key: str | None = None,
        payer_data_mode: str | None = None,
        comment_allowed: int | None = None,
        success_action_mode: str | None = None,
        request_context: Mapping[str, Any] | None = None,
    ) -> LNURLPayRequestResult:
        if not self.config.enabled:
            raise LNURLPayDisabledError("LNURL-pay is disabled")
        self._reject_secret_material(request_context)
        try:
            plan = normalize_plan_code(plan_code)
        except InvalidPlanCodeError as exc:
            raise LNURLPayUnknownPlanError("Unknown LNURL-pay subscription plan") from exc
        if product_code.strip() == "sovereign_mode":
            raise LNURLPayPlanUnavailableError("Sovereign Mode is not a subscription plan")
        if not principal_hash and not self.config.allow_anonymous_checkout:
            raise LNURLPayAnonymousCheckoutDeniedError("Anonymous LNURL-pay checkout is disabled")
        self._validate_principal(principal_hash)
        if requested_amount_msat is not None and (not isinstance(requested_amount_msat, int) or isinstance(requested_amount_msat, bool)):
            raise LNURLPayInvalidAmountError("Amount must be integer millisatoshis")
        quote = self.pricing_resolver.resolve_price(plan_code=plan, product_code=product_code, requested_amount_msat=requested_amount_msat)
        quote.validate_amount(requested_amount_msat)
        payer_data = self._build_payer_data_policy(payer_data_mode)
        comment_limit = self._resolve_comment_allowed(comment_allowed)
        success_mode = self._resolve_success_action_mode(success_action_mode)
        now = self._now()
        expires_at = now + timedelta(seconds=self.config.request_ttl_seconds)
        if self.config.request_ttl_seconds <= 0 or quote.quote_expires_at < expires_at:
            raise LNURLPayPricingExpiredError("Pricing quote expires before LNURL-pay request")
        metadata = self.metadata_provider.build_subscription_metadata(
            plan_code=plan,
            product_code=product_code,
            billing_period=quote.billing_period,
            locale=locale,
            pricing_version=quote.pricing_version,
        )
        policy_context = {
            "action": "create_lnurl_subscription_request",
            "actor_type": actor_type,
            "principal_present": principal_hash is not None,
            "plan_code": plan.value,
            "product_code": product_code,
            "billing_period": quote.billing_period,
            "requested_amount_msat": requested_amount_msat,
            "min_amount_msat": quote.min_amount_msat,
            "max_amount_msat": quote.max_amount_msat,
            "anonymous_checkout": principal_hash is None,
            "payer_data": payer_data,
            "comment_allowed": comment_limit,
            "origin_hash": sha256_prefixed(origin) if origin else None,
        }
        decision = self.policy_hook.evaluate_lnurl_pay_request(policy_context)
        if not decision.allowed:
            self._audit_failure("lnurl_pay_request_denied", principal_hash, plan.value, product_code, decision.reason_code, policy_hash=decision.policy_hash)
            raise LNURLPayPolicyDeniedError("LNURL-pay request denied by policy")
        request_fingerprint = self._request_fingerprint(
            plan=plan.value,
            product_code=product_code,
            principal_hash=principal_hash,
            actor_type=actor_type,
            pricing_version=quote.pricing_version,
            fixed_amount_msat=quote.fixed_amount_msat,
            min_amount_msat=quote.min_amount_msat,
            max_amount_msat=quote.max_amount_msat,
            metadata_hash=metadata.metadata_hash,
            payer_data=payer_data,
            comment_allowed=comment_limit,
            success_action_mode=success_mode,
            policy_hash=decision.policy_hash or quote.policy_hash,
        )
        idempotency_hash = self._idempotency_hash(idempotency_key, plan=plan, product_code=product_code, principal_hash=principal_hash)
        if idempotency_hash:
            existing = self.repository.get_by_idempotency_hash(idempotency_hash)
            if existing is not None:
                if existing.status == LNURLPayRequestStatus.REVOKED or self._is_expired(existing):
                    raise LNURLPayIdempotencyConflictError("Existing LNURL-pay request is not reusable")
                if existing.request_fingerprint != request_fingerprint:
                    self._audit_failure("lnurl_pay_idempotency_conflict", principal_hash, plan.value, product_code, "idempotency_conflict", policy_hash=decision.policy_hash)
                    raise LNURLPayIdempotencyConflictError("Conflicting LNURL-pay request")
                if self._revoked("lnurl_pay_request", existing.request_reference_hash):
                    raise LNURLPayPolicyDeniedError("LNURL-pay request is revoked")
                return self._result_from_record(
                    existing,
                    callback=self.callback_builder.build_callback_url(self._opaque_reference_for_idempotency(idempotency_hash, existing.request_fingerprint)),
                    idempotency_replayed=True,
                )
        opaque_reference = (
            self._opaque_reference_for_idempotency(idempotency_hash, request_fingerprint)
            if idempotency_hash
            else secrets.token_urlsafe(32)
        )
        callback = self.callback_builder.build_callback_url(opaque_reference)
        callback_hash = self.callback_builder.callback_hash(callback)
        request_reference_hash = hmac_sha256_prefixed(self.config.request_reference_pepper, opaque_reference)
        record = LNURLPayRequestRecord(
            request_id=sha256_prefixed(f"lnurl-pay-request:{request_reference_hash}"),
            request_reference_hash=request_reference_hash,
            product_code=product_code,
            plan_code=plan.value,
            principal_hash=principal_hash,
            actor_type=actor_type,
            pricing_version=quote.pricing_version,
            fixed_amount_msat=quote.fixed_amount_msat,
            min_amount_msat=quote.min_amount_msat,
            max_amount_msat=quote.max_amount_msat,
            metadata=metadata.metadata,
            metadata_hash=metadata.metadata_hash,
            callback_hash=callback_hash,
            payer_data_policy=payer_data,
            payer_data_policy_hash=hash_canonical_json_prefixed(payer_data) if payer_data else None,
            comment_allowed=comment_limit,
            success_action_mode=success_mode,
            status=LNURLPayRequestStatus.PENDING_CALLBACK,
            created_at=now,
            expires_at=expires_at,
            idempotency_hash=idempotency_hash,
            request_fingerprint=request_fingerprint,
            policy_hash=decision.policy_hash or quote.policy_hash,
            schema_epoch=self.config.schema_epoch,
            policy_epoch=self.config.policy_epoch,
            crypto_epoch=self.config.crypto_epoch,
        )
        try:
            persisted = self.repository.create(record)
            audit_hash = self._audit_success(persisted)
            if audit_hash:
                self.repository.update_audit_hash(persisted.request_id, audit_hash)
                persisted = self.repository.get_by_reference_hash(persisted.request_reference_hash) or persisted
        except LNURLPayRequestError:
            raise
        except Exception as exc:
            raise LNURLPayRequestPersistenceError("LNURL-pay request could not be persisted") from exc
        return self._result_from_record(persisted, callback=callback, idempotency_replayed=False)

    def _validate_principal(self, principal_hash: str | None) -> None:
        if principal_hash is None:
            return
        if self._revoked("principal", principal_hash):
            raise LNURLPayPrincipalUnavailableError("Principal is unavailable")
        if self.principal_status_checker is not None:
            status = self.principal_status_checker.get_principal_status(principal_hash)
            if status in {"revoked", "recovery_locked", "suspended"}:
                raise LNURLPayPrincipalUnavailableError("Principal is unavailable")

    def _build_payer_data_policy(self, payer_data_mode: str | None) -> dict[str, Any] | None:
        mode = LNURLPayerDataMode(payer_data_mode or LNURLPayerDataMode.NONE.value)
        if mode == LNURLPayerDataMode.NONE:
            return None
        if not self.config.payerdata_auth_enabled:
            raise LNURLPayPolicyDeniedError("payerData.auth is disabled")
        return {"auth": {"mandatory": mode == LNURLPayerDataMode.AUTH_MANDATORY}}

    def _resolve_comment_allowed(self, comment_allowed: int | None) -> int | None:
        if comment_allowed is None:
            return self.config.max_comment_length if self.config.max_comment_length > 0 else None
        if not isinstance(comment_allowed, int) or isinstance(comment_allowed, bool) or comment_allowed < 0:
            raise LNURLPayInvalidRangeError("commentAllowed must be a non-negative integer")
        if comment_allowed > self.config.max_comment_length:
            raise LNURLPayInvalidRangeError("commentAllowed exceeds configured maximum")
        return comment_allowed if comment_allowed > 0 else None

    def _resolve_success_action_mode(self, success_action_mode: str | None) -> str:
        return LNURLPaySuccessActionMode(success_action_mode or LNURLPaySuccessActionMode.NONE.value).value

    def _idempotency_hash(self, idempotency_key: str | None, *, plan: PlanCode, product_code: str, principal_hash: str | None) -> str | None:
        if not idempotency_key:
            return None
        material = canonical_json({"key": idempotency_key, "principal": principal_hash or "anonymous"})
        return hmac_sha256_prefixed(self.config.idempotency_pepper, material)

    def _request_fingerprint(self, **payload: Any) -> str:
        return hash_canonical_json_prefixed(payload)

    def _result_from_record(self, record: LNURLPayRequestRecord, *, callback: str, idempotency_replayed: bool) -> LNURLPayRequestResult:
        return LNURLPayRequestResult(
            request_id=record.request_id,
            tag=LNURLTag.PAY_REQUEST.value,
            callback=callback,
            min_sendable_msat=record.min_amount_msat,
            max_sendable_msat=record.max_amount_msat,
            metadata=record.metadata,
            expires_at=record.expires_at,
            status=record.status.value,
            comment_allowed=record.comment_allowed,
            payer_data=record.payer_data_policy,
            product_code=record.product_code,
            plan_code=record.plan_code,
            payment_context_hash=record.request_reference_hash,
            metadata_hash=record.metadata_hash,
            idempotency_replayed=idempotency_replayed,
            audit_event_hash=record.audit_event_hash,
        )

    def _opaque_reference_for_idempotency(self, idempotency_hash: str, request_fingerprint: str) -> str:
        digest = hmac.new(
            self.config.request_reference_pepper.encode("utf-8"),
            f"{idempotency_hash}:{request_fingerprint}".encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

    def _audit_success(self, record: LNURLPayRequestRecord) -> str | None:
        if self.audit_chain is None:
            return None
        event = self.audit_chain.record_event(
            event_type="lnurl_pay_request_created",
            actor_hash=record.principal_hash,
            object_hash=record.request_reference_hash,
            metadata={
                "request_reference_hash": record.request_reference_hash,
                "actor_type": record.actor_type,
                "product_code": record.product_code,
                "plan_code": record.plan_code,
                "pricing_version": record.pricing_version,
                "min_amount_msat": record.min_amount_msat,
                "max_amount_msat": record.max_amount_msat,
                "metadata_hash": record.metadata_hash,
                "callback_hash": record.callback_hash,
                "payer_data_policy_hash": record.payer_data_policy_hash,
                "comment_allowed": record.comment_allowed,
                "policy_hash": record.policy_hash,
                "expires_at": record.expires_at,
            },
        )
        return str(event.event_hash)

    def _audit_failure(self, event_type: str, principal_hash: str | None, plan_code: str, product_code: str, reason_code: str, *, policy_hash: str | None) -> None:
        if self.audit_chain is None:
            return
        self.audit_chain.record_event(
            event_type=event_type,
            actor_hash=principal_hash,
            object_hash=hash_canonical_json_prefixed({"plan": plan_code, "product": product_code}),
            metadata={"plan_code": plan_code, "product_code": product_code, "reason_code": reason_code, "policy_hash": policy_hash},
        )

    def _revoked(self, target_type: str, target_hash: str) -> bool:
        return bool(self.revocation_checker and self.revocation_checker.is_revoked(target_type, target_hash))

    def _is_expired(self, record: LNURLPayRequestRecord) -> bool:
        return record.expires_at <= self._now() or record.status == LNURLPayRequestStatus.EXPIRED

    def _now(self) -> datetime:
        value = self.clock()
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def _reject_secret_material(self, request_context: Mapping[str, Any] | None) -> None:
        if request_context is None:
            return
        forbidden = ("seed", "mnemonic", "xprv", "private_key", "wallet_seed", "bitcoin_seed", "session_token", "access_pass")
        for key, value in request_context.items():
            lowered = str(key).lower()
            if any(part in lowered for part in forbidden):
                raise LNURLPayRequestError("LNURL-pay request context contains forbidden secret material")
            if isinstance(value, str) and any(part in value.lower() for part in ("seed phrase", "private key", "mnemonic")):
                raise LNURLPayRequestError("LNURL-pay request context contains forbidden secret material")


__all__ = [
    "AllowLNURLPayPolicy",
    "InMemoryLNURLPaySubscriptionRequestRepository",
    "LNURLPayPolicyDecision",
    "LNURLPayRequestRecord",
    "LNURLPayRequestResult",
    "LNURLPayRequestStatus",
    "LNURLPaySubscriptionRequestConfig",
    "LNURLPaySubscriptionRequestRepository",
    "LNURLPaySubscriptionRequestService",
]
