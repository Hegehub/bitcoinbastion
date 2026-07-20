"""Bind settled LNURL Payment Proofs to wallet-bound Subscription Entitlements.

Payment Proof is commercial evidence; principal proofs establish identity; the
Subscription Entitlement defines access. This service never treats invoice
issuance, payment hashes, preimages, comments, payerData.email, Lightning
Address, successAction, or frontend status as authentication.
"""

from __future__ import annotations

import asyncio
import secrets
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any, Protocol

from app.domain.access.plans import PlanCode, normalize_plan_code, plan_rank
from app.domain.lnurl.payment_proofs import LNURLPaymentProof, LNURLPaymentProofStatus
from app.services.access.audit_chain import AccessAuditChain
from app.services.access.entitlement_service import SubscriptionEntitlementService
from app.services.access.crypto.hashing import hmac_sha256_prefixed, sha256_prefixed
from app.services.lnurl.errors import (
    LNURLBindingActivationExpiredError,
    LNURLBindingActivationInvalidError,
    LNURLBindingAmountInvalidError,
    LNURLBindingConflictError,
    LNURLBindingPolicyDeniedError,
    LNURLBindingPrincipalMismatchError,
    LNURLBindingPrincipalRequiredError,
    LNURLBindingProductDisabledError,
    LNURLBindingProductUnknownError,
    LNURLBindingStepUpRequiredError,
    LNURLEntitlementBindingError,
    LNURLPaymentAlreadyConsumedError,
    LNURLPaymentNotSettledError,
    LNURLPaymentProofInvalidError,
    LNURLPaymentProofMissingError,
    LNURLPaymentProofRevokedBindingError,
)
from app.services.lnurl.payment_proof import LNURLPaymentProofService


class LNURLEntitlementBindingState(StrEnum):
    PENDING_SETTLEMENT = "pending_settlement"
    SETTLEMENT_VERIFIED = "settlement_verified"
    PENDING_PRINCIPAL = "pending_principal"
    PENDING_POLICY = "pending_policy"
    ISSUING = "issuing"
    ACTIVE = "active"
    RENEWAL_APPLIED = "renewal_applied"
    UPGRADE_APPLIED = "upgrade_applied"
    DUPLICATE = "duplicate"
    REJECTED = "rejected"
    EXPIRED = "expired"
    FROZEN = "frozen"
    REVOKED = "revoked"
    FAILED_RETRYABLE = "failed_retryable"
    FAILED_TERMINAL = "failed_terminal"


class LNURLEntitlementOperationType(StrEnum):
    NEW_SUBSCRIPTION = "new_subscription"
    RENEWAL = "renewal"
    UPGRADE = "upgrade"
    EXTENSION = "extension"
    BUSINESS_INVOICE_ACTIVATION = "business_invoice_activation"
    PAYREGISTER_PLAN_ACTIVATION = "payregister_plan_activation"


class LNURLEntitlementBindingMode(StrEnum):
    AUTHENTICATED_CHECKOUT = "authenticated_checkout"
    PAYERDATA_AUTH = "payerdata_auth"
    POST_PAYMENT_ACTIVATION = "post_payment_activation"


@dataclass(frozen=True, slots=True)
class PrincipalReference:
    principal_hash: str
    principal_type: str
    binding_mode: LNURLEntitlementBindingMode | str
    auth_method: str
    verified_at: datetime
    session_active: bool = True
    principal_status: str = "active"
    request_principal_hash: str | None = None
    binding_verification_hash: str | None = None


@dataclass(frozen=True, slots=True)
class AccessRequestContext:
    actor_type: str = "wallet_principal"
    auth_method: str = "verified_lnurl_auth"
    wallet_proof_fresh: bool = True
    pop_session_active: bool = False
    recovery_only: bool = False
    risk_level: str = "normal"


@dataclass(frozen=True, slots=True)
class LNURLSubscriptionProduct:
    product_id: str
    plan_code: str
    amount_msat: int
    billing_period_days: int
    currency: str = "BTC"
    allowed_payment_method: str = "lnurl_pay"
    allowed_network: str = "lightning-mainnet"
    metric_groups: tuple[str, ...] = ()
    scopes: tuple[str, ...] = ()
    quota_policy: Mapping[str, Any] | None = None
    activation_policy: str = "principal_required"
    refund_policy: str = "standard"
    issuer_policy: str = "standard"
    enabled: bool = True
    version: int = 1
    product_metadata_hash: str = "sha256:metadata"
    overpayment_policy: str = "accept_record_overpayment"


@dataclass(frozen=True, slots=True)
class SubscriptionEntitlementRecord:
    entitlement_id: str
    principal_hash: str
    principal_type: str
    plan_code: str
    status: str
    valid_from: datetime
    valid_until: datetime
    payment_proof_fingerprint: str
    payment_binding_id: str
    product_id: str
    issuer_signature: str = "signed-by-existing-entitlement-service"


