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
from app.services.access.policy_context import AccessPolicyContext, AccessPolicyDecision
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
    "admin": {"payregister:devices:read", "payregister:operator:read", "payregister:shifts:read", "payregister:invoices:read"},
    "operator": {"payregister:operator:read", "payregister:shifts:read"},
    "cashier": {"payregister:invoices:read", "payregister:shifts:read"},
    "analyst": {"payregister:metrics:read", "business:audit:read"},
    "viewer": {"payregister:metrics:read"},
    "device": {"payregister:devices:read"},
    "bot": {"payregister:metrics:read"},
}


class AccessPolicyEngine:
    def evaluate(self, context: AccessPolicyContext | None) -> AccessPolicyDecision:
        if context is None or not isinstance(context, AccessPolicyContext):
            return self._deny(POLICY_DECISION_DENY, reasons.MISSING_ACCESS_CONTEXT, "Access context is missing.")
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
            audit_required=context.is_critical_action,
        )

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

    def _check_statuses(self, context: AccessPolicyContext, plan: PlanCode) -> AccessPolicyDecision | None:
        now = datetime.now(UTC)
        if context.certificate_fingerprint is None or context.pass_lookup_hash is None:
            return self._deny(POLICY_DECISION_DENY, reasons.MISSING_ACCESS_CONTEXT, "Certificate context is missing.", current_plan=plan)
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
        risk = context.request_risk_level.strip().lower()
        action = str(context.metadata.get("action", ""))
        critical = context.is_critical_action or action in CRITICAL_ACTIONS
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
            metadata=metadata or {},
        )


def _is_expired(value: datetime, now: datetime) -> bool:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC) <= now
