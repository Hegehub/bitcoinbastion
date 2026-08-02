"""Central Proof-of-Access authorization policy engine.

The engine evaluates explicit Access context. It never treats session validity,
Access Pass, bearer token, password, or global user identifier as sufficient for
protected access.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.domain.access.plans import PlanCode, normalize_plan_code, plan_rank
from app.domain.access.scopes import ACCESS_SCOPES, FORBIDDEN_SCOPES
from app.services.access.metric_catalog import get_metric_group, get_metric_group_for_metric
from app.services.access.metric_costs import get_metric_cost
from app.services.access.plan_entitlements import required_plan_for_metric_group, validate_history_range_allowed, validate_interval_allowed
from app.services.access.policy_context import (
    AccessPolicyContext,
    AccessPolicyDecision,
    PolicyActorType,
    PolicyAuthMethod,
)
import app.services.access.policy_reasons as reasons

POLICY_DECISION_ALLOW = "allow"
POLICY_DECISION_DENY = "deny"
POLICY_DECISION_UPGRADE_REQUIRED = "upgrade_required"
POLICY_DECISION_STEP_UP_REQUIRED = "step_up_required"
POLICY_DECISION_QUOTA_EXCEEDED = "quota_exceeded"
POLICY_DECISION_METRIC_NOT_ALLOWED = "metric_not_allowed"
POLICY_DECISION_REVOKED = "revoked"
POLICY_DECISION_EXPIRED = "expired"
POLICY_DECISION_RECOVERY_REQUIRED = "recovery_required"
POLICY_DECISION_ONLINE_CHECK_REQUIRED = "online_check_required"
POLICY_DECISION_READ_ONLY = "read_only"
POLICY_DECISION_LOCKDOWN_REQUIRED = "lockdown_required"
POLICY_DECISION_QUORUM_REQUIRED = "quorum_required"
POLICY_DECISION_DEVICE_BINDING_REQUIRED = "device_binding_required"
POLICY_DECISION_PAYMENT_NOT_SETTLED = "payment_not_settled"
POLICY_DECISION_PROOF_TOO_WEAK = "proof_too_weak"
POLICY_DECISION_ROLE_NOT_ALLOWED = "role_not_allowed"
POLICY_DECISION_RESOURCE_NOT_ALLOWED = "resource_not_allowed"
POLICY_DECISION_LOCKDOWN_ACTIVE = "lockdown_active"
POLICY_DECISION_PAYMENT_VERIFICATION_REQUIRED = "payment_verification_required"
POLICY_DECISION_RATE_LIMITED = "rate_limited"
POLICY_DECISION_AMOUNT_LIMIT_EXCEEDED = "amount_limit_exceeded"
POLICY_DECISION_MANUAL_REVIEW_REQUIRED = "manual_review_required"

HIGH_RISK_ACTIONS = frozenset({
    "add_device", "device_add", "revoke_device", "create_api_key", "increase_child_scopes",
    "create_delegated_pass", "enable_automation", "start_recovery",
    "valuable_lnurl_withdraw", "assign_business_operator", "assign_cashier_role",
})
CRITICAL_ACTIONS = frozenset(
    {
        "create_api_key",
        "increase_scope",
        "export_data",
        "create_delegated_pass",
        "enable_payregister_admin",
        "treasury_policy_change",
        "recovery_change",
        "device_add",
        "lockdown_disable",
        "business_role_assignment",
        "enterprise_policy_change",
        "subscription_upgrade_with_new_permissions",
    }
)
BUSINESS_OBJECT_TYPES = frozenset({"business_workspace", "payregister_device", "child_api_key", "delegated_pass"})
SUPPORTED_OBJECT_TYPES = BUSINESS_OBJECT_TYPES | frozenset({"trace_report", "treasury_request", "audit_event", "metric_query"})
BUSINESS_ROLE_SCOPES = {
    "owner": {"*business"},
    "admin": {"payregister:devices:read", "payregister:operator:read", "payregister:shifts:read", "payregister:invoices:read", "refunds:subscription:create", "refunds:subscription:approve", "refunds:payregister:create", "refunds:payregister:approve", "payouts:cashback:create", "payouts:partner:approve", "payouts:bounty:approve", "lnurl:withdraw:approve", "lnurl:withdraw:create", "lnurl:withdraw:read", "lnurl:withdraw:cancel"},
    "operator": {"payregister:operator:read", "payregister:shifts:read", "refunds:payregister:create", "refunds:payregister:approve", "lnurl:withdraw:create", "lnurl:withdraw:read"},
    "cashier": {"payregister:payment:create", "payregister:refund:request", "payregister:invoices:read", "payregister:shifts:read", "refunds:payregister:create", "lnurl:withdraw:read"},
    "analyst": {"payregister:metrics:read", "business:audit:read"},
    "viewer": {"payregister:metrics:read"},
    "device": {"payregister:devices:read", "lnurl:withdraw:read"},
    "bot": {"payregister:metrics:read"},
}


class AccessPolicyEngine:
    def evaluate(self, context: AccessPolicyContext | None) -> AccessPolicyDecision:
        self._current_context = context if isinstance(context, AccessPolicyContext) else None
        if context is None or not isinstance(context, AccessPolicyContext):
            return self._deny(POLICY_DECISION_DENY, reasons.MISSING_ACCESS_CONTEXT, "Access context is missing.")
        actor_decision = self._check_actor_and_auth(context)
        if actor_decision is not None:
            return actor_decision
        if context.issuer_envelope_verified is False:
            return self._deny(
                POLICY_DECISION_DENY,
                "issuer_envelope_invalid",
                "Bastion issuer envelope verification failed.",
            )
        if context.signature_requirement_policy in {"hybrid_required", "pq_required"} and context.granted_crypto_assurance not in {"hybrid_transition", "post_quantum"}:
            return self._deny(
                POLICY_DECISION_DENY,
                "required_hybrid_signature_unavailable",
                "Required issuer signature capabilities are unavailable.",
            )
        if context.legacy_auth_context:
            return self._deny(POLICY_DECISION_DENY, reasons.LEGACY_AUTH_NOT_ALLOWED, "Legacy auth context is not allowed.")
        plan = self._normalize_plan(context)
        if plan is None:
            return self._deny(POLICY_DECISION_DENY, reasons.MISSING_ACCESS_CONTEXT, "Unknown Access plan.")
        status_decision = self._check_statuses(context, plan)
        if status_decision is not None:
            return status_decision
        revocation_decision = self._check_revocation(context, plan)
        if revocation_decision is not None:
            return revocation_decision
        integrity_decision = self._check_access_integrity(context, plan)
        if integrity_decision is not None:
            return integrity_decision
        offline_decision = self._check_offline(context, plan)
        if offline_decision is not None:
            return offline_decision
        scope_decision = self._check_scope(context, plan)
        if scope_decision is not None:
            return scope_decision
        metric_decision = self.check_metric_entitlement(context, plan)
        if metric_decision is not None:
            return metric_decision
        quota_decision = self.check_quota(context, plan)
        if quota_decision is not None:
            return quota_decision
        object_decision = self._check_object_access(context, plan)
        if object_decision is not None:
            return object_decision
        role_decision = self.check_business_role(context, plan)
        if role_decision is not None:
            return role_decision
        lnurl_decision = self._check_lnurl(context, plan)
        if lnurl_decision is not None:
            return lnurl_decision
        risk_decision = self._check_risk_and_step_up(context, plan)
        if risk_decision is not None:
            return risk_decision
        return AccessPolicyDecision(
            decision=POLICY_DECISION_ALLOW,
            allowed=True,
            reason_code=reasons.ACCESS_ALLOWED,
            human_reason="Access policy allowed the request.",
            current_plan=plan,
            requested_scope=context.requested_scope,
            requested_metric_group=context.requested_metric_group,
            quota_remaining=self._quota_remaining(context),
            audit_required=context.is_critical_action or True,
            actor_type=context.actor_type,
            actor_hash=context.actor_hash,
            auth_methods_used=tuple(str(m.value if hasattr(m, "value") else m) for m in context.auth_methods),
            authentication_assurance=context.authentication_assurance,
            requested_action=context.requested_action or context.metadata.get("action"),
            resource_type=context.resource_type or context.requested_object_type,
            resource_hash=context.resource_hash or context.requested_object_id_hash,
            policy_epoch=context.policy_epoch,
            policy_hash=context.policy_hash,
            evaluated_at=datetime.now(UTC),
            safe_user_message="Access policy allowed the request.",
            offline_allowed=not context.offline_mode,
        )
        return WalletLNURLStepUpPolicy().evaluate_step_up_requirement(step_context)

    def evaluate_step_up_requirement(self, context: AccessPolicyContext) -> Any:
        from app.services.wallet_auth.step_up_policy import StepUpPolicyContext, WalletLNURLStepUpPolicy

        step_context = StepUpPolicyContext(
            action=str(context.requested_action or context.action or context.metadata.get("action", "read_public_status")),
            actor_type=context.actor_type or "unknown",
            principal_hash=context.principal_hash,
            device_key_fingerprint=str(context.device_id) if context.device_id is not None else None,
            session_hash=context.session_id_hash,
            auth_method=context.auth_method or context.primary_auth_method,
            current_verification_strength=context.authentication_assurance,
            wallet_proof_freshness_seconds=_int_or_none(context.metadata.get("wallet_proof_freshness_seconds")),
            lnurl_proof_freshness_seconds=_int_or_none(context.metadata.get("lnurl_proof_freshness_seconds")),
            session_age_seconds=_int_or_none(context.metadata.get("session_age_seconds")),
            device_trust_level=str(context.metadata.get("device_trust_level", "standard")),
            device_risk_score=context.device_risk_score,
            subscription_plan=context.plan_code,
            requested_scopes=frozenset(context.requested_scopes or ({context.requested_scope} if context.requested_scope else set())),
            effective_scopes=frozenset(context.effective_scopes),
            requested_object=context.resource_hash or context.requested_object_id_hash or context.resource_type or context.requested_object_type,
            requested_expiry=str(context.metadata.get("requested_expiry")) if context.metadata.get("requested_expiry") else None,
            requested_amount_msat=context.amount_msat,
            business_role=context.business_role,
            payregister_role=str(context.payregister_context.get("role")) if context.payregister_context.get("role") else None,
            recovery_state=context.recovery_state,
            lockdown_state=str(context.revocation_state.get("lockdown_state")) if isinstance(context.revocation_state, dict) and context.revocation_state.get("lockdown_state") else None,
            sovereign_mode=bool(context.metadata.get("sovereign_mode")),
            existing_quorum_state=context.metadata.get("quorum_state"),
            revocation_state=context.revocation_state,
            policy_epoch=context.policy_epoch,
            policy_hash=context.policy_hash,
            intent_hash=str(context.metadata.get("intent_hash")) if context.metadata.get("intent_hash") else None,
            provided_proofs=tuple(context.metadata.get("step_up_proofs", ())),
            human_intent_verified=context.human_intent_verified,
            access_certificate_present=bool(context.access_certificate_fingerprint or context.certificate_fingerprint),
            quota_state=context.quota_state,
            metric_group=context.requested_metric_group,
        )
        return WalletLNURLStepUpPolicy().evaluate_step_up_requirement(step_context)

    def evaluate_step_up_requirement(self, context: AccessPolicyContext) -> Any:
        from app.services.wallet_auth.step_up_policy import StepUpPolicyContext, WalletLNURLStepUpPolicy

        step_context = StepUpPolicyContext(
            action=str(context.requested_action or context.action or context.metadata.get("action", "read_public_status")),
            actor_type=context.actor_type or "unknown",
            principal_hash=context.principal_hash,
            device_key_fingerprint=str(context.device_id) if context.device_id is not None else None,
            session_hash=context.session_id_hash,
            auth_method=context.auth_method or context.primary_auth_method,
            current_verification_strength=context.authentication_assurance,
            wallet_proof_freshness_seconds=_int_or_none(context.metadata.get("wallet_proof_freshness_seconds")),
            lnurl_proof_freshness_seconds=_int_or_none(context.metadata.get("lnurl_proof_freshness_seconds")),
            session_age_seconds=_int_or_none(context.metadata.get("session_age_seconds")),
            device_trust_level=str(context.metadata.get("device_trust_level", "standard")),
            device_risk_score=context.device_risk_score,
            subscription_plan=context.plan_code,
            requested_scopes=frozenset(context.requested_scopes or ({context.requested_scope} if context.requested_scope else set())),
            effective_scopes=frozenset(context.effective_scopes),
            requested_object=context.resource_hash or context.requested_object_id_hash or context.resource_type or context.requested_object_type,
            requested_expiry=str(context.metadata.get("requested_expiry")) if context.metadata.get("requested_expiry") else None,
            requested_amount_msat=context.amount_msat,
            business_role=context.business_role,
            payregister_role=str(context.payregister_context.get("role")) if context.payregister_context.get("role") else None,
            recovery_state=context.recovery_state,
            lockdown_state=str(context.revocation_state.get("lockdown_state")) if isinstance(context.revocation_state, dict) and context.revocation_state.get("lockdown_state") else None,
            sovereign_mode=bool(context.metadata.get("sovereign_mode")),
            existing_quorum_state=context.metadata.get("quorum_state"),
            revocation_state=context.revocation_state,
            policy_epoch=context.policy_epoch,
            policy_hash=context.policy_hash,
            intent_hash=str(context.metadata.get("intent_hash")) if context.metadata.get("intent_hash") else None,
            provided_proofs=tuple(context.metadata.get("step_up_proofs", ())),
            human_intent_verified=context.human_intent_verified,
            access_certificate_present=bool(context.access_certificate_fingerprint or context.certificate_fingerprint),
            quota_state=context.quota_state,
            metric_group=context.requested_metric_group,
        )
        return WalletLNURLStepUpPolicy().evaluate_step_up_requirement(step_context)

    def evaluate_step_up_requirement(self, context: AccessPolicyContext) -> Any:
        from app.services.wallet_auth.step_up_policy import StepUpPolicyContext, WalletLNURLStepUpPolicy

        step_context = StepUpPolicyContext(
            action=str(context.requested_action or context.action or context.metadata.get("action", "read_public_status")),
            actor_type=context.actor_type or "unknown",
            principal_hash=context.principal_hash,
            device_key_fingerprint=str(context.device_id) if context.device_id is not None else None,
            session_hash=context.session_id_hash,
            auth_method=context.auth_method or context.primary_auth_method,
            current_verification_strength=context.authentication_assurance,
            wallet_proof_freshness_seconds=_int_or_none(context.metadata.get("wallet_proof_freshness_seconds")),
            lnurl_proof_freshness_seconds=_int_or_none(context.metadata.get("lnurl_proof_freshness_seconds")),
            session_age_seconds=_int_or_none(context.metadata.get("session_age_seconds")),
            device_trust_level=str(context.metadata.get("device_trust_level", "standard")),
            device_risk_score=context.device_risk_score,
            subscription_plan=context.plan_code,
            requested_scopes=frozenset(context.requested_scopes or ({context.requested_scope} if context.requested_scope else set())),
            effective_scopes=frozenset(context.effective_scopes),
            requested_object=context.resource_hash or context.requested_object_id_hash or context.resource_type or context.requested_object_type,
            requested_expiry=str(context.metadata.get("requested_expiry")) if context.metadata.get("requested_expiry") else None,
            requested_amount_msat=context.amount_msat,
            business_role=context.business_role,
            payregister_role=str(context.payregister_context.get("role")) if context.payregister_context.get("role") else None,
            recovery_state=context.recovery_state,
            lockdown_state=str(context.revocation_state.get("lockdown_state")) if isinstance(context.revocation_state, dict) and context.revocation_state.get("lockdown_state") else None,
            sovereign_mode=bool(context.metadata.get("sovereign_mode")),
            existing_quorum_state=context.metadata.get("quorum_state"),
            revocation_state=context.revocation_state,
            policy_epoch=context.policy_epoch,
            policy_hash=context.policy_hash,
            intent_hash=str(context.metadata.get("intent_hash")) if context.metadata.get("intent_hash") else None,
            provided_proofs=tuple(context.metadata.get("step_up_proofs", ())),
            human_intent_verified=context.human_intent_verified,
            access_certificate_present=bool(context.access_certificate_fingerprint or context.certificate_fingerprint),
            quota_state=context.quota_state,
            metric_group=context.requested_metric_group,
        )
        return WalletLNURLStepUpPolicy().evaluate_step_up_requirement(step_context)

    def has_scope(self, context: AccessPolicyContext, requested_scope: str | None = None) -> bool:
        scope = requested_scope or context.requested_scope
        if scope is None:
            return True
        if scope in FORBIDDEN_SCOPES or scope not in ACCESS_SCOPES:
            return False
        return scope in context.effective_scopes

    def check_metric_entitlement(self, context: AccessPolicyContext, plan: PlanCode | None = None) -> AccessPolicyDecision | None:
        if context.requested_metric_group is None and context.requested_metric_name is None:
            return None
        current_plan = plan or self._normalize_plan(context)
        if current_plan is None:
            return self._deny(POLICY_DECISION_DENY, reasons.METRIC_NOT_ALLOWED, "Unknown plan for metric request.")
        metric_group = context.requested_metric_group
        if metric_group is None and context.requested_metric_name is not None:
            metric_group = get_metric_group_for_metric(context.requested_metric_name)
        if metric_group is None or get_metric_group(metric_group) is None:
            return self._deny(
                POLICY_DECISION_METRIC_NOT_ALLOWED,
                reasons.METRIC_NOT_ALLOWED,
                "Metric group is unknown.",
                current_plan=current_plan,
                requested_metric_group=metric_group,
            )
        allowed_groups = set(context.metric_entitlements.get("groups", []))
        if metric_group not in allowed_groups:
            required_plan = required_plan_for_metric_group(metric_group)
            if required_plan is not None and plan_rank(required_plan) > plan_rank(current_plan):
                return self._deny(
                    POLICY_DECISION_UPGRADE_REQUIRED,
                    reasons.METRIC_REQUIRES_HIGHER_PLAN,
                    "Metric requires a higher plan.",
                    current_plan=current_plan,
                    required_plan=required_plan,
                    requested_metric_group=metric_group,
                    upgrade_available=True,
                )
            return self._deny(
                POLICY_DECISION_METRIC_NOT_ALLOWED,
                reasons.METRIC_NOT_ALLOWED,
                "Metric group is not allowed by entitlement.",
                current_plan=current_plan,
                requested_metric_group=metric_group,
            )
        if context.requested_interval and not validate_interval_allowed(current_plan, context.requested_interval):
            return self._deny(POLICY_DECISION_DENY, reasons.METRIC_NOT_ALLOWED, "Requested interval is not allowed.", current_plan=current_plan)
        if context.requested_history_days is not None and not validate_history_range_allowed(current_plan, context.requested_history_days):
            return self._deny(POLICY_DECISION_DENY, reasons.METRIC_NOT_ALLOWED, "Requested history range is not allowed.", current_plan=current_plan)
        if context.requested_metric_name is not None:
            try:
                cost = get_metric_cost(context.requested_metric_name)
            except ValueError:
                return self._deny(POLICY_DECISION_METRIC_NOT_ALLOWED, reasons.METRIC_NOT_ALLOWED, "Metric is unknown.", current_plan=current_plan)
            remaining = self._quota_remaining(context)
            if remaining is not None and remaining < cost:
                return self._quota_decision(context, current_plan)
        return None

    def check_quota(self, context: AccessPolicyContext, plan: PlanCode | None = None) -> AccessPolicyDecision | None:
        current_plan = plan or self._normalize_plan(context)
        if context.quota_state.get("exhausted") is True:
            return self._quota_decision(context, current_plan)
        remaining = self._quota_remaining(context)
        if remaining is not None and remaining < 0:
            return self._quota_decision(context, current_plan)
        return None

    def check_business_role(self, context: AccessPolicyContext, plan: PlanCode | None = None) -> AccessPolicyDecision | None:
        if context.requested_object_type not in BUSINESS_OBJECT_TYPES and not (context.requested_scope or "").startswith("payregister:"):
            return None
        role = (context.business_role or "").strip().lower()
        if not role or role not in BUSINESS_ROLE_SCOPES:
            return self._deny(POLICY_DECISION_DENY, reasons.BUSINESS_ROLE_DENIED, "Business role is required.", current_plan=plan)
        if role == "owner":
            return None
        requested_scope = context.requested_scope
        if requested_scope and requested_scope not in BUSINESS_ROLE_SCOPES[role]:
            return self._deny(POLICY_DECISION_DENY, reasons.BUSINESS_ROLE_DENIED, "Business role does not allow scope.", current_plan=plan)
        return None

    def _check_actor_and_auth(self, context: AccessPolicyContext) -> AccessPolicyDecision | None:
        actor = self._actor(context)
        if actor is None:
            if context.certificate_fingerprint and context.pass_lookup_hash:
                return None  # explicit legacy adapter for existing Access Certificate PoP sessions
            return self._deny(POLICY_DECISION_DENY, reasons.UNKNOWN_ACTOR_TYPE, "Actor type is not recognized.")
        if actor == PolicyActorType.SERVICE_ACCOUNT and PolicyAuthMethod.INTERNAL_SERVICE_IDENTITY.value not in self._methods(context):
            return self._deny(POLICY_DECISION_DENY, reasons.WALLET_PROOF_TOO_WEAK, "Service account identity is required.")
        if actor == PolicyActorType.RECOVERY_ACTOR and not self._is_recovery_action(context):
            return self._deny(POLICY_DECISION_RECOVERY_REQUIRED, reasons.RECOVERY_ONLY_ACTOR, "Recovery actor cannot access normal APIs.")
        if context.actor_status in {"inactive", "disabled", "suspended"}:
            return self._deny(POLICY_DECISION_DENY, reasons.PRINCIPAL_INACTIVE, "Principal is inactive.")
        if context.actor_status == "revoked":
            return self._deny(POLICY_DECISION_REVOKED, reasons.PRINCIPAL_REVOKED, "Principal is revoked.")
        if actor == PolicyActorType.LIGHTNING_WALLET_PRINCIPAL:
            if context.lightning_address_hash and PolicyAuthMethod.LNURL_AUTH.value not in self._methods(context):
                return self._deny(POLICY_DECISION_DENY, reasons.LIGHTNING_ADDRESS_NOT_IDENTITY, "Lightning Address is not authentication.")
            if self._is_treasury_action(context):
                return self._deny(POLICY_DECISION_DENY, reasons.LIGHTNING_PRINCIPAL_NOT_TREASURY_PROOF, "Lightning auth is not treasury proof.", step_up_required=True)
        if actor == PolicyActorType.BITCOIN_WALLET_PRINCIPAL and PolicyAuthMethod.LEGACY_BITCOIN_MESSAGE.value in self._methods(context) and self._category(context) in {"high", "critical", "sovereign"}:
            return self._deny(POLICY_DECISION_PROOF_TOO_WEAK, reasons.LEGACY_SIGNATURE_NOT_ALLOWED, "Legacy Bitcoin signatures are compatibility-only.")
        if actor in {PolicyActorType.CHILD_API_KEY, PolicyActorType.DELEGATED_PASS, PolicyActorType.BOT}:
            if context.parent_actor_status in {"revoked", "disabled", "inactive"}:
                return self._deny(POLICY_DECISION_REVOKED, reasons.PARENT_REVOKED, "Parent actor is not active.")
            parent_scopes = set(context.metadata.get("parent_scopes", context.effective_scopes))
            delegated_scopes = set(context.metadata.get("delegated_scopes", context.effective_scopes))
            if not delegated_scopes <= parent_scopes or (context.requested_scope and context.requested_scope not in delegated_scopes):
                return self._deny(POLICY_DECISION_DENY, reasons.CHILD_SCOPE_EXCEEDS_PARENT, "Delegated scope is not allowed.")
            if actor == PolicyActorType.BOT and self._category(context) == "critical":
                return self._deny(POLICY_DECISION_PROOF_TOO_WEAK, reasons.WALLET_PROOF_TOO_WEAK, "Bot cannot approve critical actions.")
        if actor == PolicyActorType.ACCESS_CERTIFICATE:
            if context.certificate_status not in {None, "active"} or not (context.access_certificate_fingerprint or context.certificate_fingerprint):
                return self._deny(POLICY_DECISION_DENY, reasons.ACCESS_CERTIFICATE_REQUIRED, "Active Access Certificate is required.")
        return None

    def _check_lnurl(self, context: AccessPolicyContext, plan: PlanCode) -> AccessPolicyDecision | None:
        if context.lnurl_operation == "auth" or context.k1_status is not None or context.lnurl_k1_status is not None:
            if context.signature_verified is False:
                return self._deny(POLICY_DECISION_DENY, reasons.LNURL_SIGNATURE_INVALID, "LNURL signature is invalid.", current_plan=plan)
            if context.domain_matches is False:
                return self._deny(POLICY_DECISION_DENY, reasons.LNURL_DOMAIN_MISMATCH, "LNURL domain mismatch.", current_plan=plan)
            internal_action = context.requested_internal_action or context.requested_action or context.metadata.get("action")
            if context.lnurl_action == "auth" and not internal_action:
                return self._deny(POLICY_DECISION_DENY, reasons.GENERIC_LNURL_AUTH_NOT_ALLOWED, "LNURL-auth must map to an internal action.", current_plan=plan)
            status = context.k1_status or context.lnurl_k1_status
            if status == "unknown":
                return self._deny(POLICY_DECISION_DENY, reasons.LNURL_K1_UNKNOWN, "LNURL challenge is invalid.", current_plan=plan)
            if status == "expired":
                return self._deny(POLICY_DECISION_EXPIRED, reasons.LNURL_K1_EXPIRED, "LNURL challenge expired.", current_plan=plan)
            if status == "reused":
                return self._deny(POLICY_DECISION_REVOKED, reasons.LNURL_K1_REUSED, "LNURL challenge was already used.", current_plan=plan)
            if context.auth_domain and context.lnurl_auth_domain and context.auth_domain != context.lnurl_auth_domain:
                return self._deny(POLICY_DECISION_DENY, reasons.LNURL_DOMAIN_MISMATCH, "LNURL domain mismatch.", current_plan=plan)
            action = context.requested_action or context.metadata.get("action")
            if context.requested_action in {"lnurl_auth_register", "lnurl_auth_login", "lnurl_auth_link"} and context.requested_internal_action not in {None, context.requested_action}:
                return self._deny(POLICY_DECISION_DENY, reasons.LNURL_ACTION_MISMATCH, "LNURL action mismatch.", current_plan=plan)
            if context.challenge_action and internal_action and context.challenge_action not in {internal_action, context.lnurl_auth_action, context.lnurl_action} and not str(context.challenge_action).startswith("lnurl_auth_"):
                return self._deny(POLICY_DECISION_DENY, reasons.LNURL_ACTION_MISMATCH, "LNURL action mismatch.", current_plan=plan)
            if context.lnurl_auth_action and action and context.lnurl_auth_action not in {action, "login", "register", "link", "step_up"}:
                return self._deny(POLICY_DECISION_DENY, reasons.LNURL_ACTION_MISMATCH, "LNURL action mismatch.", current_plan=plan)
        if context.amount_msat is not None and context.expected_amount_msat is not None and context.amount_msat != context.expected_amount_msat:
            reason = reasons.INVOICE_AMOUNT_MISMATCH if context.lnurl_operation == "withdraw" else reasons.AMOUNT_MISMATCH
            return self._deny(POLICY_DECISION_AMOUNT_LIMIT_EXCEEDED, reason, "Amount does not match policy.", current_plan=plan)
        if context.maximum_allowed_msat is not None and context.amount_msat is not None and context.amount_msat > context.maximum_allowed_msat:
            return self._deny(POLICY_DECISION_AMOUNT_LIMIT_EXCEEDED, reasons.AMOUNT_LIMIT_EXCEEDED, "Amount exceeds policy limit.", current_plan=plan)
        if context.lnurl_operation == "pay":
            pay_status = context.payment_status or context.lnurl_payment_status
            invoice_status = context.invoice_status
            if pay_status in {"expired", "payment_request_expired"}:
                return self._deny(POLICY_DECISION_EXPIRED, reasons.PAYMENT_REQUEST_EXPIRED, "Payment request is expired.", current_plan=plan)
            if context.previous_state == "entitlement_issued" or context.requested_state == "duplicate_entitlement":
                return self._deny(POLICY_DECISION_DENY, reasons.DUPLICATE_ENTITLEMENT, "Entitlement was already issued.", current_plan=plan)
            if invoice_status in {"issued", "pending"} or pay_status in {"invoice_issued", "pending", "invoice_created"}:
                return self._deny(POLICY_DECISION_PAYMENT_NOT_SETTLED, reasons.PAYMENT_NOT_SETTLED, "Payment is not settled.", current_plan=plan)
            if context.settlement_verified is False:
                return self._deny(POLICY_DECISION_PAYMENT_VERIFICATION_REQUIRED, reasons.SETTLEMENT_NOT_VERIFIED, "Payment settlement is not verified.", current_plan=plan)
            if context.payment_proof_hash is None and context.requested_state in {"entitlement_issued", "payment_proof_created"}:
                return self._deny(POLICY_DECISION_PAYMENT_VERIFICATION_REQUIRED, reasons.PAYMENT_PROOF_INVALID, "Payment proof is required.", current_plan=plan)
        if context.lnurl_operation == "lightning_address_resolve":
            if context.address_status in {"disabled", "inactive"}:
                return self._deny(POLICY_DECISION_DENY, reasons.ADDRESS_DISABLED, "Lightning Address is unavailable.", current_plan=plan)
            if context.address_status == "revoked" or context.payregister_terminal_hash and context.revocation_state.get("terminal_revoked"):
                return self._deny(POLICY_DECISION_REVOKED, reasons.TERMINAL_REVOKED, "Lightning Address is unavailable.", current_plan=plan)
            if context.custom_domain_verified is False:
                return self._deny(POLICY_DECISION_DENY, reasons.CUSTOM_DOMAIN_UNVERIFIED, "Lightning Address domain is unavailable.", current_plan=plan)
        if context.lnurl_operation == "withdraw":
            if context.withdraw_status in {"expired"}:
                return self._deny(POLICY_DECISION_EXPIRED, reasons.WITHDRAW_REQUEST_EXPIRED, "Withdraw request is expired.", current_plan=plan)
            if context.withdraw_status in {"revoked"}:
                return self._deny(POLICY_DECISION_REVOKED, reasons.WITHDRAW_REQUEST_REVOKED, "Withdraw request is revoked.", current_plan=plan)
            if context.withdraw_status in {"paid", "payment_queued"} and context.requested_state == "payment_execution":
                return self._deny(POLICY_DECISION_DENY, reasons.WITHDRAW_ALREADY_PAID, "Withdraw request already paid.", current_plan=plan)
            if context.invoice_valid is False:
                return self._deny(POLICY_DECISION_DENY, reasons.INVOICE_INVALID, "Withdraw invoice is invalid.", current_plan=plan)
            if context.cooldown_satisfied is False:
                return self._deny(POLICY_DECISION_RATE_LIMITED, reasons.COOLDOWN_REQUIRED, "Cooldown is required.", current_plan=plan)
            if context.quorum_satisfied is False:
                return self._deny(POLICY_DECISION_QUORUM_REQUIRED, reasons.QUORUM_REQUIRED, "Quorum is required.", current_plan=plan, metadata={"required_quorum": context.required_quorum or "policy_profile"})
        if context.payer_data_present and context.requested_action == "lnurl_payerdata_bind_auth" and not context.payer_data_auth_verified:
            return self._deny(POLICY_DECISION_DENY, reasons.PAYER_DATA_AUTH_INVALID, "payerData auth is invalid.", current_plan=plan)
        if context.comment_present and context.requested_action not in {"lnurl_comment_store", "payregister_lnurl_create_payment", "lnurl_pay_issue_invoice"}:
            return self._deny(POLICY_DECISION_DENY, reasons.PAYER_DATA_NOT_AUTHORIZATION, "LNURL comments cannot authorize access.", current_plan=plan)
        if context.success_action_type and context.requested_action in {"lnurl_pay_issue_entitlement", "complete_recovery", "lnurl_auth_login"}:
            return self._deny(POLICY_DECISION_DENY, reasons.SUCCESS_ACTION_TYPE_NOT_ALLOWED, "successAction is UX only.", current_plan=plan)
        return None

    def _actor(self, context: AccessPolicyContext) -> PolicyActorType | None:
        try:
            return PolicyActorType(context.actor_type) if context.actor_type is not None else None
        except ValueError:
            return None

    def _methods(self, context: AccessPolicyContext) -> set[str]:
        return {str(m.value if hasattr(m, "value") else m) for m in context.auth_methods}

    def _assurance_rank(self, context: AccessPolicyContext) -> int:
        order = {"compatibility": 0, "standard": 1, "high_assurance": 2, "sovereign": 3}
        val = context.authentication_assurance.value if hasattr(context.authentication_assurance, "value") else str(context.authentication_assurance)
        return order.get(val, -1)

    def _category(self, context: AccessPolicyContext) -> str:
        action = str(context.requested_action or context.metadata.get("action", ""))
        if action in {"complete_recovery", "change_recovery_policy", "release_lockdown", "treasury_policy_change", "enterprise_policy_change", "business_owner_assignment", "payregister_owner_transfer", "high_value_refund", "high_value_payout", "sovereign_policy_change"}:
            return "sovereign" if action == "sovereign_policy_change" else "critical"
        if action in HIGH_RISK_ACTIONS:
            return "high"
        return context.request_risk_level.strip().lower()

    def _is_treasury_action(self, context: AccessPolicyContext) -> bool:
        action = str(context.requested_action or context.metadata.get("action", ""))
        return action.startswith("treasury_") or (context.requested_scope or "").startswith("treasury:")

    def _is_recovery_action(self, context: AccessPolicyContext) -> bool:
        action = str(context.requested_action or context.metadata.get("action", ""))
        return action.startswith("recovery") or action in {"complete_recovery", "start_recovery"}

    def _check_statuses(self, context: AccessPolicyContext, plan: PlanCode) -> AccessPolicyDecision | None:
        now = datetime.now(UTC)
        action = str(context.requested_action or context.metadata.get("action", ""))
        session_optional = action in {"lnurl_auth_register", "lnurl_auth_login", "lnurl_pay_create_request", "lightning_address_resolve"}
        legacy_access_certificate_context = self._actor(context) is None and context.certificate_fingerprint and context.pass_lookup_hash
        if context.session_id_hash is None and self._actor(context) is not PolicyActorType.SERVICE_ACCOUNT and not session_optional and not legacy_access_certificate_context:
            return self._deny(POLICY_DECISION_DENY, reasons.SESSION_MISSING, "Session context is missing.", current_plan=plan)
        if self._actor(context) is None and (context.certificate_fingerprint is None or context.pass_lookup_hash is None):
            return self._deny(POLICY_DECISION_DENY, reasons.MISSING_ACCESS_CONTEXT, "Certificate context is missing.", current_plan=plan)
        if self._actor(context) not in {None, PolicyActorType.SERVICE_ACCOUNT} and context.device_status in {"missing", "required"}:
            return self._deny(POLICY_DECISION_DEVICE_BINDING_REQUIRED, reasons.DEVICE_MISSING, "Device binding is required.", current_plan=plan)
        if context.session_status == "expired" or (context.session_expires_at and _is_expired(context.session_expires_at, now)):
            return self._deny(POLICY_DECISION_EXPIRED, reasons.SESSION_EXPIRED, "Session is expired.", current_plan=plan)
        if context.session_status in {"revoked", "frozen"}:
            return self._deny(POLICY_DECISION_REVOKED, reasons.SESSION_REVOKED, "Session is revoked.", current_plan=plan)
        if context.device_status in {"revoked", "frozen"}:
            return self._deny(POLICY_DECISION_REVOKED, reasons.DEVICE_REVOKED, "Device is revoked.", current_plan=plan)
        if context.entitlement_status == "expired" or (context.entitlement_valid_until and _is_expired(context.entitlement_valid_until, now)):
            return self._deny(POLICY_DECISION_EXPIRED, reasons.ENTITLEMENT_EXPIRED, "Entitlement is expired.", current_plan=plan)
        if context.entitlement_status not in {"active", "grace"}:
            return self._deny(POLICY_DECISION_DENY, reasons.ENTITLEMENT_INACTIVE, "Entitlement is inactive.", current_plan=plan)
        return None

    def _check_revocation(self, context: AccessPolicyContext, plan: PlanCode) -> AccessPolicyDecision | None:
        resolution = context.revocation_resolution
        if resolution.get("revoked"):
            return self._deny(POLICY_DECISION_REVOKED, reasons.PRINCIPAL_REVOKED,
                "Access has been revoked.", current_plan=plan,
                metadata={"inherited_revocation": bool(resolution.get("inherited_from_parent")),
                          "propagation_status": resolution.get("propagation_status"),
                          "target_scope": resolution.get("scope")})
        if context.propagation_status in {"pending_propagation", "partially_propagated"} and context.is_critical_action:
            return self._deny(POLICY_DECISION_REVOKED, reasons.PRINCIPAL_REVOKED,
                "Revocation state is still propagating.", current_plan=plan)
        if context.offline_epoch_status == "stale":
            return self._deny(POLICY_DECISION_ONLINE_CHECK_REQUIRED, reasons.ONLINE_CHECK_REQUIRED,
                "Online revocation check is required.", current_plan=plan)
        if context.withdraw_revocation_status == "revoked":
            return self._deny(POLICY_DECISION_REVOKED, reasons.WITHDRAW_REQUEST_REVOKED,
                "Withdraw request is unavailable.", current_plan=plan)
        if context.payment_proof_status in {"revoked", "invalidated", "dispute_review"}:
            return self._deny(POLICY_DECISION_REVOKED, reasons.PAYMENT_VERIFICATION_FAILED,
                "Payment proof is unavailable.", current_plan=plan)
        revoked_targets = context.revocation_state.get("revoked_targets") if isinstance(context.revocation_state, dict) else None
        if revoked_targets:
            raw_target_type = revoked_targets[0].get("target_type") if isinstance(revoked_targets[0], dict) else None
            target_type = raw_target_type if isinstance(raw_target_type, str) else ""
            reason_code = {
                "certificate": reasons.CERTIFICATE_REVOKED,
                "session": reasons.SESSION_REVOKED,
                "device": reasons.DEVICE_REVOKED,
            }.get(target_type, reasons.SESSION_REVOKED)
            return self._deny(POLICY_DECISION_REVOKED, reason_code, "Access material is revoked.", current_plan=plan, metadata={"revoked_targets": revoked_targets})
        if context.revocation_state.get("allowed") is False:
            return self._deny(POLICY_DECISION_REVOKED, reasons.SESSION_REVOKED, "Access material is revoked.", current_plan=plan)
        return None

    def _check_access_integrity(self, context: AccessPolicyContext, plan: PlanCode) -> AccessPolicyDecision | None:
        """Consume server-calculated posture only as a restrictive risk signal."""
        if context.integrity_score_version is None:
            return None
        if context.integrity_score_version != "2.0" or context.access_integrity_score is None:
            return self._deny(POLICY_DECISION_DENY, reasons.VERIFICATION_TOO_WEAK,
                "Access posture evidence is unavailable.", current_plan=plan)
        if context.access_integrity_band == "critical" or context.access_integrity_score < 30:
            return self._deny(POLICY_DECISION_LOCKDOWN_ACTIVE, reasons.LOCKDOWN_ACTIVE,
                "Access posture requires recovery review.", current_plan=plan)
        if context.access_integrity_band == "restricted" or context.access_integrity_score < 55:
            return self._deny(POLICY_DECISION_DENY, reasons.VERIFICATION_TOO_WEAK,
                "Access posture permits only restricted access.", current_plan=plan)
        if context.access_integrity_band == "guarded" and (context.is_critical_action or context.request_risk_level in {"high", "critical"}):
            return self._deny(POLICY_DECISION_STEP_UP_REQUIRED, reasons.STEP_UP_REQUIRED,
                "Additional verification is required.", current_plan=plan, step_up_required=True)
        return None

    def _check_offline(self, context: AccessPolicyContext, plan: PlanCode) -> AccessPolicyDecision | None:
        if not context.offline_mode:
            return None
        if plan in {PlanCode.LITE, PlanCode.BASIC}:
            return self._deny(POLICY_DECISION_ONLINE_CHECK_REQUIRED, reasons.OFFLINE_ACCESS_NOT_ALLOWED, "Offline access is not allowed.", current_plan=plan)
        if context.is_critical_action or (context.requested_scope or "").startswith(("treasury:", "payregister:admin")):
            return self._deny(POLICY_DECISION_ONLINE_CHECK_REQUIRED, reasons.ONLINE_CHECK_REQUIRED, "Online check is required.", current_plan=plan)
        return None

    def _check_scope(self, context: AccessPolicyContext, plan: PlanCode) -> AccessPolicyDecision | None:
        scope = context.requested_scope
        if scope is None:
            return None
        if scope in FORBIDDEN_SCOPES or scope not in ACCESS_SCOPES or scope not in context.effective_scopes:
            return self._deny(POLICY_DECISION_DENY, reasons.SCOPE_NOT_ALLOWED, "Requested scope is not allowed.", current_plan=plan, requested_scope=scope)
        return None

    def _check_object_access(self, context: AccessPolicyContext, plan: PlanCode) -> AccessPolicyDecision | None:
        if context.requested_object_type is None:
            return None
        if context.requested_object_type not in SUPPORTED_OBJECT_TYPES or context.requested_object_id_hash is None:
            return self._deny(POLICY_DECISION_DENY, reasons.OBJECT_ACCESS_DENIED, "Object access cannot be determined.", current_plan=plan)
        return None

    def _check_risk_and_step_up(self, context: AccessPolicyContext, plan: PlanCode) -> AccessPolicyDecision | None:
        step_policy_decision = None if self._actor(context) is None else self.evaluate_step_up_requirement(context)
        if step_policy_decision is None:
            risk = self._category(context)
            action = str(context.requested_action or context.metadata.get("action", ""))
            critical = context.is_critical_action or action in CRITICAL_ACTIONS or risk in {"critical", "sovereign"}
        else:
            if step_policy_decision.decision in {"deny", "quorum_required"}:
                return self._deny(POLICY_DECISION_QUORUM_REQUIRED if step_policy_decision.decision == "quorum_required" else POLICY_DECISION_DENY, step_policy_decision.reason_code, step_policy_decision.safe_user_message, current_plan=plan, step_up_required=step_policy_decision.decision == "step_up_required", metadata={"step_up_requirement": step_policy_decision.requirement, "required_quorum": step_policy_decision.required_quorum})
            if step_policy_decision.decision == "step_up_required":
                return self._deny(POLICY_DECISION_STEP_UP_REQUIRED, step_policy_decision.reason_code, step_policy_decision.safe_user_message, current_plan=plan, step_up_required=True, metadata={"step_up_requirement": step_policy_decision.requirement, "required_auth_methods": step_policy_decision.required_auth_methods})
            risk = self._category(context)
            action = str(context.requested_action or context.metadata.get("action", ""))
            critical = context.is_critical_action or action in CRITICAL_ACTIONS or risk in {"critical", "sovereign"}
        if risk in {"high", "critical", "sovereign"} and self._assurance_rank(context) <= 0:
            return self._deny(POLICY_DECISION_PROOF_TOO_WEAK, reasons.WALLET_PROOF_TOO_WEAK, "Authentication assurance is too weak.", current_plan=plan)
        if risk == "sovereign" and not context.quorum_evidence:
            return self._deny(POLICY_DECISION_QUORUM_REQUIRED, reasons.QUORUM_REQUIRED, "Quorum is required.", current_plan=plan, metadata={"required_quorum": context.required_quorum or "policy_profile"})
        if risk == "critical" and not context.human_intent_verified:
            return self._deny(POLICY_DECISION_LOCKDOWN_REQUIRED, reasons.LOCKDOWN_REQUIRED, "Critical risk requires lockdown or human intent.", current_plan=plan, lockdown_recommended=True)
        if risk == "high" and not context.step_up_present:
            return self._deny(POLICY_DECISION_STEP_UP_REQUIRED, reasons.CRITICAL_ACTION_REQUIRES_STEP_UP, "High-risk request requires step-up.", current_plan=plan, step_up_required=True)
        if risk == "medium" and critical and not context.step_up_present:
            return self._deny(POLICY_DECISION_STEP_UP_REQUIRED, reasons.CRITICAL_ACTION_REQUIRES_STEP_UP, "Critical request requires step-up.", current_plan=plan, step_up_required=True)
        if critical and not context.human_intent_verified:
            return self._deny(POLICY_DECISION_STEP_UP_REQUIRED, reasons.CRITICAL_ACTION_REQUIRES_HUMAN_INTENT, "Critical request requires Human Intent Signature.", current_plan=plan, step_up_required=True)
        if context.device_risk_score is not None and context.device_risk_score >= 90 and not context.step_up_present:
            return self._deny(POLICY_DECISION_STEP_UP_REQUIRED, reasons.DEVICE_RISK_TOO_HIGH, "Device risk is too high.", current_plan=plan, step_up_required=True)
        return None

    def _normalize_plan(self, context: AccessPolicyContext) -> PlanCode | None:
        try:
            return normalize_plan_code(context.plan_code) if context.plan_code is not None else None
        except ValueError:
            return None

    def _quota_remaining(self, context: AccessPolicyContext) -> int | None:
        remaining = context.quota_state.get("remaining")
        return remaining if isinstance(remaining, int) else None

    def _quota_decision(self, context: AccessPolicyContext, plan: PlanCode | None) -> AccessPolicyDecision:
        retry = context.quota_state.get("retry_after_seconds")
        return self._deny(
            POLICY_DECISION_QUOTA_EXCEEDED,
            reasons.QUOTA_EXCEEDED,
            "Quota is exhausted.",
            current_plan=plan,
            quota_remaining=self._quota_remaining(context),
            retry_after_seconds=retry if isinstance(retry, int) else None,
        )

    def _deny(
        self,
        decision: str,
        reason_code: str,
        human_reason: str,
        *,
        current_plan: PlanCode | None = None,
        required_plan: PlanCode | None = None,
        requested_scope: str | None = None,
        requested_metric_group: str | None = None,
        upgrade_available: bool = False,
        step_up_required: bool = False,
        quota_remaining: int | None = None,
        retry_after_seconds: int | None = None,
        lockdown_recommended: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> AccessPolicyDecision:
        meta = metadata or {}
        context = getattr(self, "_current_context", None)
        return AccessPolicyDecision(
            decision=decision,
            allowed=False,
            reason_code=reason_code,
            human_reason=human_reason,
            current_plan=current_plan,
            required_plan=required_plan,
            requested_scope=requested_scope,
            requested_metric_group=requested_metric_group,
            upgrade_available=upgrade_available,
            step_up_required=step_up_required,
            quota_remaining=quota_remaining,
            retry_after_seconds=retry_after_seconds,
            audit_required=True,
            lockdown_recommended=lockdown_recommended,
            metadata=meta,
            actor_type=getattr(context, "actor_type", None),
            actor_hash=getattr(context, "actor_hash", None),
            auth_methods_used=tuple(str(m.value if hasattr(m, "value") else m) for m in getattr(context, "auth_methods", ())),
            authentication_assurance=getattr(context, "authentication_assurance", None),
            requested_action=getattr(context, "requested_action", None) or (getattr(context, "metadata", {}) or {}).get("action") if context is not None else None,
            resource_type=getattr(context, "resource_type", None) or getattr(context, "requested_object_type", None),
            resource_hash=getattr(context, "resource_hash", None) or getattr(context, "requested_object_id_hash", None),
            policy_epoch=getattr(context, "policy_epoch", None),
            policy_hash=getattr(context, "policy_hash", None),
            requires_quorum=decision == POLICY_DECISION_QUORUM_REQUIRED,
            required_quorum=meta.get("required_quorum") if isinstance(meta.get("required_quorum"), str) else None,
            requires_access_certificate=reason_code == reasons.ACCESS_CERTIFICATE_REQUIRED,
            safe_user_message=human_reason,
            evaluated_at=datetime.now(UTC),
        )


def _int_or_none(value: Any) -> int | None:
    return value if isinstance(value, int) else None


def _is_expired(value: datetime, now: datetime) -> bool:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC) <= now