@dataclass(frozen=True, slots=True)
class LNURLEntitlementBindingRecord:
    binding_id: str
    payment_proof_id: str
    payment_proof_fingerprint: str
    principal_hash: str | None
    principal_type: str | None
    entitlement_id: str | None
    product_id: str
    plan_code: str
    operation_type: str
    binding_mode: str
    status: str
    idempotency_key: str
    failure_reason: str | None
    activation_reference_hash: str | None
    activation_expires_at: datetime | None
    policy_decision_hash: str | None
    audit_event_hash: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    consumed: bool = False


@dataclass(frozen=True, slots=True)
class EntitlementBindingResult:
    binding_id: str
    payment_proof_fingerprint: str
    principal_hash: str | None
    principal_type: str | None
    plan_code: str
    entitlement_id: str | None
    entitlement_status: str | None
    binding_status: str
    operation_type: str
    valid_from: datetime | None
    valid_until: datetime | None
    requires_wallet_activation: bool
    policy_refresh_required: bool
    audit_event_hash: str | None
    idempotent_replay: bool
    limitations: tuple[str, ...] = ()
    activation_reference: str | None = None


class LNURLEntitlementBindingRepository(Protocol):
    def get_binding_by_payment_proof(self, payment_proof_id: str) -> LNURLEntitlementBindingRecord | None: ...
    def get_binding_by_id(self, binding_id: str) -> LNURLEntitlementBindingRecord | None: ...
    def create_pending_binding(self, record: LNURLEntitlementBindingRecord) -> LNURLEntitlementBindingRecord: ...
    def mark_binding_active(self, record: LNURLEntitlementBindingRecord) -> LNURLEntitlementBindingRecord: ...
    def mark_binding_failed(self, record: LNURLEntitlementBindingRecord) -> LNURLEntitlementBindingRecord: ...
    def get_reservation_by_activation_hash(self, activation_hash: str) -> LNURLEntitlementBindingRecord | None: ...
    def consume_reservation(self, record: LNURLEntitlementBindingRecord) -> LNURLEntitlementBindingRecord: ...
    def record_payment_proof_consumption(self, payment_proof_id: str, purpose: str, binding_id: str) -> bool: ...
    def find_active_entitlement_for_principal(self, principal_hash: str) -> SubscriptionEntitlementRecord | None: ...
    def save_entitlement_transition(self, entitlement: SubscriptionEntitlementRecord) -> SubscriptionEntitlementRecord: ...
    def get_product(self, product_id: str) -> LNURLSubscriptionProduct | None: ...


class InMemoryLNURLEntitlementBindingRepository:
    def __init__(self, products: Mapping[str, LNURLSubscriptionProduct] | None = None) -> None:
        self._lock = asyncio.Lock()
        self.bindings_by_proof: dict[str, LNURLEntitlementBindingRecord] = {}
        self.bindings_by_id: dict[str, LNURLEntitlementBindingRecord] = {}
        self.bindings_by_activation_hash: dict[str, LNURLEntitlementBindingRecord] = {}
        self.consumptions: dict[tuple[str, str], str] = {}
        self.entitlements_by_principal: dict[str, SubscriptionEntitlementRecord] = {}
        self.products = dict(products or default_lnurl_subscription_products())

    def get_binding_by_payment_proof(self, payment_proof_id: str) -> LNURLEntitlementBindingRecord | None:
        return self.bindings_by_proof.get(payment_proof_id)

    def get_binding_by_id(self, binding_id: str) -> LNURLEntitlementBindingRecord | None:
        return self.bindings_by_id.get(binding_id)

    def create_pending_binding(self, record: LNURLEntitlementBindingRecord) -> LNURLEntitlementBindingRecord:
        existing = self.bindings_by_proof.get(record.payment_proof_id)
        if existing is not None:
            return existing
        self.bindings_by_proof[record.payment_proof_id] = record
        self.bindings_by_id[record.binding_id] = record
        if record.activation_reference_hash:
            self.bindings_by_activation_hash[record.activation_reference_hash] = record
        return record

    def mark_binding_active(self, record: LNURLEntitlementBindingRecord) -> LNURLEntitlementBindingRecord:
        self.bindings_by_proof[record.payment_proof_id] = record
        self.bindings_by_id[record.binding_id] = record
        return record

    def mark_binding_failed(self, record: LNURLEntitlementBindingRecord) -> LNURLEntitlementBindingRecord:
        self.bindings_by_proof[record.payment_proof_id] = record
        self.bindings_by_id[record.binding_id] = record
        return record

    def get_reservation_by_activation_hash(self, activation_hash: str) -> LNURLEntitlementBindingRecord | None:
        return self.bindings_by_activation_hash.get(activation_hash)

    def consume_reservation(self, record: LNURLEntitlementBindingRecord) -> LNURLEntitlementBindingRecord:
        consumed = replace(record, consumed=True, activation_reference_hash=None, updated_at=datetime.now(UTC))
        self.bindings_by_proof[consumed.payment_proof_id] = consumed
        self.bindings_by_id[consumed.binding_id] = consumed
        return consumed

    def record_payment_proof_consumption(self, payment_proof_id: str, purpose: str, binding_id: str) -> bool:
        key = (payment_proof_id, purpose)
        existing = self.consumptions.get(key)
        if existing is not None:
            return existing == binding_id
        self.consumptions[key] = binding_id
        return True

    def find_active_entitlement_for_principal(self, principal_hash: str) -> SubscriptionEntitlementRecord | None:
        entitlement = self.entitlements_by_principal.get(principal_hash)
        if entitlement and entitlement.status == "active":
            return entitlement
        return None

    def save_entitlement_transition(self, entitlement: SubscriptionEntitlementRecord) -> SubscriptionEntitlementRecord:
        self.entitlements_by_principal[entitlement.principal_hash] = entitlement
        return entitlement

    def get_product(self, product_id: str) -> LNURLSubscriptionProduct | None:
        return self.products.get(product_id)


