"""Central Policy Engine integration for LNURL-withdraw refunds and payouts.

A valid LNURL-withdraw k1 or callback never authorizes value transfer by itself.
This service builds narrow, auditable policy contexts for each payout stage and
uses the central AccessPolicyEngine as the final allow/deny authority, while
adding LNURL-specific refund linkage, velocity, role-boundary, step-up, quorum,
and idempotency invariants.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any, Protocol

from app.services.access.crypto.hashing import hash_canonical_json_prefixed, safe_hash_for_log
from app.services.access.policy_context import AccessPolicyContext
from app.services.access.policy_engine import AccessPolicyEngine
from app.services.lnurl.repositories.withdraw_requests import LNURLWithdrawRequestRecord


class LNURLPayoutPurpose(StrEnum):
    SUBSCRIPTION_REFUND = "subscription_refund"
    PAYREGISTER_REFUND = "payregister_refund"
    MERCHANT_REFUND = "merchant_refund"
    CASHBACK = "cashback"
    CUSTOMER_REWARD = "customer_reward"
    PARTNER_PAYOUT = "partner_payout"
    OPERATOR_REWARD = "operator_reward"
    BUG_BOUNTY = "bug_bounty"
    AFFILIATE_PAYOUT = "affiliate_payout"
    BUSINESS_EXPENSE_REIMBURSEMENT = "business_expense_reimbursement"
    TESTNET_FAUCET = "testnet_faucet"
    SIGNET_FAUCET = "signet_faucet"


class LNURLPayoutActorType(StrEnum):
    WALLET_PRINCIPAL = "wallet_principal"
    LIGHTNING_WALLET_PRINCIPAL = "lightning_wallet_principal"
    BUSINESS_OWNER = "business_owner"
    BUSINESS_ADMIN = "business_admin"
    BUSINESS_OPERATOR = "business_operator"
    CASHIER = "cashier"
    PAYREGISTER_DEVICE = "payregister_device"
    PARTNER_PRINCIPAL = "partner_principal"
    BUG_BOUNTY_REVIEWER = "bug_bounty_reviewer"
    SYSTEM_JOB = "system_job"


class LNURLPayoutRiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LNURLPayoutPolicyStage(StrEnum):
    REQUEST_CREATION = "request_creation"
    WITHDRAW_EXPOSURE = "withdraw_exposure"
    INVOICE_ACCEPTANCE = "invoice_acceptance"
    PAYMENT_EXECUTION = "payment_execution"
    RETRY = "retry"
    CANCEL = "cancel"


class LNURLPayoutPolicyDecision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    STEP_UP_REQUIRED = "step_up_required"
    QUORUM_REQUIRED = "quorum_required"
    COOLDOWN_REQUIRED = "cooldown_required"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    QUOTA_EXCEEDED = "quota_exceeded"
    AMOUNT_EXCEEDED = "amount_exceeded"
    ROLE_NOT_ALLOWED = "role_not_allowed"
    OBJECT_MISMATCH = "object_mismatch"
    ORIGINAL_PAYMENT_REQUIRED = "original_payment_required"
    REFUND_WINDOW_EXPIRED = "refund_window_expired"
    DUPLICATE_REQUEST = "duplicate_request"
    REVOKED = "revoked"
    EXPIRED = "expired"
    LOCKDOWN_ACTIVE = "lockdown_active"
    RECOVERY_LOCKED = "recovery_locked"
    ONLINE_CHECK_REQUIRED = "online_check_required"
    EXECUTOR_UNAVAILABLE = "executor_unavailable"


class LNURLPayoutRequestStatus(StrEnum):
    DRAFT = "draft"
    POLICY_PENDING = "policy_pending"
    STEP_UP_REQUIRED = "step_up_required"
    QUORUM_REQUIRED = "quorum_required"
    COOLDOWN = "cooldown"
    APPROVED = "approved"
    WITHDRAW_EXPOSED = "withdraw_exposed"
    INVOICE_RECEIVED = "invoice_received"
    PAYMENT_QUEUED = "payment_queued"
    PAYMENT_IN_PROGRESS = "payment_in_progress"
    PAYMENT_UNKNOWN = "payment_unknown"
    PAID = "paid"
    FAILED = "failed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REVOKED = "revoked"
    MANUAL_REVIEW = "manual_review"


PAYOUT_POLICY_ACTIONS: frozenset[str] = frozenset(
    {
        "lnurl_withdraw_request_create",
        "lnurl_withdraw_expose",
        "lnurl_withdraw_invoice_accept",
        "lnurl_withdraw_payment_execute",
        "lnurl_withdraw_retry",
        "lnurl_withdraw_cancel",
        "subscription_refund_approve",
        "payregister_refund_approve",
        "merchant_refund_approve",
        "business_payout_approve",
        "bug_bounty_payout_approve",
        "partner_payout_approve",
    }
)

PAYOUT_POLICY_SCOPES: frozenset[str] = frozenset(
    {
        "refunds:subscription:create",
        "refunds:subscription:approve",
        "refunds:payregister:create",
        "refunds:payregister:approve",
        "payouts:cashback:create",
        "payouts:partner:create",
        "payouts:partner:approve",
        "payouts:bounty:create",
        "payouts:bounty:approve",
        "payouts:execute",
        "lnurl:withdraw:read",
        "lnurl:withdraw:create",
        "lnurl:withdraw:approve",
        "lnurl:withdraw:cancel",
    }
)


@dataclass(frozen=True, slots=True)
class OriginalPaymentRefundState:
    payment_proof_hash: str
    workspace_hash: str | None
    principal_hash: str | None
    original_amount_msat: int
    refunded_amount_msat: int = 0
    settled_at: datetime | None = None
    refund_window_days: int = 30

    @property
    def remaining_refundable_msat(self) -> int:
        return max(0, self.original_amount_msat - self.refunded_amount_msat)


@dataclass(frozen=True, slots=True)
class LNURLPayoutPolicyContext:
    stage: LNURLPayoutPolicyStage | str
    purpose: LNURLPayoutPurpose | str
    actor_type: LNURLPayoutActorType | str
    amount_msat: int
    network: str = "bitcoin-mainnet"
    access_context: AccessPolicyContext | None = None
    original_payment: OriginalPaymentRefundState | None = None
    withdraw_request: LNURLWithdrawRequestRecord | None = None
    invoice_hash: str | None = None
    payment_hash_hash: str | None = None
    workspace_hash: str | None = None
    store_hash: str | None = None
    terminal_hash: str | None = None
    business_role: str | None = None
    step_up_fresh: bool = False
    human_intent_verified: bool = False
    quorum_approved: bool = False
    legacy_signature: bool = False
    browser_only_approval: bool = False
    recovery_only_session: bool = False
    lockdown_active: bool = False
    revoked_targets: tuple[str, ...] = ()
    system_job_preapproved: bool = False
    payout_request_id: str | None = None
    policy_approval_id: str | None = None
    payment_execution_id: str | None = None
    daily_amount_used_msat: int = 0
    rolling_amount_used_msat: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PolicyDecisionResult:
    decision: str
    allowed: bool
    reason_code: str
    policy_rule_id: str
    policy_hash: str
    risk_level: str
    required_auth: tuple[str, ...] = ()
    required_roles: tuple[str, ...] = ()
    required_quorum: int | None = None
    cooldown_until: datetime | None = None
    allowed_amount_msat: int | None = None
    retryable: bool = False
    audit_required: bool = True
    execution_approved: bool = False
    public_reason: str = "Payout policy decision is not allow."


@dataclass(frozen=True, slots=True)
class LNURLPayoutExecutionContext:
    payment_execution_id: str
    withdraw_request_hash: str
    policy_approval_id: str
    invoice_hash: str
    payment_hash_hash: str
    amount_msat: int
    network: str
    purpose: str


@dataclass(frozen=True, slots=True)
class LNURLPayoutExecutionResult:
    queued: bool
    status: str
    payment_execution_id: str
    reason_code: str = "queued"


class LNURLPayoutExecutor(Protocol):
    def validate_execution_context(self, context: LNURLPayoutExecutionContext) -> bool: ...
    def enqueue_payment(self, context: LNURLPayoutExecutionContext) -> LNURLPayoutExecutionResult: ...
    def get_payment_status(self, payment_execution_id: str) -> str: ...
    def cancel_payment_if_supported(self, payment_execution_id: str) -> bool: ...


class DisabledLNURLPayoutExecutor:
    def validate_execution_context(self, context: LNURLPayoutExecutionContext) -> bool:
        return False

    def enqueue_payment(self, context: LNURLPayoutExecutionContext) -> LNURLPayoutExecutionResult:
        return LNURLPayoutExecutionResult(False, LNURLPayoutRequestStatus.FAILED.value, context.payment_execution_id, "executor_unavailable")

    def get_payment_status(self, payment_execution_id: str) -> str:
        return LNURLPayoutRequestStatus.FAILED.value

    def cancel_payment_if_supported(self, payment_execution_id: str) -> bool:
        return False


class FakeLNURLPayoutExecutor:
    """Controlled test executor; never represents production payout execution."""

    def __init__(self) -> None:
        self.enqueued: dict[str, LNURLPayoutExecutionContext] = {}
        self._lock = threading.RLock()

    def validate_execution_context(self, context: LNURLPayoutExecutionContext) -> bool:
        return bool(context.policy_approval_id and context.invoice_hash and context.payment_hash_hash)

    def enqueue_payment(self, context: LNURLPayoutExecutionContext) -> LNURLPayoutExecutionResult:
        with self._lock:
            if context.payment_execution_id in self.enqueued:
                return LNURLPayoutExecutionResult(True, LNURLPayoutRequestStatus.PAYMENT_QUEUED.value, context.payment_execution_id, "duplicate_execution_id")
            self.enqueued[context.payment_execution_id] = context
            return LNURLPayoutExecutionResult(True, LNURLPayoutRequestStatus.PAYMENT_QUEUED.value, context.payment_execution_id)

    def get_payment_status(self, payment_execution_id: str) -> str:
        return LNURLPayoutRequestStatus.PAID.value if payment_execution_id in self.enqueued else LNURLPayoutRequestStatus.FAILED.value

    def cancel_payment_if_supported(self, payment_execution_id: str) -> bool:
        return False


class LNURLPayoutAuditSink(Protocol):
    def emit(self, event_type: str, payload: dict[str, Any]) -> str: ...


class InMemoryLNURLPayoutAuditSink:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def emit(self, event_type: str, payload: dict[str, Any]) -> str:
        safe_payload = {k: v for k, v in payload.items() if "k1" not in k and "invoice" not in k.lower() or k == "invoice_hash"}
        event_hash = hash_canonical_json_prefixed({"event_type": event_type, **safe_payload, "index": len(self.events)})
        self.events.append({"event_type": event_type, "event_hash": event_hash, **safe_payload})
        return event_hash


class InMemoryRefundLedger:
    def __init__(self) -> None:
        self._by_payment: dict[str, OriginalPaymentRefundState] = {}
        self._lock = threading.RLock()

    def put(self, state: OriginalPaymentRefundState) -> None:
        with self._lock:
            self._by_payment[state.payment_proof_hash] = state

    def get(self, payment_proof_hash: str) -> OriginalPaymentRefundState | None:
        with self._lock:
            return self._by_payment.get(payment_proof_hash)

    def reserve_refund(self, payment_proof_hash: str, amount_msat: int) -> OriginalPaymentRefundState:
        with self._lock:
            state = self._by_payment[payment_proof_hash]
            if amount_msat > state.remaining_refundable_msat:
                raise ValueError("refund_limit_exceeded")
            updated = replace(state, refunded_amount_msat=state.refunded_amount_msat + amount_msat)
            self._by_payment[payment_proof_hash] = updated
            return updated


@dataclass(frozen=True, slots=True)
class LNURLWithdrawPolicyLimits:
    global_max_msat: int = 10_000_000
    low_max_msat: int = 100_000
    medium_max_msat: int = 1_000_000
    high_max_msat: int = 5_000_000
    critical_max_msat: int = 25_000_000
    daily_max_msat: int = 10_000_000
    rolling_1h_max_msat: int = 5_000_000
    cooldown_seconds_after_policy_change: int = 300


class LNURLWithdrawPolicyService:
    def __init__(
        self,
        *,
        central_policy_engine: AccessPolicyEngine | None = None,
        audit_sink: LNURLPayoutAuditSink | None = None,
        refund_ledger: InMemoryRefundLedger | None = None,
        executor: LNURLPayoutExecutor | None = None,
        limits: LNURLWithdrawPolicyLimits | None = None,
        policy_epoch: int = 1,
    ) -> None:
        self.central_policy_engine = central_policy_engine or AccessPolicyEngine()
        self.audit_sink = audit_sink or InMemoryLNURLPayoutAuditSink()
        self.refund_ledger = refund_ledger or InMemoryRefundLedger()
        self.executor = executor or DisabledLNURLPayoutExecutor()
        self.limits = limits or LNURLWithdrawPolicyLimits()
        self.policy_epoch = policy_epoch
        self._approved_execution_ids: set[str] = set()
        self._paid_payment_hashes: set[str] = set()
        self._lock = threading.RLock()

    def evaluate_request_creation(self, context: LNURLPayoutPolicyContext) -> PolicyDecisionResult:
        return self._evaluate(context, LNURLPayoutPolicyStage.REQUEST_CREATION, "lnurl_payout_policy_requested")

    def evaluate_withdraw_exposure(self, context: LNURLPayoutPolicyContext) -> PolicyDecisionResult:
        return self._evaluate(context, LNURLPayoutPolicyStage.WITHDRAW_EXPOSURE, "lnurl_withdraw_exposed")

    def evaluate_invoice_acceptance(self, context: LNURLPayoutPolicyContext) -> PolicyDecisionResult:
        return self._evaluate(context, LNURLPayoutPolicyStage.INVOICE_ACCEPTANCE, "lnurl_withdraw_invoice_policy_allowed")

    def evaluate_payment_execution(self, context: LNURLPayoutPolicyContext) -> PolicyDecisionResult:
        decision = self._evaluate(context, LNURLPayoutPolicyStage.PAYMENT_EXECUTION, "lnurl_payout_policy_allowed")
        if decision.allowed and decision.execution_approved and context.payment_execution_id:
            with self._lock:
                self._approved_execution_ids.add(context.payment_execution_id)
        return decision

    def evaluate_retry(self, context: LNURLPayoutPolicyContext) -> PolicyDecisionResult:
        return self._evaluate(context, LNURLPayoutPolicyStage.RETRY, "lnurl_payout_policy_requested")

    def evaluate_cancel(self, context: LNURLPayoutPolicyContext) -> PolicyDecisionResult:
        return self._evaluate(context, LNURLPayoutPolicyStage.CANCEL, "lnurl_payout_policy_requested")

    def enqueue_payment(self, context: LNURLPayoutPolicyContext) -> LNURLPayoutExecutionResult:
        decision = self.evaluate_payment_execution(context)
        if not decision.allowed or not decision.execution_approved:
            self.audit_sink.emit("lnurl_payout_policy_denied", self._audit_payload(context, decision))
            return LNURLPayoutExecutionResult(False, LNURLPayoutRequestStatus.REJECTED.value, context.payment_execution_id or "missing", decision.reason_code)
        if not context.invoice_hash or not context.payment_hash_hash or not context.payment_execution_id:
            return LNURLPayoutExecutionResult(False, LNURLPayoutRequestStatus.REJECTED.value, context.payment_execution_id or "missing", "execution_context_missing")
        with self._lock:
            if context.payment_hash_hash in self._paid_payment_hashes:
                return LNURLPayoutExecutionResult(False, LNURLPayoutRequestStatus.REJECTED.value, context.payment_execution_id, "payment_hash_duplicate")
            request_hash = context.withdraw_request.withdraw_request_reference_hash if context.withdraw_request else safe_hash_for_log(context.payout_request_id or context.payment_execution_id)
            exec_ctx = LNURLPayoutExecutionContext(context.payment_execution_id, request_hash, context.policy_approval_id or decision.policy_hash, context.invoice_hash, context.payment_hash_hash, context.amount_msat, context.network, str(context.purpose))
            if not self.executor.validate_execution_context(exec_ctx):
                return LNURLPayoutExecutionResult(False, LNURLPayoutRequestStatus.FAILED.value, context.payment_execution_id, "executor_unavailable")
            result = self.executor.enqueue_payment(exec_ctx)
            if result.queued:
                self.audit_sink.emit("lnurl_payout_queued", self._audit_payload(context, decision))
            return result

    def record_paid(self, payment_hash_hash: str, *, execution_id: str) -> None:
        with self._lock:
            if payment_hash_hash in self._paid_payment_hashes:
                raise ValueError("payment_hash_duplicate")
            if execution_id not in self._approved_execution_ids:
                raise ValueError("execution_requires_prior_policy_approval")
            self._paid_payment_hashes.add(payment_hash_hash)
            self.audit_sink.emit("lnurl_payout_paid", {"payment_hash_commitment": safe_hash_for_log(payment_hash_hash), "payment_execution_id_hash": safe_hash_for_log(execution_id)})

    def _evaluate(self, context: LNURLPayoutPolicyContext, stage: LNURLPayoutPolicyStage, audit_event: str) -> PolicyDecisionResult:
        normalized = self._normalize_context(context, stage)
        decision = self._local_decision(normalized, stage)
        if decision is None:
            access_decision = self.central_policy_engine.evaluate(self._access_context(normalized, stage))
            decision = self._from_access_decision(normalized, stage, access_decision)
        event_type = audit_event if decision.allowed else "lnurl_payout_policy_denied"
        if decision.decision == LNURLPayoutPolicyDecision.STEP_UP_REQUIRED.value:
            event_type = "lnurl_payout_step_up_required"
        if decision.decision == LNURLPayoutPolicyDecision.QUORUM_REQUIRED.value:
            event_type = "lnurl_payout_quorum_required"
        self.audit_sink.emit(event_type, self._audit_payload(normalized, decision))
        return decision

    def _local_decision(self, context: LNURLPayoutPolicyContext, stage: LNURLPayoutPolicyStage) -> PolicyDecisionResult | None:
        try:
            purpose = LNURLPayoutPurpose(str(context.purpose))
            actor = LNURLPayoutActorType(str(context.actor_type))
        except ValueError:
            return self._decision(context, LNURLPayoutPolicyDecision.DENY, "unknown_purpose_or_actor", retryable=False)
        if context.lockdown_active:
            return self._decision(context, LNURLPayoutPolicyDecision.LOCKDOWN_ACTIVE, "lockdown_active")
        if context.revoked_targets:
            return self._decision(context, LNURLPayoutPolicyDecision.REVOKED, "revoked")
        if context.amount_msat <= 0:
            return self._decision(context, LNURLPayoutPolicyDecision.AMOUNT_EXCEEDED, "amount_invalid")
        risk = self._risk_level(context, purpose, actor)
        max_for_risk = {
            LNURLPayoutRiskLevel.LOW: self.limits.low_max_msat,
            LNURLPayoutRiskLevel.MEDIUM: self.limits.medium_max_msat,
            LNURLPayoutRiskLevel.HIGH: self.limits.high_max_msat,
            LNURLPayoutRiskLevel.CRITICAL: self.limits.critical_max_msat,
        }[risk]
        if context.amount_msat > min(max_for_risk, self.limits.global_max_msat):
            return self._decision(context, LNURLPayoutPolicyDecision.AMOUNT_EXCEEDED, "amount_over_limit", risk=risk.value)
        if context.daily_amount_used_msat + context.amount_msat > self.limits.daily_max_msat or context.rolling_amount_used_msat + context.amount_msat > self.limits.rolling_1h_max_msat:
            return self._decision(context, LNURLPayoutPolicyDecision.QUOTA_EXCEEDED, "rolling_limit_exceeded", risk=risk.value, retryable=True)
        if purpose in {LNURLPayoutPurpose.TESTNET_FAUCET, LNURLPayoutPurpose.SIGNET_FAUCET} and context.network == "bitcoin-mainnet":
            return self._decision(context, LNURLPayoutPolicyDecision.DENY, "faucet_policy_not_valid_on_mainnet", risk=risk.value)
        if purpose in {LNURLPayoutPurpose.SUBSCRIPTION_REFUND, LNURLPayoutPurpose.PAYREGISTER_REFUND, LNURLPayoutPurpose.MERCHANT_REFUND}:
            refund_decision = self._refund_decision(context, purpose, actor, risk)
            if refund_decision is not None:
                return refund_decision
        if actor == LNURLPayoutActorType.SYSTEM_JOB and stage != LNURLPayoutPolicyStage.PAYMENT_EXECUTION:
            return self._decision(context, LNURLPayoutPolicyDecision.ROLE_NOT_ALLOWED, "system_job_cannot_approve_own_payout", risk=risk.value)
        if actor == LNURLPayoutActorType.SYSTEM_JOB and not context.system_job_preapproved:
            return self._decision(context, LNURLPayoutPolicyDecision.ROLE_NOT_ALLOWED, "system_job_requires_prior_approval", risk=risk.value)
        if actor == LNURLPayoutActorType.PAYREGISTER_DEVICE and purpose not in {LNURLPayoutPurpose.PAYREGISTER_REFUND, LNURLPayoutPurpose.CASHBACK}:
            return self._decision(context, LNURLPayoutPolicyDecision.ROLE_NOT_ALLOWED, "payregister_device_cannot_approve_owner_payout", risk=risk.value)
        if actor == LNURLPayoutActorType.CASHIER and context.amount_msat > self.limits.medium_max_msat:
            return self._decision(context, LNURLPayoutPolicyDecision.ROLE_NOT_ALLOWED, "cashier_cannot_approve_high_value_refund", risk=risk.value, required_roles=("business_admin", "business_owner"))
        if context.legacy_signature and risk in {LNURLPayoutRiskLevel.HIGH, LNURLPayoutRiskLevel.CRITICAL}:
            return self._decision(context, LNURLPayoutPolicyDecision.STEP_UP_REQUIRED, "legacy_signature_not_sufficient", risk=risk.value, required_auth=("fresh_lnurl_auth", "wallet_step_up"))
        if context.browser_only_approval and risk == LNURLPayoutRiskLevel.CRITICAL:
            return self._decision(context, LNURLPayoutPolicyDecision.STEP_UP_REQUIRED, "browser_only_approval_not_sufficient", risk=risk.value, required_auth=("human_intent_signature",))
        if context.recovery_only_session and stage == LNURLPayoutPolicyStage.PAYMENT_EXECUTION:
            return self._decision(context, LNURLPayoutPolicyDecision.RECOVERY_LOCKED, "recovery_only_session_cannot_execute_payout", risk=risk.value)
        if risk == LNURLPayoutRiskLevel.HIGH and not context.step_up_fresh:
            return self._decision(context, LNURLPayoutPolicyDecision.STEP_UP_REQUIRED, "fresh_step_up_required", risk=risk.value, required_auth=("fresh_lnurl_auth_or_wallet_proof",))
        if risk == LNURLPayoutRiskLevel.CRITICAL:
            if not context.step_up_fresh or not context.human_intent_verified:
                return self._decision(context, LNURLPayoutPolicyDecision.STEP_UP_REQUIRED, "critical_payout_requires_human_intent", risk=risk.value, required_auth=("fresh_wallet_proof", "human_intent_signature"))
            if not context.quorum_approved:
                return self._decision(context, LNURLPayoutPolicyDecision.QUORUM_REQUIRED, "critical_payout_requires_quorum", risk=risk.value, required_quorum=2)
        if stage == LNURLPayoutPolicyStage.WITHDRAW_EXPOSURE:
            if context.withdraw_request is not None and context.withdraw_request.status.value not in {"lnurl_issued", "invoice_received"}:
                return self._decision(context, LNURLPayoutPolicyDecision.EXPIRED, "withdraw_not_exposable", risk=risk.value)
        if stage == LNURLPayoutPolicyStage.INVOICE_ACCEPTANCE:
            if not context.invoice_hash or not context.payment_hash_hash:
                return self._decision(context, LNURLPayoutPolicyDecision.DENY, "invoice_verification_required", risk=risk.value)
        if stage == LNURLPayoutPolicyStage.PAYMENT_EXECUTION:
            if not context.policy_approval_id:
                return self._decision(context, LNURLPayoutPolicyDecision.DENY, "execution_requires_prior_policy_approval", risk=risk.value)
            if not context.invoice_hash or not context.payment_hash_hash:
                return self._decision(context, LNURLPayoutPolicyDecision.DENY, "invoice_acceptance_required", risk=risk.value)
            return self._decision(context, LNURLPayoutPolicyDecision.ALLOW, "payment_execution_allowed", risk=risk.value, execution_approved=True)
        return None

    def _refund_decision(self, context: LNURLPayoutPolicyContext, purpose: LNURLPayoutPurpose, actor: LNURLPayoutActorType, risk: LNURLPayoutRiskLevel) -> PolicyDecisionResult | None:
        original = context.original_payment
        if original is None:
            return self._decision(context, LNURLPayoutPolicyDecision.ORIGINAL_PAYMENT_REQUIRED, "original_payment_required", risk=risk.value)
        if context.workspace_hash and original.workspace_hash and context.workspace_hash != original.workspace_hash:
            return self._decision(context, LNURLPayoutPolicyDecision.OBJECT_MISMATCH, "original_payment_workspace_mismatch", risk=risk.value)
        if context.amount_msat > original.remaining_refundable_msat:
            return self._decision(context, LNURLPayoutPolicyDecision.AMOUNT_EXCEEDED, "refund_amount_exceeds_remaining", risk=risk.value)
        if original.settled_at and datetime.now(UTC) > original.settled_at + timedelta(days=original.refund_window_days):
            return self._decision(context, LNURLPayoutPolicyDecision.REFUND_WINDOW_EXPIRED, "refund_window_expired", risk=risk.value, required_auth=("supervisor_step_up",))
        if actor == LNURLPayoutActorType.CASHIER and purpose != LNURLPayoutPurpose.PAYREGISTER_REFUND:
            return self._decision(context, LNURLPayoutPolicyDecision.ROLE_NOT_ALLOWED, "cashier_scope_limited_to_payregister_refund", risk=risk.value)
        self.audit_sink.emit("lnurl_refund_original_payment_validated", {"payment_proof_hash": safe_hash_for_log(original.payment_proof_hash), "amount_msat": context.amount_msat, "purpose": purpose.value})
        return None

    def _access_context(self, context: LNURLPayoutPolicyContext, stage: LNURLPayoutPolicyStage) -> AccessPolicyContext:
        base = context.access_context or AccessPolicyContext(plan_code="enterprise_pass", certificate_fingerprint="sha256:cert", pass_lookup_hash="hmac-sha256:pass", effective_scopes=set(PAYOUT_POLICY_SCOPES), metric_entitlements={"groups": []})
        risk = self._risk_level(context, LNURLPayoutPurpose(str(context.purpose)), LNURLPayoutActorType(str(context.actor_type))).value
        scope = _scope_for(context, stage)
        return replace(
            base,
            requested_scope=scope,
            requested_object_type="business_workspace" if context.workspace_hash else None,
            requested_object_id_hash=context.workspace_hash,
            request_risk_level=risk,
            business_role=context.business_role or _business_role_for_actor(context.actor_type),
            workspace_id_hash=context.workspace_hash,
            is_critical_action=risk == LNURLPayoutRiskLevel.CRITICAL,
            step_up_present=context.step_up_fresh,
            human_intent_verified=context.human_intent_verified,
            legacy_auth_context=context.legacy_signature,
            revocation_state={"allowed": not bool(context.revoked_targets), "revoked_targets": [{"target_type": t} for t in context.revoked_targets]},
            metadata={**base.metadata, "action": _action_for(context, stage), "purpose": str(context.purpose)},
        )

    def _from_access_decision(self, context: LNURLPayoutPolicyContext, stage: LNURLPayoutPolicyStage, access_decision: Any) -> PolicyDecisionResult:
        if access_decision.allowed:
            risk = self._risk_level(context, LNURLPayoutPurpose(str(context.purpose)), LNURLPayoutActorType(str(context.actor_type))).value
            return self._decision(context, LNURLPayoutPolicyDecision.ALLOW, "policy_allowed", risk=risk, execution_approved=stage == LNURLPayoutPolicyStage.PAYMENT_EXECUTION, retryable=True)
        decision_map = {
            "step_up_required": LNURLPayoutPolicyDecision.STEP_UP_REQUIRED,
            "quota_exceeded": LNURLPayoutPolicyDecision.QUOTA_EXCEEDED,
            "revoked": LNURLPayoutPolicyDecision.REVOKED,
            "expired": LNURLPayoutPolicyDecision.EXPIRED,
            "online_check_required": LNURLPayoutPolicyDecision.ONLINE_CHECK_REQUIRED,
            "lockdown_required": LNURLPayoutPolicyDecision.LOCKDOWN_ACTIVE,
        }
        mapped = decision_map.get(str(access_decision.decision), LNURLPayoutPolicyDecision.DENY)
        return self._decision(context, mapped, str(access_decision.reason_code), risk=context.access_context.request_risk_level if context.access_context else "medium", required_auth=("step_up",) if getattr(access_decision, "step_up_required", False) else ())

    def _normalize_context(self, context: LNURLPayoutPolicyContext, stage: LNURLPayoutPolicyStage) -> LNURLPayoutPolicyContext:
        return replace(context, stage=stage)

    def _risk_level(self, context: LNURLPayoutPolicyContext, purpose: LNURLPayoutPurpose, actor: LNURLPayoutActorType) -> LNURLPayoutRiskLevel:
        if purpose in {LNURLPayoutPurpose.TESTNET_FAUCET, LNURLPayoutPurpose.SIGNET_FAUCET, LNURLPayoutPurpose.CASHBACK, LNURLPayoutPurpose.CUSTOMER_REWARD} and context.amount_msat <= self.limits.low_max_msat:
            return LNURLPayoutRiskLevel.LOW
        if purpose in {LNURLPayoutPurpose.BUG_BOUNTY, LNURLPayoutPurpose.PARTNER_PAYOUT, LNURLPayoutPurpose.BUSINESS_EXPENSE_REIMBURSEMENT} or context.amount_msat > self.limits.high_max_msat:
            return LNURLPayoutRiskLevel.CRITICAL
        if context.amount_msat > self.limits.medium_max_msat or actor in {LNURLPayoutActorType.BUSINESS_OWNER, LNURLPayoutActorType.BUSINESS_ADMIN}:
            return LNURLPayoutRiskLevel.HIGH
        return LNURLPayoutRiskLevel.MEDIUM

    def _decision(self, context: LNURLPayoutPolicyContext, decision: LNURLPayoutPolicyDecision, reason: str, *, risk: str | None = None, required_auth: tuple[str, ...] = (), required_roles: tuple[str, ...] = (), required_quorum: int | None = None, retryable: bool = False, execution_approved: bool = False) -> PolicyDecisionResult:
        risk_level = risk or "medium"
        return PolicyDecisionResult(
            decision=decision.value,
            allowed=decision == LNURLPayoutPolicyDecision.ALLOW,
            reason_code=reason,
            policy_rule_id=f"lnurl_withdraw:{str(context.stage)}:{reason}",
            policy_hash=hash_canonical_json_prefixed({"epoch": self.policy_epoch, "stage": str(context.stage), "purpose": str(context.purpose), "risk": risk_level, "reason": reason}),
            risk_level=risk_level,
            required_auth=required_auth,
            required_roles=required_roles,
            required_quorum=required_quorum,
            allowed_amount_msat=context.amount_msat if decision == LNURLPayoutPolicyDecision.ALLOW else None,
            retryable=retryable,
            execution_approved=execution_approved,
        )

    def _audit_payload(self, context: LNURLPayoutPolicyContext, decision: PolicyDecisionResult) -> dict[str, Any]:
        return {
            "request_payout_hash": safe_hash_for_log(context.payout_request_id or context.withdraw_request.withdraw_request_reference_hash if context.withdraw_request else "missing"),
            "actor_hash": safe_hash_for_log((context.access_context.pass_lookup_hash if context.access_context else None) or str(context.actor_type)),
            "principal_type": str(context.actor_type),
            "workspace_hash": context.workspace_hash,
            "store_hash": context.store_hash,
            "purpose": str(context.purpose),
            "amount_msat": context.amount_msat,
            "unit": "msat",
            "policy_rule_id": decision.policy_rule_id,
            "policy_hash": decision.policy_hash,
            "policy_version": self.policy_epoch,
            "decision": decision.decision,
            "required_assurance": ",".join(decision.required_auth),
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }


def _business_role_for_actor(actor_type: str | LNURLPayoutActorType) -> str | None:
    return {
        LNURLPayoutActorType.BUSINESS_OWNER.value: "owner",
        LNURLPayoutActorType.BUSINESS_ADMIN.value: "admin",
        LNURLPayoutActorType.BUSINESS_OPERATOR.value: "operator",
        LNURLPayoutActorType.CASHIER.value: "cashier",
        LNURLPayoutActorType.PAYREGISTER_DEVICE.value: "device",
    }.get(str(actor_type))


def _action_for(context: LNURLPayoutPolicyContext, stage: LNURLPayoutPolicyStage) -> str:
    return {
        LNURLPayoutPolicyStage.REQUEST_CREATION: "lnurl_withdraw_request_create",
        LNURLPayoutPolicyStage.WITHDRAW_EXPOSURE: "lnurl_withdraw_expose",
        LNURLPayoutPolicyStage.INVOICE_ACCEPTANCE: "lnurl_withdraw_invoice_accept",
        LNURLPayoutPolicyStage.PAYMENT_EXECUTION: "lnurl_withdraw_payment_execute",
        LNURLPayoutPolicyStage.RETRY: "lnurl_withdraw_retry",
        LNURLPayoutPolicyStage.CANCEL: "lnurl_withdraw_cancel",
    }[stage]


def _scope_for(context: LNURLPayoutPolicyContext, stage: LNURLPayoutPolicyStage) -> str:
    if stage == LNURLPayoutPolicyStage.PAYMENT_EXECUTION:
        return "payouts:execute"
    if stage == LNURLPayoutPolicyStage.CANCEL:
        return "lnurl:withdraw:cancel"
    if stage == LNURLPayoutPolicyStage.WITHDRAW_EXPOSURE:
        return "lnurl:withdraw:read"
    purpose = str(context.purpose)
    if purpose == LNURLPayoutPurpose.SUBSCRIPTION_REFUND.value:
        return "refunds:subscription:approve" if stage == LNURLPayoutPolicyStage.INVOICE_ACCEPTANCE else "refunds:subscription:create"
    if purpose == LNURLPayoutPurpose.PAYREGISTER_REFUND.value:
        return "refunds:payregister:approve" if stage == LNURLPayoutPolicyStage.INVOICE_ACCEPTANCE else "refunds:payregister:create"
    if purpose == LNURLPayoutPurpose.PARTNER_PAYOUT.value:
        return "payouts:partner:approve"
    if purpose == LNURLPayoutPurpose.BUG_BOUNTY.value:
        return "payouts:bounty:approve"
    if purpose == LNURLPayoutPurpose.CASHBACK.value:
        return "payouts:cashback:create"
    return "lnurl:withdraw:create"


__all__ = [
    "DisabledLNURLPayoutExecutor",
    "FakeLNURLPayoutExecutor",
    "InMemoryLNURLPayoutAuditSink",
    "InMemoryRefundLedger",
    "LNURLPayoutActorType",
    "LNURLPayoutExecutionContext",
    "LNURLPayoutExecutionResult",
    "LNURLPayoutExecutor",
    "LNURLPayoutPolicyContext",
    "LNURLPayoutPolicyDecision",
    "LNURLPayoutPolicyStage",
    "LNURLPayoutPurpose",
    "LNURLPayoutRequestStatus",
    "LNURLPayoutRiskLevel",
    "LNURLWithdrawPolicyLimits",
    "LNURLWithdrawPolicyService",
    "OriginalPaymentRefundState",
    "PAYOUT_POLICY_ACTIONS",
    "PAYOUT_POLICY_SCOPES",
    "PolicyDecisionResult",
]
