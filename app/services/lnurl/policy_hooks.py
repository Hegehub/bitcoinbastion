"""LNURL integration hooks for the central Bastion Access Policy Engine.

Protocol validators prove LNURL syntax, signatures, invoices, payerData, and
settlement facts before reaching this module.  These hooks only normalize those
verified facts into :class:`AccessPolicyContext` and ask the existing central
:class:`AccessPolicyEngine` for the final authorization decision.  They never
perform cryptographic verification and never implement an independent allow path.

Evaluation order used by these hooks:
1. Normalize audit-safe LNURL context (hashes/fingerprints only).
2. Resolve explicit LNURL policy action and actor type.
3. Attach revocation state from the configured revocation checker.
4. Attach verified protocol state (k1, signature, domain, settlement, invoice).
5. Call the central Policy Engine.
6. Emit an audit-safe LNURL policy event.
7. Record low-cardinality metrics.
8. Return the structured central policy decision.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol

from app.domain.access.plans import PlanCode
from app.services.access.crypto.hashing import hash_canonical_json_prefixed
from app.services.access.policy_context import (
    AccessPolicyContext,
    AccessPolicyDecision,
    AuthenticationAssuranceLevel,
    PolicyActorType,
    PolicyAuthMethod,
    PolicySourceChannel,
)
from app.services.access.policy_engine import AccessPolicyEngine
import app.services.access.policy_reasons as reasons
from app.services.lnurl.metrics import MetricEvent


class LNURLPolicyAction(StrEnum):
    LNURL_AUTH_REGISTER = "lnurl_auth_register"
    LNURL_AUTH_LOGIN = "lnurl_auth_login"
    LNURL_AUTH_LINK = "lnurl_auth_link"
    LNURL_AUTH_STEP_UP = "lnurl_auth_step_up"
    LNURL_AUTH_ADD_DEVICE = "lnurl_auth_add_device"
    LNURL_AUTH_LOCKDOWN = "lnurl_auth_lockdown"
    LNURL_AUTH_RECOVERY_FACTOR = "lnurl_auth_recovery_factor"
    LNURL_PAY_CREATE_REQUEST = "lnurl_pay_create_request"
    LNURL_PAY_ISSUE_INVOICE = "lnurl_pay_issue_invoice"
    LNURL_PAY_VERIFY_SETTLEMENT = "lnurl_pay_verify_settlement"
    LNURL_PAY_CREATE_PAYMENT_PROOF = "lnurl_pay_create_payment_proof"
    LNURL_PAY_ISSUE_ENTITLEMENT = "lnurl_pay_issue_entitlement"
    LNURL_PAY_UPGRADE_SUBSCRIPTION = "lnurl_pay_upgrade_subscription"
    LNURL_PAY_RENEW_SUBSCRIPTION = "lnurl_pay_renew_subscription"
    LIGHTNING_ADDRESS_RESOLVE = "lightning_address_resolve"
    LIGHTNING_ADDRESS_CREATE = "lightning_address_create"
    LIGHTNING_ADDRESS_UPDATE = "lightning_address_update"
    LIGHTNING_ADDRESS_DISABLE = "lightning_address_disable"
    LNURL_WITHDRAW_CREATE = "lnurl_withdraw_create"
    LNURL_WITHDRAW_ACCEPT_INVOICE = "lnurl_withdraw_accept_invoice"
    LNURL_WITHDRAW_PAY = "lnurl_withdraw_pay"
    LNURL_WITHDRAW_CANCEL = "lnurl_withdraw_cancel"
    LNURL_REFUND_CREATE = "lnurl_refund_create"
    LNURL_REFUND_PAY = "lnurl_refund_pay"
    LNURL_PARTNER_PAYOUT = "lnurl_partner_payout"
    LNURL_REWARD_PAYOUT = "lnurl_reward_payout"
    PAYREGISTER_LNURL_CREATE_PAYMENT = "payregister_lnurl_create_payment"
    PAYREGISTER_LNURL_ISSUE_INVOICE = "payregister_lnurl_issue_invoice"
    PAYREGISTER_LNURL_REFUND = "payregister_lnurl_refund"
    PAYREGISTER_LNURL_SETTLEMENT = "payregister_lnurl_settlement"
    PAYREGISTER_LNURL_TERMINAL_ENROLL = "payregister_lnurl_terminal_enroll"
    LNURL_PAYERDATA_BIND_AUTH = "lnurl_payerdata_bind_auth"
    LNURL_SUCCESS_ACTION_CREATE = "lnurl_success_action_create"
    LNURL_COMMENT_STORE = "lnurl_comment_store"


class LNURLPolicyOperation(StrEnum):
    AUTH = "auth"
    PAY = "pay"
    VERIFY = "verify"
    WITHDRAW = "withdraw"
    LIGHTNING_ADDRESS_RESOLVE = "lightning_address_resolve"
    PAYER_DATA_BIND = "payer_data_bind"
    SUCCESS_ACTION = "success_action"
    COMMENT = "comment"


class LNURLPolicyAuditSink(Protocol):
    def emit(self, event_type: str, payload: dict[str, Any]) -> str: ...


class LNURLPolicyMetricsSink(Protocol):
    def record(self, name: str, labels: dict[str, str] | None = None, value: float = 1.0) -> MetricEvent: ...


RevocationChecker = Callable[[AccessPolicyContext], Mapping[str, Any]]
PolicyEngineFactory = Callable[[], AccessPolicyEngine]


@dataclass(frozen=True, slots=True)
class LNURLPolicyHookConfig:
    policy_hash: str = "sha256:lnurl-policy-v1"
    policy_epoch: int = 1
    allow_public_lightning_address_degraded: bool = False
    public_lightning_address_plan: PlanCode = PlanCode.LITE
    default_plan: PlanCode = PlanCode.LITE


@dataclass(frozen=True, slots=True)
class LNURLPolicyInput:
    action: LNURLPolicyAction | str
    actor_type: PolicyActorType | str = PolicyActorType.LIGHTNING_WALLET_PRINCIPAL
    principal_hash: str | None = None
    actor_hash: str | None = None
    auth_methods: frozenset[PolicyAuthMethod | str] = field(default_factory=frozenset)
    authentication_assurance: AuthenticationAssuranceLevel | str = AuthenticationAssuranceLevel.STANDARD
    requested_scope: str | None = None
    requested_scopes: frozenset[str] = field(default_factory=frozenset)
    effective_scopes: set[str] = field(default_factory=set)
    metric_group: str | None = None
    resource_type: str | None = None
    object_hash: str | None = None
    request_origin: str | None = None
    auth_domain: str | None = None
    device_key_fingerprint: str | None = None
    session_hash: str | None = None
    session_status: str = "active"
    subscription_plan: PlanCode | str | None = None
    entitlement_status: str = "active"
    business_role: str | None = None
    risk_level: str = "low"
    verification_strength: str | None = None
    revocation_epoch: int | None = None
    recovery_state: str | None = None
    step_up_freshness: str | None = None
    step_up_present: bool = False
    human_intent_verified: bool = False
    audit_required: bool = True
    policy_hash: str | None = None
    policy_epoch: int | None = None
    idempotency_key_hash: str | None = None
    previous_state: str | None = None
    requested_state: str | None = None
    object_version: int | None = None
    data: dict[str, Any] = field(default_factory=dict)


class InMemoryLNURLPolicyAuditSink:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def emit(self, event_type: str, payload: dict[str, Any]) -> str:
        safe = _safe_payload(payload)
        event_hash = hash_canonical_json_prefixed({"event_type": event_type, "payload": safe, "index": len(self.events)})
        self.events.append({"event_type": event_type, "event_hash": event_hash, **safe})
        return event_hash


class InMemoryLNURLPolicyMetricsSink:
    def __init__(self) -> None:
        self.events: list[MetricEvent] = []

    def record(self, name: str, labels: dict[str, str] | None = None, value: float = 1.0) -> MetricEvent:
        labels = labels or {}
        forbidden = {"principal_hash", "k1_hash", "wallet_address", "linking_key", "invoice_hash", "payment_id", "email", "merchant_id"}
        if set(labels) & forbidden:
            raise ValueError("forbidden high-cardinality LNURL policy metric label")
        event = MetricEvent(name=name, labels=dict(labels), value=value)
        self.events.append(event)
        return event


class LNURLPolicyHooks:
    def __init__(
        self,
        *,
        policy_engine_factory: PolicyEngineFactory | None = None,
        audit_sink: LNURLPolicyAuditSink | None = None,
        metrics_sink: LNURLPolicyMetricsSink | None = None,
        revocation_checker: RevocationChecker | None = None,
        config: LNURLPolicyHookConfig | None = None,
    ) -> None:
        self.policy_engine_factory = policy_engine_factory or AccessPolicyEngine
        self.audit_sink = audit_sink or InMemoryLNURLPolicyAuditSink()
        self.metrics_sink = metrics_sink or InMemoryLNURLPolicyMetricsSink()
        self.revocation_checker = revocation_checker
        self.config = config or LNURLPolicyHookConfig()

    def authorize_auth_registration(self, **kwargs: Any) -> AccessPolicyDecision:
        return self._authorize(LNURLPolicyInput(action=LNURLPolicyAction.LNURL_AUTH_REGISTER, requested_state="principal_registered", data=kwargs, **_base_auth(kwargs)))

    def authorize_auth_login(self, **kwargs: Any) -> AccessPolicyDecision:
        return self._authorize(LNURLPolicyInput(action=LNURLPolicyAction.LNURL_AUTH_LOGIN, requested_state="session_issued", data=kwargs, **_base_auth(kwargs)))

    def authorize_principal_link(self, **kwargs: Any) -> AccessPolicyDecision:
        return self._authorize(LNURLPolicyInput(action=LNURLPolicyAction.LNURL_AUTH_LINK, risk_level="high", requested_state="principal_linked", data=kwargs, **_base_auth(kwargs)))

    def authorize_auth_step_up(self, **kwargs: Any) -> AccessPolicyDecision:
        return self._authorize(LNURLPolicyInput(action=LNURLPolicyAction.LNURL_AUTH_STEP_UP, risk_level="high", requested_state="step_up_approved", data=kwargs, **_base_auth(kwargs)))

    def authorize_subscription_payment_request(self, **kwargs: Any) -> AccessPolicyDecision:
        return self._authorize(self._input(LNURLPolicyAction.LNURL_PAY_CREATE_REQUEST, LNURLPolicyOperation.PAY, kwargs, requested_state="payment_request_created"))

    def authorize_entitlement_issuance(self, **kwargs: Any) -> AccessPolicyDecision:
        return self._authorize(self._input(LNURLPolicyAction.LNURL_PAY_ISSUE_ENTITLEMENT, LNURLPolicyOperation.PAY, kwargs, requested_state="entitlement_issued"))

    def authorize_lightning_address_resolution(self, **kwargs: Any) -> AccessPolicyDecision:
        return self._authorize(self._input(LNURLPolicyAction.LIGHTNING_ADDRESS_RESOLVE, LNURLPolicyOperation.LIGHTNING_ADDRESS_RESOLVE, kwargs, actor_type=kwargs.get("actor_type", PolicyActorType.SERVICE_ACCOUNT), auth_methods=frozenset({PolicyAuthMethod.INTERNAL_SERVICE_IDENTITY}), requested_state="address_resolved"))

    def authorize_withdraw_request_creation(self, **kwargs: Any) -> AccessPolicyDecision:
        return self._withdraw(LNURLPolicyAction.LNURL_WITHDRAW_CREATE, "request_creation", kwargs)

    def authorize_withdraw_invoice_acceptance(self, **kwargs: Any) -> AccessPolicyDecision:
        return self._withdraw(LNURLPolicyAction.LNURL_WITHDRAW_ACCEPT_INVOICE, "invoice_acceptance", kwargs)

    def authorize_withdraw_payment(self, **kwargs: Any) -> AccessPolicyDecision:
        return self._withdraw(LNURLPolicyAction.LNURL_WITHDRAW_PAY, "payment_execution", kwargs)

    def authorize_payregister_payment(self, **kwargs: Any) -> AccessPolicyDecision:
        return self._authorize(self._input(LNURLPolicyAction.PAYREGISTER_LNURL_CREATE_PAYMENT, LNURLPolicyOperation.PAY, kwargs, actor_type=PolicyActorType.PAYREGISTER_DEVICE, requested_scope="payregister:payment:create", requested_state="payregister_payment_created"))

    def authorize_payregister_refund(self, **kwargs: Any) -> AccessPolicyDecision:
        return self._authorize(self._input(LNURLPolicyAction.PAYREGISTER_LNURL_REFUND, LNURLPolicyOperation.WITHDRAW, kwargs, actor_type=kwargs.get("actor_type", PolicyActorType.LIGHTNING_WALLET_PRINCIPAL), requested_scope="refunds:payregister:approve", risk_level="high", requested_state="payregister_refund_approved"))

    def authorize_payer_data_binding(self, **kwargs: Any) -> AccessPolicyDecision:
        return self._authorize(self._input(LNURLPolicyAction.LNURL_PAYERDATA_BIND_AUTH, LNURLPolicyOperation.PAYER_DATA_BIND, kwargs, requested_state="payerdata_bound"))

    def authorize_success_action_creation(self, **kwargs: Any) -> AccessPolicyDecision:
        return self._authorize(self._input(LNURLPolicyAction.LNURL_SUCCESS_ACTION_CREATE, LNURLPolicyOperation.SUCCESS_ACTION, kwargs, actor_type=PolicyActorType.SERVICE_ACCOUNT, auth_methods=frozenset({PolicyAuthMethod.INTERNAL_SERVICE_IDENTITY}), requested_state="success_action_created"))

    def authorize_comment_storage(self, **kwargs: Any) -> AccessPolicyDecision:
        return self._authorize(self._input(LNURLPolicyAction.LNURL_COMMENT_STORE, LNURLPolicyOperation.COMMENT, kwargs, requested_state="comment_stored"))

    def _withdraw(self, action: LNURLPolicyAction, stage: str, kwargs: dict[str, Any]) -> AccessPolicyDecision:
        return self._authorize(self._input(action, LNURLPolicyOperation.WITHDRAW, kwargs, risk_level=kwargs.get("risk_level", "high"), requested_state=stage))

    def _input(self, action: LNURLPolicyAction, operation: LNURLPolicyOperation, kwargs: dict[str, Any], **overrides: Any) -> LNURLPolicyInput:
        data = {**kwargs, "lnurl_operation": operation.value, **overrides}
        fields = {name: data.pop(name) for name in list(data) if name in LNURLPolicyInput.__dataclass_fields__ and name != "data"}
        return LNURLPolicyInput(action=action, data=data, **fields)

    def _authorize(self, request: LNURLPolicyInput) -> AccessPolicyDecision:
        try:
            context = self._to_policy_context(request)
            if self.revocation_checker is not None:
                context = replace(context, revocation_state=dict(self.revocation_checker(context)))
            decision = self.policy_engine_factory().evaluate(context)
        except Exception as exc:
            decision = AccessPolicyDecision(
                decision="deny",
                allowed=False,
                reason_code=reasons.POLICY_ENGINE_UNAVAILABLE,
                human_reason="LNURL policy authorization is unavailable.",
                audit_required=True,
                requested_action=str(request.action),
                actor_type=request.actor_type,
                actor_hash=request.actor_hash,
                policy_hash=request.policy_hash or self.config.policy_hash,
                policy_epoch=request.policy_epoch or self.config.policy_epoch,
                evaluated_at=datetime.now(UTC),
                safe_user_message="LNURL policy authorization is unavailable.",
                internal_reason_details={"exception_type": type(exc).__name__},
            )
        self._audit_decision(request, decision)
        self._record_metrics(request, decision)
        return decision

    def _to_policy_context(self, request: LNURLPolicyInput) -> AccessPolicyContext:
        action = _value(request.action)
        data = dict(request.data)
        operation = data.get("lnurl_operation") or _operation_for_action(action)
        auth_methods = request.auth_methods or _default_methods_for_action(action)
        scope = request.requested_scope or _scope_for_action(action)
        effective_scopes = set(request.effective_scopes)
        if scope:
            effective_scopes.add(scope)
        plan = request.subscription_plan or data.get("plan_code") or self.config.default_plan
        return AccessPolicyContext(
            actor_type=request.actor_type,
            actor_hash=request.actor_hash or request.principal_hash,
            principal_hash=request.principal_hash,
            actor_status=data.get("actor_status", "active"),
            revocation_state=data.get("revocation_state", {}),
            principal_type=_value(request.actor_type),
            auth_methods=auth_methods,
            auth_method=next(iter(auth_methods), None),
            authentication_assurance=request.authentication_assurance,
            requested_action=action,
            action=action,
            requested_internal_action=data.get("requested_internal_action", action),
            resource=request.resource_type,
            object_hash=request.object_hash,
            request_origin=request.request_origin,
            origin=request.request_origin,
            auth_domain=request.auth_domain or data.get("challenge_domain"),
            device_id=request.device_key_fingerprint,
            session_id_hash=request.session_hash,
            session_status=request.session_status,
            plan_code=plan,
            entitlement_status=request.entitlement_status,
            effective_scopes=effective_scopes,
            requested_scope=scope,
            requested_scopes=request.requested_scopes,
            requested_metric_group=request.metric_group,
            requested_object_type=request.resource_type,
            requested_object_id_hash=request.object_hash,
            business_role=request.business_role,
            request_risk_level=request.risk_level,
            verification_strength=request.verification_strength,
            policy_epoch=request.policy_epoch or self.config.policy_epoch,
            policy_hash=request.policy_hash or self.config.policy_hash,
            revocation_epoch=request.revocation_epoch,
            recovery_state=request.recovery_state,
            step_up_freshness=request.step_up_freshness,
            step_up_present=request.step_up_present,
            human_intent_verified=request.human_intent_verified,
            audit_required=request.audit_required,
            idempotency_key_hash=request.idempotency_key_hash,
            previous_state=request.previous_state,
            requested_state=request.requested_state,
            object_version=request.object_version,
            lnurl_operation=str(operation),
            lnurl_action=data.get("lnurl_action", "auth" if operation == "auth" else None),
            lnurl_auth_action=data.get("lnurl_auth_action"),
            k1_hash=data.get("k1_hash"),
            k1_status=data.get("k1_status"),
            k1_expires_at=data.get("k1_expires_at"),
            k1_used_at=data.get("k1_used_at"),
            linking_key_hash=data.get("linking_key_hash"),
            signature_verified=data.get("signature_verified"),
            challenge_domain=data.get("challenge_domain"),
            callback_domain=data.get("callback_domain"),
            domain_matches=data.get("domain_matches"),
            challenge_action=data.get("challenge_action"),
            wallet_compatibility_level=data.get("wallet_compatibility_level"),
            payment_request_hash=data.get("payment_request_hash"),
            payment_status=data.get("payment_status"),
            invoice_hash=data.get("invoice_hash"),
            invoice_status=data.get("invoice_status"),
            amount_msat=data.get("amount_msat"),
            expected_amount_msat=data.get("expected_amount_msat"),
            product_code=data.get("product_code"),
            metadata_hash=data.get("metadata_hash"),
            callback_hash=data.get("callback_hash"),
            settlement_verified=data.get("settlement_verified"),
            settlement_method=data.get("settlement_method"),
            payment_proof_hash=data.get("payment_proof_hash"),
            payer_data_present=bool(data.get("payer_data_present", False)),
            payer_data_auth_verified=bool(data.get("payer_data_auth_verified", False)),
            withdraw_request_hash=data.get("withdraw_request_hash"),
            withdraw_status=data.get("withdraw_status"),
            withdraw_k1_hash=data.get("withdraw_k1_hash"),
            maximum_allowed_msat=data.get("maximum_allowed_msat"),
            invoice_valid=data.get("invoice_valid"),
            payout_policy_id=data.get("payout_policy_id"),
            payout_recipient_context_hash=data.get("payout_recipient_context_hash"),
            refund_reference_hash=data.get("refund_reference_hash"),
            cooldown_satisfied=data.get("cooldown_satisfied"),
            quorum_satisfied=data.get("quorum_satisfied"),
            lightning_address_hash=data.get("lightning_address_hash"),
            address_name_hash=data.get("address_name_hash"),
            address_domain=data.get("address_domain"),
            address_status=data.get("address_status"),
            merchant_hash=data.get("merchant_hash"),
            custom_domain_verified=data.get("custom_domain_verified"),
            payregister_store_hash=data.get("payregister_store_hash"),
            payregister_terminal_hash=data.get("payregister_terminal_hash"),
            source_channel=data.get("source_channel", PolicySourceChannel.LNURL_CALLBACK),
            success_action_type=data.get("success_action_type"),
            comment_present=bool(data.get("comment_present", False)),
            metadata={"lnurl_policy_hook": True, "idempotency_key_hash": request.idempotency_key_hash},
        )

    def _audit_decision(self, request: LNURLPolicyInput, decision: AccessPolicyDecision) -> None:
        payload = {
            "decision": decision.decision,
            "reason_code": decision.reason_code,
            "actor_type": _value(request.actor_type),
            "principal_hash": request.principal_hash,
            "object_hash": request.object_hash,
            "action": _value(request.action),
            "risk_level": request.risk_level,
            "verification_strength": request.verification_strength,
            "policy_hash": decision.policy_hash or request.policy_hash or self.config.policy_hash,
            "policy_epoch": decision.policy_epoch or request.policy_epoch or self.config.policy_epoch,
            "revocation_epoch": request.revocation_epoch,
            "audit_correlation_id": request.data.get("audit_correlation_id"),
        }
        self.audit_sink.emit(_event_type_for_decision(request.action, decision), payload)

    def _record_metrics(self, request: LNURLPolicyInput, decision: AccessPolicyDecision) -> None:
        labels = {
            "action_category": _category_for_action(_value(request.action)),
            "decision": decision.decision,
            "reason_category": _reason_category(decision.reason_code),
            "actor_type": _value(request.actor_type),
            "verification_strength": str(request.verification_strength or request.authentication_assurance),
            "environment": "test",
        }
        self.metrics_sink.record("bastion_lnurl_policy_decisions_total", labels)
        if not decision.allowed:
            self.metrics_sink.record("bastion_lnurl_policy_denials_total", labels)
            if _category_for_action(_value(request.action)) == "entitlement":
                self.metrics_sink.record("bastion_lnurl_entitlement_denied_total", labels)
            if _category_for_action(_value(request.action)) == "withdraw":
                self.metrics_sink.record("bastion_lnurl_withdraw_denied_total", labels)
        if decision.decision == "step_up_required":
            self.metrics_sink.record("bastion_lnurl_policy_step_up_total", labels)
        if decision.decision == "quorum_required":
            self.metrics_sink.record("bastion_lnurl_policy_quorum_required_total", labels)


def _base_auth(kwargs: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "actor_type": kwargs.get("actor_type", PolicyActorType.LIGHTNING_WALLET_PRINCIPAL),
        "principal_hash": kwargs.get("principal_hash"),
        "actor_hash": kwargs.get("actor_hash", kwargs.get("principal_hash")),
        "auth_methods": kwargs.get("auth_methods", frozenset({PolicyAuthMethod.LNURL_AUTH})),
        "authentication_assurance": kwargs.get("authentication_assurance", AuthenticationAssuranceLevel.STANDARD),
        "session_hash": kwargs.get("session_hash"),
        "device_key_fingerprint": kwargs.get("device_key_fingerprint"),
        "subscription_plan": kwargs.get("subscription_plan", PlanCode.LITE),
        "effective_scopes": kwargs.get("effective_scopes", set()),
        "step_up_present": bool(kwargs.get("step_up_present", False)),
        "human_intent_verified": bool(kwargs.get("human_intent_verified", False)),
    }


def _default_methods_for_action(action: str) -> frozenset[PolicyAuthMethod | str]:
    if action.startswith("lnurl_auth"):
        return frozenset({PolicyAuthMethod.LNURL_AUTH})
    if action.startswith("lightning_address") or action.startswith("lnurl_success_action"):
        return frozenset({PolicyAuthMethod.INTERNAL_SERVICE_IDENTITY})
    return frozenset({PolicyAuthMethod.LNURL_AUTH, PolicyAuthMethod.DEVICE_POP, PolicyAuthMethod.SESSION_POP})


def _scope_for_action(action: str) -> str | None:
    return {
        "lnurl_withdraw_create": "lnurl:withdraw:create",
        "lnurl_withdraw_accept_invoice": "lnurl:withdraw:approve",
        "lnurl_withdraw_pay": "payouts:execute",
        "lnurl_refund_create": "refunds:subscription:create",
        "lnurl_refund_pay": "refunds:subscription:approve",
        "lnurl_partner_payout": "payouts:partner:approve",
        "lnurl_reward_payout": "payouts:bounty:approve",
        "payregister_lnurl_create_payment": "payregister:payment:create",
        "payregister_lnurl_refund": "refunds:payregister:approve",
    }.get(action)


def _operation_for_action(action: str) -> str:
    if action.startswith("lnurl_auth"):
        return LNURLPolicyOperation.AUTH.value
    if action.startswith("lnurl_pay"):
        return LNURLPolicyOperation.PAY.value
    if action.startswith("lightning_address"):
        return LNURLPolicyOperation.LIGHTNING_ADDRESS_RESOLVE.value
    if "withdraw" in action or "refund" in action or "payout" in action:
        return LNURLPolicyOperation.WITHDRAW.value
    if "payerdata" in action:
        return LNURLPolicyOperation.PAYER_DATA_BIND.value
    if "success_action" in action:
        return LNURLPolicyOperation.SUCCESS_ACTION.value
    return "unknown"


def _event_type_for_decision(action: LNURLPolicyAction | str, decision: AccessPolicyDecision) -> str:
    if decision.decision == "allow":
        base = "lnurl_policy_allow"
    elif decision.decision == "step_up_required":
        base = "lnurl_policy_step_up_required"
    elif decision.decision == "quorum_required":
        base = "lnurl_policy_quorum_required"
    else:
        base = "lnurl_policy_deny"
    category = _category_for_action(_value(action))
    specific = {
        "auth": "lnurl_auth_policy_evaluated",
        "entitlement": "lnurl_pay_entitlement_policy_evaluated",
        "withdraw": "lnurl_withdraw_policy_evaluated",
        "address": "lightning_address_policy_evaluated",
        "payer_data": "payer_data_policy_evaluated",
        "success_action": "success_action_policy_evaluated",
    }.get(category)
    return specific or base


def _category_for_action(action: str) -> str:
    if action.startswith("lnurl_auth"):
        return "auth"
    if "entitlement" in action or action.startswith("lnurl_pay"):
        return "entitlement"
    if action.startswith("lightning_address"):
        return "address"
    if "withdraw" in action or "refund" in action or "payout" in action:
        return "withdraw"
    if "payerdata" in action:
        return "payer_data"
    if "success_action" in action:
        return "success_action"
    return "metadata"


def _reason_category(reason_code: str) -> str:
    return reason_code.split("_", 1)[0] if reason_code else "unknown"


def _value(value: Any) -> str:
    return str(value.value if hasattr(value, "value") else value)


def _safe_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    forbidden_parts = ("raw", "signature", "invoice", "preimage", "address", "email", "session_token", "private", "seed")
    safe: dict[str, Any] = {}
    for key, value in payload.items():
        lower = key.lower()
        if lower in {"invoice_hash", "principal_hash"} or lower.endswith("_hash") or lower.endswith("_fingerprint"):
            safe[key] = value
            continue
        if any(part in lower for part in forbidden_parts):
            continue
        safe[key] = value
    return safe


__all__ = [
    "InMemoryLNURLPolicyAuditSink",
    "InMemoryLNURLPolicyMetricsSink",
    "LNURLPolicyAction",
    "LNURLPolicyHookConfig",
    "LNURLPolicyHooks",
    "LNURLPolicyInput",
    "LNURLPolicyOperation",
]