class EntitlementIssuer(Protocol):
    def issue(
        self,
        *,
        principal: PrincipalReference,
        product: LNURLSubscriptionProduct,
        operation_type: LNURLEntitlementOperationType,
        binding_id: str,
        payment_proof_fingerprint: str,
        current: SubscriptionEntitlementRecord | None,
        now: datetime,
    ) -> SubscriptionEntitlementRecord: ...


class InMemoryEntitlementIssuer:
    """Adapter-shaped issuer used in tests; production should wrap SubscriptionEntitlementService."""

    def issue(
        self,
        *,
        principal: PrincipalReference,
        product: LNURLSubscriptionProduct,
        operation_type: LNURLEntitlementOperationType,
        binding_id: str,
        payment_proof_fingerprint: str,
        current: SubscriptionEntitlementRecord | None,
        now: datetime,
    ) -> SubscriptionEntitlementRecord:
        valid_from = now
        if operation_type is LNURLEntitlementOperationType.RENEWAL and current is not None:
            valid_from = current.valid_from if current.valid_until > now else now
            valid_until = (current.valid_until if current.valid_until > now else now) + timedelta(days=product.billing_period_days)
        else:
            valid_until = now + timedelta(days=product.billing_period_days)
        return SubscriptionEntitlementRecord(
            entitlement_id="ent_" + sha256_prefixed(binding_id + principal.principal_hash).split(":", 1)[1][:24],
            principal_hash=principal.principal_hash,
            principal_type=principal.principal_type,
            plan_code=product.plan_code,
            status="active",
            valid_from=valid_from,
            valid_until=valid_until,
            payment_proof_fingerprint=payment_proof_fingerprint,
            payment_binding_id=binding_id,
            product_id=product.product_id,
        )


class SubscriptionEntitlementServiceIssuer:
    """Adapter that delegates issuance/renewal/upgrade to the existing Access Entitlement Service."""

    def __init__(self, entitlement_service: SubscriptionEntitlementService) -> None:
        self.entitlement_service = entitlement_service

    def issue(
        self,
        *,
        principal: PrincipalReference,
        product: LNURLSubscriptionProduct,
        operation_type: LNURLEntitlementOperationType,
        binding_id: str,
        payment_proof_fingerprint: str,
        current: SubscriptionEntitlementRecord | None,
        now: datetime,
    ) -> SubscriptionEntitlementRecord:
        valid_from = now
        valid_until = now + timedelta(days=product.billing_period_days)
        metadata = {
            "payment_method": "lnurl_pay",
            "payment_proof_fingerprint": payment_proof_fingerprint,
            "payment_binding_id": binding_id,
            "product_id": product.product_id,
            "product_version": product.version,
            "product_metadata_hash": product.product_metadata_hash,
        }
        pass_lookup_hash = principal.principal_hash
        certificate_fingerprint = principal.binding_verification_hash or sha256_prefixed(principal.principal_hash)
        existing = self.entitlement_service.get_current_entitlement(
            pass_lookup_hash=pass_lookup_hash, include_restricted=False
        )
        if operation_type is LNURLEntitlementOperationType.RENEWAL and existing is not None:
            base = existing.valid_until if existing.valid_until > now.replace(tzinfo=None) else now
            model = self.entitlement_service.renew_entitlement(
                existing,
                valid_from=existing.valid_from,
                valid_until=base + timedelta(days=product.billing_period_days),
            )
        elif operation_type is LNURLEntitlementOperationType.UPGRADE and existing is not None:
            model = self.entitlement_service.upgrade_entitlement(
                existing,
                new_plan_code=product.plan_code,
                valid_from=now,
                valid_until=valid_until,
            )
        else:
            model = self.entitlement_service.issue_entitlement(
                pass_lookup_hash=pass_lookup_hash,
                certificate_fingerprint=certificate_fingerprint,
                plan_code=product.plan_code,
                valid_from=valid_from,
                valid_until=valid_until,
                metadata=metadata,
            )
        return SubscriptionEntitlementRecord(
            entitlement_id=str(model.id),
            principal_hash=principal.principal_hash,
            principal_type=principal.principal_type,
            plan_code=model.plan_code,
            status=model.status,
            valid_from=model.valid_from.replace(tzinfo=UTC) if model.valid_from.tzinfo is None else model.valid_from,
            valid_until=model.valid_until.replace(tzinfo=UTC) if model.valid_until.tzinfo is None else model.valid_until,
            payment_proof_fingerprint=payment_proof_fingerprint,
            payment_binding_id=binding_id,
            product_id=product.product_id,
            issuer_signature=str(model.issuer_signature_json),
        )


