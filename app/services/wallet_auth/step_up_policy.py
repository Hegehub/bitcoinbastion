"""Central Wallet + LNURL step-up policy rules.

This module is a focused rules provider for the existing AccessPolicyEngine. It
classifies actions, validates proof freshness and intent binding, and returns a
structured decision. It does not replace subscription/scope/metric/object checks
and does not perform cryptographic verification.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from app.domain.access.plans import PlanCode
from app.services.access.policy_context import AuthenticationAssuranceLevel, PolicyActorType, PolicyAuthMethod
import app.services.access.policy_reasons as reasons


class StepUpRequirement(StrEnum):
    NONE = "none"
    DEVICE_CONFIRMATION = "device_confirmation"
    FRESH_POP_CONFIRMATION = "fresh_pop_confirmation"
    FRESH_LNURL_AUTH = "fresh_lnurl_auth"
    FRESH_BIP322 = "fresh_bip322"
    HARDWARE_WALLET_PROOF = "hardware_wallet_proof"
    DUAL_METHOD = "dual_method"
    MULTI_WALLET_QUORUM = "multi_wallet_quorum"
    RECOVERY_QUORUM = "recovery_quorum"
    SOVEREIGN_CEREMONY = "sovereign_ceremony"
    DENIED = "denied"


class StepUpDecision(StrEnum):
    ALLOW = "allow"
    STEP_UP_REQUIRED = "step_up_required"
    QUORUM_REQUIRED = "quorum_required"
    DENY = "deny"


class StepUpActionClass(StrEnum):
    ROUTINE = "routine"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    SOVEREIGN = "sovereign"


ROUTINE_ACTIONS = frozenset({
    "read_public_status", "read_basic_metrics", "read_current_entitlements", "list_own_devices",
    "read_non_sensitive_dashboard", "read_allowed_trace_lite", "read_wallet_health_watch_only", "read_metric",
})
MEDIUM_RISK_ACTIONS = frozenset({
    "renew_subscription", "update_non_sensitive_preferences", "create_short_lived_read_only_child_key",
    "export_small_non_sensitive_report", "link_optional_contact_channel", "request_limited_offline_pack",
})
HIGH_RISK_ACTIONS = frozenset({
    "create_api_key", "increase_scope", "create_delegated_pass", "add_device", "device_add", "revoke_device",
    "export_sensitive_data", "create_long_lived_automation_key", "enable_advanced_trace_access",
    "change_subscription_to_plan_with_new_permissions", "create_payregister_cashier_pass", "create_business_role_binding",
})
CRITICAL_ACTIONS = frozenset({
    "treasury_policy_change", "recovery_change", "recovery_complete", "complete_recovery", "lockdown_release",
    "business_owner_change", "business_admin_assignment", "enterprise_policy_change", "payregister_admin_enable",
    "payregister_owner_change", "high-value_refund", "high-value_lnurl_withdraw", "issuer_policy_change",
    "access_certificate_root_rotation", "offline_validity_pack_admin_issue", "transparency_checkpoint_override",
})
SOVEREIGN_ACTIONS = frozenset({
    "sovereign_recovery_complete", "root_policy_rotation", "issuer_key_rotation", "enterprise_owner_quorum_change",
    "revocation_epoch_override", "emergency_transparency_override", "high-value_business_payout", "offline_root_certificate_issue",
})
TREASURY_ACTIONS = frozenset({"treasury_policy_change", "transparency_checkpoint_override"})


@dataclass(frozen=True, slots=True)
class StepUpPolicyConfig:
    intent_ttl_seconds: int = int(os.getenv("WALLET_STEP_UP_INTENT_TTL_SECONDS", "300"))
    lnurl_ttl_seconds: int = int(os.getenv("WALLET_STEP_UP_LNURL_TTL_SECONDS", "300"))
    bip322_ttl_seconds: int = int(os.getenv("WALLET_STEP_UP_BIP322_TTL_SECONDS", "300"))
    quorum_ttl_seconds: int = int(os.getenv("WALLET_STEP_UP_QUORUM_TTL_SECONDS", "300"))
    sovereign_mode_enabled: bool = os.getenv("WALLET_STEP_UP_SOVEREIGN_MODE_ENABLED", "false").lower() in {"1", "true", "yes"}
    policy_epoch: int = 1
    policy_hash: str = "sha256:wallet-step-up-policy-v1"


@dataclass(frozen=True, slots=True)
class StepUpProofState:
    method: PolicyAuthMethod | str
    freshness_seconds: int | None = None
    intent_hash: str | None = None
    action: str | None = None
    policy_hash: str | None = None
    verified: bool = False
    hardware_evidence_verified: bool = False
    k1_status: str | None = None
    challenge_status: str | None = None
    principal_hash: str | None = None
    proof_class: str | None = None


@dataclass(frozen=True, slots=True)
class QuorumState:
    threshold: int
    participants: int
    signer_principal_hashes: tuple[str, ...] = ()
    intent_hash: str | None = None
    freshness_seconds: int | None = None
    distinct_roles: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class StepUpPolicyContext:
    action: str
    actor_type: PolicyActorType | str
    principal_hash: str | None = None
    device_key_fingerprint: str | None = None
    session_hash: str | None = None
    auth_method: PolicyAuthMethod | str | None = None
    current_verification_strength: AuthenticationAssuranceLevel | str = AuthenticationAssuranceLevel.STANDARD
    wallet_proof_freshness_seconds: int | None = None
    lnurl_proof_freshness_seconds: int | None = None
    session_age_seconds: int | None = None
    device_trust_level: str = "standard"
    device_risk_score: int | None = None
    subscription_plan: PlanCode | str | None = None
    requested_scopes: frozenset[str] = field(default_factory=frozenset)
    effective_scopes: frozenset[str] = field(default_factory=frozenset)
    requested_object: str | None = None
    requested_expiry: str | None = None
    requested_amount_msat: int | None = None
    business_role: str | None = None
    payregister_role: str | None = None
    recovery_state: str | None = None
    lockdown_state: str | None = None
    sovereign_mode: bool = False
    existing_quorum_state: QuorumState | None = None
    revocation_state: dict[str, Any] = field(default_factory=dict)
    policy_epoch: int = 1
    policy_hash: str = "sha256:wallet-step-up-policy-v1"
    intent_hash: str | None = None
    provided_proofs: tuple[StepUpProofState, ...] = ()
    human_intent_verified: bool = False
    access_certificate_present: bool = False
    quota_state: dict[str, Any] = field(default_factory=dict)
    metric_group: str | None = None


@dataclass(frozen=True, slots=True)
class StepUpPolicyDecision:
    decision: str
    requirement: StepUpRequirement | str
    reason_code: str
    action: str
    risk_level: str
    required_auth_methods: tuple[str, ...] = ()
    accepted_auth_methods: tuple[str, ...] = ()
    required_verification_strength: str | None = None
    required_quorum: dict[str, Any] | None = None
    intent_required: bool = False
    cooldown_seconds: int | None = None
    proof_freshness_seconds: int | None = None
    audit_required: bool = True
    transparency_checkpoint_required: bool = False
    access_certificate_required: bool = False
    policy_hash: str = "sha256:wallet-step-up-policy-v1"
    policy_epoch: int = 1
    safe_user_message: str = "Step-up policy evaluated."

    @property
    def allowed(self) -> bool:
        return self.decision == StepUpDecision.ALLOW.value


class WalletLNURLStepUpPolicy:
    def __init__(self, config: StepUpPolicyConfig | None = None) -> None:
        self.config = config or StepUpPolicyConfig()

    def evaluate_step_up_requirement(self, context: StepUpPolicyContext) -> StepUpPolicyDecision:
        action_class = classify_step_up_action(context.action)
        revoked = self._revoked(context)
        if revoked:
            return self._decision(context, StepUpDecision.DENY, StepUpRequirement.DENIED, revoked, action_class)
        if not context.policy_hash.startswith("sha256:"):
            return self._decision(context, StepUpDecision.DENY, StepUpRequirement.DENIED, reasons.POLICY_HASH_MISMATCH, action_class)
        if context.recovery_state == "recovery_locked" and context.action not in {"recovery_complete", "sovereign_recovery_complete", "lockdown_release"}:
            return self._decision(context, StepUpDecision.DENY, StepUpRequirement.DENIED, reasons.RECOVERY_LOCKED, action_class)
        if context.lockdown_state == "active" and context.action != "lockdown_release":
            return self._decision(context, StepUpDecision.DENY, StepUpRequirement.DENIED, reasons.LOCKDOWN_ACTIVE, action_class)
        if not context.requested_scopes <= context.effective_scopes:
            return self._decision(context, StepUpDecision.DENY, StepUpRequirement.DENIED, reasons.SCOPE_NOT_ALLOWED, action_class)
        if context.quota_state.get("exhausted") is True:
            return self._decision(context, StepUpDecision.DENY, StepUpRequirement.DENIED, reasons.QUOTA_EXCEEDED, action_class)
        if action_class is StepUpActionClass.ROUTINE:
            return self._decision(context, StepUpDecision.ALLOW, StepUpRequirement.NONE, reasons.STEP_UP_NOT_REQUIRED, action_class)
        if self._legacy_forbidden(context, action_class):
            return self._decision(context, StepUpDecision.STEP_UP_REQUIRED, StepUpRequirement.FRESH_BIP322, reasons.STRONGER_WALLET_PROOF_REQUIRED, action_class, required=("pop_session", "bip322", "human_intent"))
        strength = str(context.current_verification_strength.value if hasattr(context.current_verification_strength, "value") else context.current_verification_strength)
        if action_class in {StepUpActionClass.HIGH, StepUpActionClass.CRITICAL, StepUpActionClass.SOVEREIGN} and strength == AuthenticationAssuranceLevel.COMPATIBILITY.value:
            return self._decision(context, StepUpDecision.STEP_UP_REQUIRED, StepUpRequirement.FRESH_BIP322, reasons.WALLET_PROOF_TOO_WEAK, action_class, required=("pop_session", "bip322_or_lnurl_auth", "human_intent"), strength="standard")
        if context.action in TREASURY_ACTIONS or context.requested_object == "treasury":
            if str(context.actor_type) == PolicyActorType.LIGHTNING_WALLET_PRINCIPAL.value:
                return self._decision(context, StepUpDecision.STEP_UP_REQUIRED, StepUpRequirement.FRESH_BIP322, reasons.FRESH_BIP322_REQUIRED, action_class, required=("pop_session", "bip322", "human_intent"), strength="high_assurance")
            if self._proof_ok(context, PolicyAuthMethod.BIP322, self.config.bip322_ttl_seconds):
                return self._decision(context, StepUpDecision.ALLOW, StepUpRequirement.FRESH_BIP322, reasons.FRESH_BIP322_STEP_UP_SATISFIED, action_class, accepted=("bip322",))
            return self._decision(context, StepUpDecision.STEP_UP_REQUIRED, StepUpRequirement.FRESH_BIP322, reasons.FRESH_BIP322_REQUIRED, action_class, required=("pop_session", "bip322", "human_intent"), strength="high_assurance")
        if action_class is StepUpActionClass.SOVEREIGN:
            if self._quorum_ok(context, require_hardware=True):
                return self._decision(context, StepUpDecision.ALLOW, StepUpRequirement.SOVEREIGN_CEREMONY, reasons.SOVEREIGN_CEREMONY_SATISFIED, action_class, accepted=("multi_wallet_quorum",))
            return self._decision(context, StepUpDecision.QUORUM_REQUIRED, StepUpRequirement.SOVEREIGN_CEREMONY, reasons.SOVEREIGN_CEREMONY_REQUIRED, action_class, required=("pop_session", "human_intent", "multi_wallet_quorum", "hardware_wallet"), quorum={"threshold": 2, "participants": 3}, strength="sovereign", transparency=True)
        if context.action in {"business_owner_change", "enterprise_owner_quorum_change"}:
            if self._quorum_ok(context):
                return self._decision(context, StepUpDecision.ALLOW, StepUpRequirement.MULTI_WALLET_QUORUM, reasons.MULTI_WALLET_QUORUM_SATISFIED, action_class, accepted=("multi_wallet_quorum",))
            return self._decision(context, StepUpDecision.QUORUM_REQUIRED, StepUpRequirement.MULTI_WALLET_QUORUM, reasons.MULTI_WALLET_QUORUM_REQUIRED, action_class, required=("pop_session", "human_intent", "multi_wallet_quorum"), quorum={"threshold": 2, "participants": 3, "distinct_roles": ["owner", "admin"]})
        if context.action in {"high-value_lnurl_withdraw", "high-value_business_payout"} or (context.requested_amount_msat or 0) >= 10_000_000:
            if self._dual_method_ok(context):
                return self._decision(context, StepUpDecision.ALLOW, StepUpRequirement.DUAL_METHOD, reasons.DUAL_METHOD_STEP_UP_SATISFIED, action_class, accepted=("lnurl_auth", "bip322"))
            return self._decision(context, StepUpDecision.STEP_UP_REQUIRED, StepUpRequirement.DUAL_METHOD, reasons.DUAL_METHOD_REQUIRED, action_class, required=("pop_session", "human_intent", "lnurl_auth_or_bip322", "second_distinct_method"), strength="high_assurance")
        if action_class is StepUpActionClass.CRITICAL:
            if self._proof_ok(context, PolicyAuthMethod.BIP322, self.config.bip322_ttl_seconds) or self._hardware_ok(context):
                return self._decision(context, StepUpDecision.ALLOW, StepUpRequirement.FRESH_BIP322, reasons.FRESH_BIP322_STEP_UP_SATISFIED, action_class, accepted=("bip322",))
            return self._decision(context, StepUpDecision.STEP_UP_REQUIRED, StepUpRequirement.FRESH_BIP322, reasons.FRESH_BIP322_REQUIRED, action_class, required=("pop_session", "bip322", "human_intent"), strength="high_assurance")
        if action_class is StepUpActionClass.HIGH:
            strength = str(context.current_verification_strength.value if hasattr(context.current_verification_strength, "value") else context.current_verification_strength)
            if context.human_intent_verified and strength in {"high_assurance", "sovereign"} and not context.provided_proofs:
                return self._decision(context, StepUpDecision.ALLOW, StepUpRequirement.FRESH_POP_CONFIRMATION, reasons.FRESH_POP_CONFIRMATION_SATISFIED, action_class, accepted=("human_intent",))
            if self._proof_ok(context, PolicyAuthMethod.LNURL_AUTH, self.config.lnurl_ttl_seconds) or self._proof_ok(context, PolicyAuthMethod.BIP322, self.config.bip322_ttl_seconds):
                accepted = tuple(sorted({str(p.method.value if hasattr(p.method, "value") else p.method) for p in context.provided_proofs if p.verified}))
                return self._decision(context, StepUpDecision.ALLOW, StepUpRequirement.FRESH_LNURL_AUTH, reasons.FRESH_LNURL_STEP_UP_SATISFIED, action_class, accepted=accepted)
            return self._decision(context, StepUpDecision.STEP_UP_REQUIRED, StepUpRequirement.FRESH_LNURL_AUTH, reasons.FRESH_LNURL_AUTH_REQUIRED, action_class, required=("pop_session", "human_intent", "lnurl_auth_or_bip322"), strength="standard")
        if self._proof_ok(context, PolicyAuthMethod.DEVICE_POP, self.config.intent_ttl_seconds):
            return self._decision(context, StepUpDecision.ALLOW, StepUpRequirement.FRESH_POP_CONFIRMATION, reasons.FRESH_POP_CONFIRMATION_SATISFIED, action_class, accepted=("device_pop",))
        return self._decision(context, StepUpDecision.STEP_UP_REQUIRED, StepUpRequirement.FRESH_POP_CONFIRMATION, reasons.FRESH_POP_CONFIRMATION_REQUIRED, action_class, required=("pop_session", "human_intent"))

    def _proof_ok(self, context: StepUpPolicyContext, method: PolicyAuthMethod, ttl: int) -> bool:
        for proof in context.provided_proofs:
            if str(proof.method.value if hasattr(proof.method, "value") else proof.method) != method.value:
                continue
            if not proof.verified:
                continue
            if proof.freshness_seconds is None or proof.freshness_seconds > ttl:
                continue
            if proof.intent_hash != context.intent_hash or proof.action != context.action or proof.policy_hash != context.policy_hash:
                continue
            if proof.principal_hash and context.principal_hash and proof.principal_hash != context.principal_hash:
                continue
            if method is PolicyAuthMethod.LNURL_AUTH and proof.k1_status not in {None, "used"}:
                continue
            if method is PolicyAuthMethod.BIP322 and proof.challenge_status not in {None, "used"}:
                continue
            return True
        return False

    def _hardware_ok(self, context: StepUpPolicyContext) -> bool:
        return any(proof.verified and proof.hardware_evidence_verified and proof.intent_hash == context.intent_hash and proof.policy_hash == context.policy_hash for proof in context.provided_proofs)

    def _dual_method_ok(self, context: StepUpPolicyContext) -> bool:
        classes = {proof.proof_class or str(proof.method.value if hasattr(proof.method, "value") else proof.method) for proof in context.provided_proofs if proof.verified and proof.intent_hash == context.intent_hash and proof.policy_hash == context.policy_hash and proof.freshness_seconds is not None and proof.freshness_seconds <= self.config.intent_ttl_seconds}
        return len(classes) >= 2

    def _quorum_ok(self, context: StepUpPolicyContext, *, require_hardware: bool = False) -> bool:
        quorum = context.existing_quorum_state
        if quorum is None or quorum.intent_hash != context.intent_hash:
            return False
        if quorum.freshness_seconds is None or quorum.freshness_seconds > self.config.quorum_ttl_seconds:
            return False
        if len(set(quorum.signer_principal_hashes)) < quorum.threshold:
            return False
        if require_hardware and not self._hardware_ok(context):
            return False
        return True

    def _legacy_forbidden(self, context: StepUpPolicyContext, action_class: StepUpActionClass) -> bool:
        method = context.auth_method.value if isinstance(context.auth_method, PolicyAuthMethod) else str(context.auth_method or "")
        return method in {PolicyAuthMethod.LEGACY_BITCOIN_MESSAGE.value, "legacy_message_signature"} and action_class in {StepUpActionClass.HIGH, StepUpActionClass.CRITICAL, StepUpActionClass.SOVEREIGN}

    def _revoked(self, context: StepUpPolicyContext) -> str | None:
        if context.revocation_state.get("principal_revoked") or context.revocation_state.get("allowed") is False:
            return reasons.PRINCIPAL_REVOKED
        if context.revocation_state.get("device_revoked"):
            return reasons.DEVICE_REVOKED
        if context.revocation_state.get("session_revoked"):
            return reasons.SESSION_REVOKED
        if context.revocation_state.get("entitlement_expired"):
            return reasons.ENTITLEMENT_EXPIRED
        return None

    def _decision(self, context: StepUpPolicyContext, decision: StepUpDecision, requirement: StepUpRequirement, reason_code: str, action_class: StepUpActionClass, *, required: tuple[str, ...] = (), accepted: tuple[str, ...] = (), strength: str | None = None, quorum: dict[str, Any] | None = None, transparency: bool = False) -> StepUpPolicyDecision:
        return StepUpPolicyDecision(
            decision=decision.value,
            requirement=requirement.value,
            reason_code=reason_code,
            action=context.action,
            risk_level=action_class.value,
            required_auth_methods=required,
            accepted_auth_methods=accepted,
            required_verification_strength=strength,
            required_quorum=quorum,
            intent_required=requirement is not StepUpRequirement.NONE,
            cooldown_seconds=self.config.quorum_ttl_seconds if decision is StepUpDecision.QUORUM_REQUIRED else None,
            proof_freshness_seconds=self.config.intent_ttl_seconds,
            audit_required=action_class is not StepUpActionClass.ROUTINE,
            transparency_checkpoint_required=transparency,
            access_certificate_required=requirement is StepUpRequirement.SOVEREIGN_CEREMONY,
            policy_hash=context.policy_hash,
            policy_epoch=context.policy_epoch,
            safe_user_message=_public_message(reason_code),
        )


def classify_step_up_action(action: str) -> StepUpActionClass:
    if action in SOVEREIGN_ACTIONS:
        return StepUpActionClass.SOVEREIGN
    if action in CRITICAL_ACTIONS:
        return StepUpActionClass.CRITICAL
    if action in HIGH_RISK_ACTIONS:
        return StepUpActionClass.HIGH
    if action in MEDIUM_RISK_ACTIONS:
        return StepUpActionClass.MEDIUM
    return StepUpActionClass.ROUTINE


def _public_message(reason_code: str) -> str:
    if reason_code.endswith("required"):
        return "Additional wallet approval is required."
    if "revoked" in reason_code or "locked" in reason_code:
        return "This action is not currently available."
    if "scope" in reason_code or "plan" in reason_code:
        return "Your current access does not permit this action."
    return "Step-up policy evaluated."


__all__ = [
    "StepUpActionClass",
    "StepUpDecision",
    "StepUpPolicyConfig",
    "StepUpPolicyContext",
    "StepUpPolicyDecision",
    "StepUpProofState",
    "StepUpRequirement",
    "QuorumState",
    "WalletLNURLStepUpPolicy",
    "classify_step_up_action",
]