class BindingPolicy(Protocol):
    def decide(self, context: dict[str, Any]) -> tuple[str, str]: ...


class DefaultBindingPolicy:
    def decide(self, context: dict[str, Any]) -> tuple[str, str]:
        if context.get("principal_status") == "revoked":
            return "deny", "revoked"
        if context.get("operation_type") == LNURLEntitlementOperationType.UPGRADE.value and context.get("risk_level") == "high":
            return "step_up_required", "lnurl_binding_step_up_required"
        return "allow", "allow"


@dataclass(frozen=True, slots=True)
class LNURLEntitlementBindingConfig:
    enabled: bool = True
    activation_ttl_seconds: int = 900
    max_activation_attempts: int = 5
    require_principal: bool = True
    allow_pending_reservations: bool = True
    overpayment_policy: str = "accept_record_overpayment"
    quote_max_age_seconds: int = 900
    retry_max_attempts: int = 3
    idempotency_pepper: str = "dev-lnurl-entitlement-binding-pepper-change-me"


class LNURLEntitlementBindingService:
    def __init__(
        self,
        *,
        payment_proof_service: LNURLPaymentProofService,
        repository: LNURLEntitlementBindingRepository | None = None,
        entitlement_issuer: EntitlementIssuer | None = None,
        policy: BindingPolicy | None = None,
        audit_chain: AccessAuditChain | None = None,
        cache_invalidator: Callable[[str], None] | None = None,
        config: LNURLEntitlementBindingConfig | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.payment_proof_service = payment_proof_service
        self.repository = repository or InMemoryLNURLEntitlementBindingRepository()
        self.entitlement_issuer = entitlement_issuer or InMemoryEntitlementIssuer()
        self.policy = policy or DefaultBindingPolicy()
        self.audit_chain = audit_chain
        self.cache_invalidator = cache_invalidator
        self.config = config or LNURLEntitlementBindingConfig()
        self.clock = clock or (lambda: datetime.now(UTC))

    async def bind_settled_payment_to_principal(
        self,
        *,
        payment_proof_id: str,
        principal_reference: PrincipalReference | None,
        activation_reference: str | None = None,
        request_context: AccessRequestContext | None = None,
        operation_type: LNURLEntitlementOperationType | str = LNURLEntitlementOperationType.NEW_SUBSCRIPTION,
    ) -> EntitlementBindingResult:
        lock = getattr(self.repository, "_lock", None)
        if lock is not None:
            async with lock:
                return self._bind_locked(
                    payment_proof_id=payment_proof_id,
                    principal_reference=principal_reference,
                    activation_reference=activation_reference,
                    request_context=request_context or AccessRequestContext(),
                    operation_type=LNURLEntitlementOperationType(operation_type),
                )
        return self._bind_locked(
            payment_proof_id=payment_proof_id,
            principal_reference=principal_reference,
            activation_reference=activation_reference,
            request_context=request_context or AccessRequestContext(),
            operation_type=LNURLEntitlementOperationType(operation_type),
        )

    def issue_entitlement_from_payment(self, **kwargs: Any) -> EntitlementBindingResult:
        kwargs["operation_type"] = LNURLEntitlementOperationType.NEW_SUBSCRIPTION
        return asyncio.run(self.bind_settled_payment_to_principal(**kwargs))

    def renew_entitlement_from_payment(self, **kwargs: Any) -> EntitlementBindingResult:
        kwargs["operation_type"] = LNURLEntitlementOperationType.RENEWAL
        return asyncio.run(self.bind_settled_payment_to_principal(**kwargs))

    def upgrade_entitlement_from_payment(self, **kwargs: Any) -> EntitlementBindingResult:
        kwargs["operation_type"] = LNURLEntitlementOperationType.UPGRADE
        return asyncio.run(self.bind_settled_payment_to_principal(**kwargs))

    def resolve_payment_binding(self, payment_proof_id: str) -> LNURLEntitlementBindingRecord | None:
        return self.repository.get_binding_by_payment_proof(payment_proof_id)

    def get_binding_status(self, binding_id: str) -> EntitlementBindingResult | None:
        record = self.repository.get_binding_by_id(binding_id)
        return self._result(record, idempotent=True) if record else None

    def retry_failed_binding(self, binding_id: str, principal_reference: PrincipalReference) -> EntitlementBindingResult:
        record = self.repository.get_binding_by_id(binding_id)
        if record is None or record.status != LNURLEntitlementBindingState.FAILED_RETRYABLE.value:
            raise LNURLEntitlementBindingError("lnurl_binding_not_retryable")
        return asyncio.run(
            self.bind_settled_payment_to_principal(
                payment_proof_id=record.payment_proof_id,
                principal_reference=principal_reference,
                operation_type=record.operation_type,
            )
        )

    def freeze_invalid_binding(self, binding_id: str, reason: str) -> LNURLEntitlementBindingRecord:
        record = self.repository.get_binding_by_id(binding_id)
        if record is None:
            raise LNURLEntitlementBindingError("lnurl_binding_missing")
        frozen = replace(record, status=LNURLEntitlementBindingState.FROZEN.value, failure_reason=reason, updated_at=self.clock())
        self.repository.mark_binding_failed(frozen)
        self._audit("lnurl_entitlement_binding_failed", frozen, decision="deny", reason_code=reason)
        return frozen

    def verify_binding_integrity(self, binding_id: str) -> bool:
        record = self.repository.get_binding_by_id(binding_id)
        if record is None:
            raise LNURLEntitlementBindingError("lnurl_binding_missing")
        expected = self._idempotency_key(record.payment_proof_fingerprint, record.product_id, LNURLEntitlementOperationType(record.operation_type), record.principal_hash)
        if expected != record.idempotency_key:
            raise LNURLEntitlementBindingError("lnurl_binding_integrity_failed")
        return True

    def _bind_locked(
        self,
        *,
        payment_proof_id: str,
        principal_reference: PrincipalReference | None,
        activation_reference: str | None,
        request_context: AccessRequestContext,
        operation_type: LNURLEntitlementOperationType,
    ) -> EntitlementBindingResult:
        proof = self._load_and_validate_proof(payment_proof_id)
        existing = self.repository.get_binding_by_payment_proof(payment_proof_id)
        if existing is not None:
            if existing.status == LNURLEntitlementBindingState.PENDING_PRINCIPAL.value and principal_reference and activation_reference:
                return self._activate_reservation(existing, proof, principal_reference, activation_reference, request_context)
            if existing.principal_hash and principal_reference and existing.principal_hash != principal_reference.principal_hash:
                raise LNURLBindingPrincipalMismatchError("lnurl_binding_principal_mismatch")
            return self._result(existing, idempotent=True)
        product = self._validate_product(proof)
        if principal_reference is None:
            if not self.config.allow_pending_reservations:
                raise LNURLBindingPrincipalRequiredError("lnurl_binding_principal_required")
            return self._create_reservation(proof, product, operation_type)
        principal = self._validate_principal(proof, principal_reference, request_context)
        return self._issue_for_principal(proof, product, principal, operation_type, request_context, None)

    def _activate_reservation(
        self,
        record: LNURLEntitlementBindingRecord,
        proof: LNURLPaymentProof,
        principal: PrincipalReference,
        activation_reference: str,
        request_context: AccessRequestContext,
    ) -> EntitlementBindingResult:
        if record.activation_expires_at and record.activation_expires_at <= self.clock():
            raise LNURLBindingActivationExpiredError("lnurl_binding_activation_expired")
        activation_hash = self._activation_hash(activation_reference, proof.proof_fingerprint)
        if not record.activation_reference_hash or activation_hash != record.activation_reference_hash:
            raise LNURLBindingActivationInvalidError("lnurl_binding_activation_invalid")
        if not request_context.wallet_proof_fresh:
            raise LNURLBindingPrincipalRequiredError("lnurl_binding_principal_required")
        validated = self._validate_principal(proof, principal, request_context, allow_unmatched_request=True)
        return self._issue_for_principal(
            proof,
            self._validate_product(proof),
            validated,
            LNURLEntitlementOperationType(record.operation_type),
            request_context,
            record,
        )

    def _load_and_validate_proof(self, payment_proof_id: str) -> LNURLPaymentProof:
        proof = self.payment_proof_service.get_payment_proof(payment_proof_id)
        if proof is None:
            raise LNURLPaymentProofMissingError("lnurl_payment_proof_missing")
        if proof.status == LNURLPaymentProofStatus.REVOKED.value or proof.revoked_at is not None:
            raise LNURLPaymentProofRevokedBindingError("lnurl_payment_proof_revoked")
        if not proof.settled or not proof.settled_at:
            raise LNURLPaymentNotSettledError("lnurl_payment_not_settled")
        try:
            self.payment_proof_service.verify_payment_proof_integrity(proof)
        except Exception as exc:
            raise LNURLPaymentProofInvalidError("lnurl_payment_proof_invalid") from exc
        return proof

    def _validate_product(self, proof: LNURLPaymentProof) -> LNURLSubscriptionProduct:
        product = self.repository.get_product(proof.product_code)
        if product is None:
            raise LNURLBindingProductUnknownError("lnurl_binding_product_unknown")
        if not product.enabled:
            raise LNURLBindingProductDisabledError("lnurl_binding_product_disabled")
        if proof.amount_msat < product.amount_msat:
            raise LNURLBindingAmountInvalidError("lnurl_binding_amount_invalid")
        if proof.amount_msat > product.amount_msat and product.overpayment_policy == "reject":
            raise LNURLBindingAmountInvalidError("lnurl_binding_amount_invalid")
        if proof.currency != product.currency or proof.network != product.allowed_network:
            raise LNURLBindingAmountInvalidError("lnurl_binding_amount_invalid")
        if proof.payment_metadata_hash != product.product_metadata_hash:
            raise LNURLPaymentProofInvalidError("lnurl_payment_proof_invalid")
        normalize_plan_code(product.plan_code)
        return product

    def _validate_principal(
        self,
        proof: LNURLPaymentProof,
        principal: PrincipalReference,
        request_context: AccessRequestContext,
        *,
        allow_unmatched_request: bool = False,
    ) -> PrincipalReference:
        if principal.principal_type not in {"bitcoin_wallet_principal", "lightning_wallet_principal"}:
            raise LNURLBindingPrincipalRequiredError("lnurl_binding_principal_required")
        if principal.principal_status != "active":
            raise LNURLBindingPolicyDeniedError("lnurl_binding_policy_denied")
        if not principal.session_active or request_context.recovery_only:
            raise LNURLBindingPolicyDeniedError("lnurl_binding_policy_denied")
        mode = LNURLEntitlementBindingMode(principal.binding_mode)
        if mode is LNURLEntitlementBindingMode.AUTHENTICATED_CHECKOUT:
            if not request_context.pop_session_active:
                raise LNURLBindingPrincipalRequiredError("lnurl_binding_principal_required")
            if proof.principal_hash and proof.principal_hash != principal.principal_hash:
                raise LNURLBindingPrincipalMismatchError("lnurl_binding_principal_mismatch")
            if principal.request_principal_hash and principal.request_principal_hash != principal.principal_hash:
                raise LNURLBindingPrincipalMismatchError("lnurl_binding_principal_mismatch")
        elif mode is LNURLEntitlementBindingMode.PAYERDATA_AUTH:
            if not principal.binding_verification_hash:
                raise LNURLBindingPrincipalRequiredError("lnurl_binding_principal_required")
        elif mode is LNURLEntitlementBindingMode.POST_PAYMENT_ACTIVATION:
            if not allow_unmatched_request:
                raise LNURLBindingPrincipalRequiredError("lnurl_binding_principal_required")
            if not request_context.wallet_proof_fresh:
                raise LNURLBindingPrincipalRequiredError("lnurl_binding_principal_required")
        return principal

    def _issue_for_principal(
        self,
        proof: LNURLPaymentProof,
        product: LNURLSubscriptionProduct,
        principal: PrincipalReference,
        operation_type: LNURLEntitlementOperationType,
        request_context: AccessRequestContext,
        existing_reservation: LNURLEntitlementBindingRecord | None,
    ) -> EntitlementBindingResult:
        current = self.repository.find_active_entitlement_for_principal(principal.principal_hash)
        if operation_type is LNURLEntitlementOperationType.UPGRADE and current and plan_rank(normalize_plan_code(product.plan_code)) <= plan_rank(normalize_plan_code(current.plan_code)):
            raise LNURLBindingConflictError("lnurl_binding_conflict")
        decision, reason = self.policy.decide(self._policy_context(proof, product, principal, operation_type, request_context, current))
        if decision == "step_up_required":
            record = self._new_record(proof, product, principal, operation_type, LNURLEntitlementBindingState.PENDING_POLICY, reason)
            self.repository.create_pending_binding(record)
            self._audit("lnurl_entitlement_binding_step_up_required", record, decision=decision, reason_code=reason)
            raise LNURLBindingStepUpRequiredError("lnurl_binding_step_up_required")
        if decision != "allow":
            record = self._new_record(proof, product, principal, operation_type, LNURLEntitlementBindingState.REJECTED, reason)
            self.repository.create_pending_binding(record)
            self._audit("lnurl_entitlement_binding_policy_denied", record, decision=decision, reason_code=reason)
            raise LNURLBindingPolicyDeniedError("lnurl_binding_policy_denied")
        binding = existing_reservation or self._new_record(proof, product, principal, operation_type, LNURLEntitlementBindingState.ISSUING, None)
        binding = self.repository.create_pending_binding(binding)
        if not self.repository.record_payment_proof_consumption(proof.proof_id, self._consumption_purpose(operation_type), binding.binding_id):
            raise LNURLPaymentAlreadyConsumedError("lnurl_payment_already_consumed")
        entitlement = self.entitlement_issuer.issue(
            principal=principal,
            product=product,
            operation_type=operation_type,
            binding_id=binding.binding_id,
            payment_proof_fingerprint=proof.proof_fingerprint,
            current=current,
            now=self.clock(),
        )
        entitlement = self.repository.save_entitlement_transition(entitlement)
        final_state = {
            LNURLEntitlementOperationType.RENEWAL: LNURLEntitlementBindingState.RENEWAL_APPLIED,
            LNURLEntitlementOperationType.UPGRADE: LNURLEntitlementBindingState.UPGRADE_APPLIED,
        }.get(operation_type, LNURLEntitlementBindingState.ACTIVE)
        active = replace(
            binding,
            principal_hash=principal.principal_hash,
            principal_type=principal.principal_type,
            entitlement_id=entitlement.entitlement_id,
            status=final_state.value,
            completed_at=self.clock(),
            updated_at=self.clock(),
            consumed=True,
        )
        audit_hash = self._audit("lnurl_entitlement_issued" if final_state is LNURLEntitlementBindingState.ACTIVE else f"lnurl_entitlement_{operation_type.value}d", active, decision="allow", reason_code="allow")
        active = replace(active, audit_event_hash=audit_hash)
        active = self.repository.mark_binding_active(active)
        self._audit("lnurl_payment_proof_consumed", active, decision="allow", reason_code="consumed")
        if self.cache_invalidator:
            self.cache_invalidator(principal.principal_hash)
        return self._result(active, entitlement=entitlement, idempotent=False)

    def _create_reservation(
        self,
        proof: LNURLPaymentProof,
        product: LNURLSubscriptionProduct,
        operation_type: LNURLEntitlementOperationType,
    ) -> EntitlementBindingResult:
        activation = "lnact_" + secrets.token_urlsafe(32)
        activation_hash = self._activation_hash(activation, proof.proof_fingerprint)
        record = self._new_record(
            proof,
            product,
            None,
            operation_type,
            LNURLEntitlementBindingState.PENDING_PRINCIPAL,
            None,
            activation_hash=activation_hash,
            activation_expires_at=self.clock() + timedelta(seconds=self.config.activation_ttl_seconds),
        )
        record = self.repository.create_pending_binding(record)
        audit_hash = self._audit("lnurl_entitlement_reservation_created", record, decision="pending_principal", reason_code="principal_required")
        record = replace(record, audit_event_hash=audit_hash)
        self.repository.mark_binding_active(record)
        result = self._result(record, idempotent=False)
        return replace(result, activation_reference=activation)

    def _new_record(
        self,
        proof: LNURLPaymentProof,
        product: LNURLSubscriptionProduct,
        principal: PrincipalReference | None,
        operation_type: LNURLEntitlementOperationType,
        state: LNURLEntitlementBindingState,
        failure_reason: str | None,
        *,
        activation_hash: str | None = None,
        activation_expires_at: datetime | None = None,
    ) -> LNURLEntitlementBindingRecord:
        idem = self._idempotency_key(proof.proof_fingerprint, product.product_id, operation_type, principal.principal_hash if principal else None)
        binding_id = "lnbind_" + idem.split(":", 1)[1][:24]
        now = self.clock()
        return LNURLEntitlementBindingRecord(
            binding_id=binding_id,
            payment_proof_id=proof.proof_id,
            payment_proof_fingerprint=proof.proof_fingerprint,
            principal_hash=principal.principal_hash if principal else None,
            principal_type=principal.principal_type if principal else None,
            entitlement_id=None,
            product_id=product.product_id,
            plan_code=product.plan_code,
            operation_type=operation_type.value,
            binding_mode=(LNURLEntitlementBindingMode(principal.binding_mode).value if principal else LNURLEntitlementBindingMode.POST_PAYMENT_ACTIVATION.value),
            status=state.value,
            idempotency_key=idem,
            failure_reason=failure_reason,
            activation_reference_hash=activation_hash,
            activation_expires_at=activation_expires_at,
            policy_decision_hash=sha256_prefixed(failure_reason or "allow"),
            audit_event_hash=None,
            created_at=now,
            updated_at=now,
        )

    def _idempotency_key(self, proof_fingerprint: str, product_id: str, operation_type: LNURLEntitlementOperationType, principal_hash: str | None) -> str:
        return hmac_sha256_prefixed(self.config.idempotency_pepper, proof_fingerprint + product_id + operation_type.value + (principal_hash or "pending_principal"))

    def _activation_hash(self, activation_reference: str, proof_fingerprint: str) -> str:
        return hmac_sha256_prefixed(self.config.idempotency_pepper, activation_reference + proof_fingerprint)

    def _consumption_purpose(self, operation_type: LNURLEntitlementOperationType) -> str:
        return {
            LNURLEntitlementOperationType.RENEWAL: "subscription_renewal",
            LNURLEntitlementOperationType.UPGRADE: "plan_upgrade",
            LNURLEntitlementOperationType.PAYREGISTER_PLAN_ACTIVATION: "payregister_plan_activation",
            LNURLEntitlementOperationType.BUSINESS_INVOICE_ACTIVATION: "business_invoice_activation",
        }.get(operation_type, "subscription_entitlement")

    def _policy_context(
        self,
        proof: LNURLPaymentProof,
        product: LNURLSubscriptionProduct,
        principal: PrincipalReference,
        operation_type: LNURLEntitlementOperationType,
        request_context: AccessRequestContext,
        current: SubscriptionEntitlementRecord | None,
    ) -> dict[str, Any]:
        return {
            "action": "bind_lnurl_payment_to_principal",
            "actor_type": request_context.actor_type,
            "principal_hash": principal.principal_hash,
            "principal_status": principal.principal_status,
            "auth_method": request_context.auth_method,
            "wallet_proof_fresh": request_context.wallet_proof_fresh,
            "pop_session_status": "active" if request_context.pop_session_active else "none",
            "payment_method": "lnurl_pay",
            "payment_proof_status": proof.status,
            "verify_method": proof.settlement_method,
            "payment_amount": proof.amount_msat,
            "product_id": product.product_id,
            "plan_code": product.plan_code,
            "operation_type": operation_type.value,
            "current_entitlement": current.entitlement_id if current else None,
            "risk_level": request_context.risk_level,
            "activation_mode": principal.binding_mode,
        }

    def _audit(self, event_type: str, record: LNURLEntitlementBindingRecord, *, decision: str, reason_code: str, entitlement: SubscriptionEntitlementRecord | None = None) -> str | None:
        if not self.audit_chain:
            return None
        event = self.audit_chain.record_event(
            event_type=event_type,
            object_hash=sha256_prefixed(record.binding_id),
            metadata={
                "binding_id_hash": sha256_prefixed(record.binding_id),
                "payment_proof_fingerprint": record.payment_proof_fingerprint,
                "principal_hash": record.principal_hash,
                "principal_type": record.principal_type,
                "product_id": record.product_id,
                "plan_code": record.plan_code,
                "operation_type": record.operation_type,
                "decision": decision,
                "reason_code": reason_code,
                "new_entitlement_fingerprint": sha256_prefixed(entitlement.entitlement_id) if entitlement else None,
                "policy_hash": sha256_prefixed(record.policy_decision_hash or reason_code),
                "policy_epoch": 1,
                "timestamp": self.clock().isoformat(),
            },
        )
        return getattr(event, "event_hash", None)

    def _result(
        self,
        record: LNURLEntitlementBindingRecord,
        *,
        entitlement: SubscriptionEntitlementRecord | None = None,
        idempotent: bool,
    ) -> EntitlementBindingResult:
        entitlement = entitlement or (self.repository.find_active_entitlement_for_principal(record.principal_hash) if record.principal_hash else None)
        return EntitlementBindingResult(
            binding_id=record.binding_id,
            payment_proof_fingerprint=record.payment_proof_fingerprint,
            principal_hash=record.principal_hash,
            principal_type=record.principal_type,
            plan_code=record.plan_code,
            entitlement_id=record.entitlement_id or (entitlement.entitlement_id if entitlement else None),
            entitlement_status=entitlement.status if entitlement else None,
            binding_status=record.status,
            operation_type=record.operation_type,
            valid_from=entitlement.valid_from if entitlement else None,
            valid_until=entitlement.valid_until if entitlement else None,
            requires_wallet_activation=record.status == LNURLEntitlementBindingState.PENDING_PRINCIPAL.value,
            policy_refresh_required=record.status in {LNURLEntitlementBindingState.ACTIVE.value, LNURLEntitlementBindingState.RENEWAL_APPLIED.value, LNURLEntitlementBindingState.UPGRADE_APPLIED.value},
            audit_event_hash=record.audit_event_hash,
            idempotent_replay=idempotent,
            limitations=() if entitlement else ("no_api_access_until_wallet_activation",),
        )


def default_lnurl_subscription_products() -> dict[str, LNURLSubscriptionProduct]:
    amounts = {
        PlanCode.LITE.value: 1000,
        PlanCode.BASIC.value: 2000,
        PlanCode.PLUS.value: 3000,
        PlanCode.PRO.value: 4000,
        PlanCode.BUSINESS.value: 10000,
        PlanCode.ENTERPRISE.value: 50000,
    }
    return {
        plan: LNURLSubscriptionProduct(
            product_id=plan,
            plan_code=plan,
            amount_msat=amount,
            billing_period_days=30,
            metric_groups=(plan.removesuffix("_pass"),),
            scopes=("market:read",),
        )
        for plan, amount in amounts.items()
    }
