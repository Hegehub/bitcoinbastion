"""Wallet-bound Subscription Entitlement service.

The service treats payment proof as commercial evidence and wallet/LNURL-auth
proofs as principal evidence. An entitlement is not a bearer credential and is
only one input to PoP-session and Policy Engine authorization.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from threading import RLock
from typing import Any

from app.domain.access.decisions import AccessDecision, PolicyDecision
from app.domain.access.entitlements import get_plan_limits, get_plan_metric_groups, get_plan_scopes
from app.domain.access.plans import PlanCode, normalize_plan_code, plan_rank
from app.domain.access.wallet_entitlements import (
    EffectiveEntitlement,
    EntitlementAssurance,
    EntitlementLimits,
    EntitlementPaymentMethod,
    EntitlementRestriction,
    EntitlementSubjectType,
    IssuerSignatureMetadata,
    WalletEntitlementStatus,
    WalletSubscriptionEntitlement,
)
from app.services.access.crypto.hashing import hash_canonical_json_prefixed, reject_forbidden_secret_keys, sha256_prefixed
from app.services.access.crypto.signatures import sign_subscription_entitlement, verify_subscription_entitlement_signature

ENTITLEMENT_TYPE = "bastion_wallet_subscription_entitlement"
ENTITLEMENT_VERSION = 2
CANONICAL_PLAN_CODES = {plan.value for plan in PlanCode}
ACTIVE_ENTITLEMENT_STATUSES = {WalletEntitlementStatus.ACTIVE, WalletEntitlementStatus.GRACE_PERIOD}
DENY_ENTITLEMENT_STATUSES = {
    WalletEntitlementStatus.PENDING_PAYMENT,
    WalletEntitlementStatus.PENDING_VERIFICATION,
    WalletEntitlementStatus.SUSPENDED,
    WalletEntitlementStatus.EXPIRED,
    WalletEntitlementStatus.REVOKED,
    WalletEntitlementStatus.RECOVERY_LOCKED,
    WalletEntitlementStatus.PAYMENT_DISPUTED,
}
SECRET_MARKERS = ("raw_bitcoin_address", "raw_lnurl", "lnurl_k1", "wallet_signature", "raw_access_pass", "session_token", "wallet_seed", "private_key", "mnemonic", "xprv", "email")
AuditEmitter = Callable[[str, dict[str, Any]], None]


class WalletEntitlementError(ValueError):
    """Base safe exception for wallet-bound entitlement failures."""


class EntitlementPolicyError(WalletEntitlementError):
    pass


class EntitlementSignatureVerificationError(WalletEntitlementError):
    pass


@dataclass(frozen=True, slots=True)
class PrincipalState:
    principal_hash: str
    subject_type: EntitlementSubjectType
    status: str = "active"
    revoked: bool = False
    workspace_id_hash: str | None = None


@dataclass(frozen=True, slots=True)
class VerifiedPaymentProofRef:
    payment_proof_hash: str
    plan_code: str
    amount_msat: int
    network: str
    settled: bool
    verified: bool
    expires_at: datetime | None = None
    principal_hash: str | None = None
    product_code: str | None = None
    payerdata_auth_hash: str | None = None


@dataclass(frozen=True, slots=True)
class IssuerContext:
    issuer_private_key: str
    issuer_key_id: str
    issuer_public_key: str | None = None
    schema_epoch: int = 2
    policy_epoch: int = 1
    crypto_epoch: int = 1


@dataclass(frozen=True, slots=True)
class AccessCheckContext:
    principal_hash: str
    pop_session_active: bool
    policy_allowed: bool
    requested_scope: str | None = None
    requested_metric_group: str | None = None
    history_days: int | None = None
    interval_seconds: int | None = None
    quota_cost: int = 0
    quota_remaining: int | None = None
    step_up_fresh: bool = False
    access_certificate_present: bool = False
    revoked: bool = False


class InMemoryWalletEntitlementRepository:
    def __init__(self) -> None:
        self._lock = RLock()
        self.by_entitlement_hash: dict[str, WalletSubscriptionEntitlement] = {}
        self.by_principal: dict[str, WalletSubscriptionEntitlement] = {}
        self.payment_bindings: dict[str, str] = {}
        self.frozen_children: dict[str, set[str]] = {}

    def save(self, entitlement: WalletSubscriptionEntitlement) -> WalletSubscriptionEntitlement:
        with self._lock:
            self.by_entitlement_hash[entitlement.entitlement_id_hash] = entitlement
            self.by_principal[entitlement.principal_hash] = entitlement
            if entitlement.payment_proof_hash:
                self.payment_bindings[entitlement.payment_proof_hash] = entitlement.entitlement_id_hash
            return entitlement

    def get_by_payment_proof(self, payment_proof_hash: str) -> WalletSubscriptionEntitlement | None:
        with self._lock:
            entitlement_hash = self.payment_bindings.get(payment_proof_hash)
            return self.by_entitlement_hash.get(entitlement_hash) if entitlement_hash else None

    def get_by_hash(self, entitlement_id_hash: str) -> WalletSubscriptionEntitlement | None:
        return self.by_entitlement_hash.get(entitlement_id_hash)

    def current_for_principal(self, principal_hash: str) -> WalletSubscriptionEntitlement | None:
        return self.by_principal.get(principal_hash)

    def freeze_child(self, parent_entitlement_hash: str, child_hash: str) -> None:
        self.frozen_children.setdefault(parent_entitlement_hash, set()).add(child_hash)


class WalletBoundSubscriptionEntitlementService:
    def __init__(self, repository: InMemoryWalletEntitlementRepository | None = None, audit_emitter: AuditEmitter | None = None) -> None:
        self.repository = repository or InMemoryWalletEntitlementRepository()
        self.audit_emitter = audit_emitter

    def issue_wallet_bound_entitlement(
        self,
        *,
        principal: PrincipalState,
        verified_payment_proof: VerifiedPaymentProofRef,
        plan_code: PlanCode | str,
        payment_method: EntitlementPaymentMethod | str,
        valid_from: datetime,
        valid_until: datetime,
        issuer_context: IssuerContext,
        parent_entitlement_hash: str | None = None,
        workspace_id_hash: str | None = None,
        assurance: EntitlementAssurance | None = None,
    ) -> WalletSubscriptionEntitlement:
        self._validate_principal(principal)
        existing = self.repository.get_by_payment_proof(verified_payment_proof.payment_proof_hash)
        if existing is not None:
            if existing.principal_hash != principal.principal_hash or existing.plan_code != normalize_plan_code(plan_code).value:
                raise EntitlementPolicyError("payment_proof_binding_conflict")
            return existing
        self._validate_payment_proof(verified_payment_proof, plan_code, principal.principal_hash)
        payment_method = EntitlementPaymentMethod(payment_method)
        if payment_method is EntitlementPaymentMethod.MANUAL_GRANT:
            raise EntitlementPolicyError("manual_grant_disabled")
        entitlement = self._build_unsigned_entitlement(
            principal=principal,
            payment_proof=verified_payment_proof,
            plan_code=plan_code,
            payment_method=payment_method,
            valid_from=valid_from,
            valid_until=valid_until,
            issuer_context=issuer_context,
            parent_entitlement_hash=parent_entitlement_hash,
            workspace_id_hash=workspace_id_hash or principal.workspace_id_hash,
            assurance=assurance,
            status=WalletEntitlementStatus.ACTIVE,
        )
        signed = self._sign(entitlement, issuer_context)
        self.repository.save(signed)
        event_name = "lightning_entitlement_issued" if principal.subject_type is EntitlementSubjectType.LIGHTNING_WALLET_PRINCIPAL else "wallet_entitlement_issued"
        self._emit(event_name, signed, {"payment_proof_hash": verified_payment_proof.payment_proof_hash})
        return signed

    def renew_entitlement(self, entitlement: WalletSubscriptionEntitlement, *, payment_proof: VerifiedPaymentProofRef, valid_until: datetime, issuer_context: IssuerContext) -> WalletSubscriptionEntitlement:
        if payment_proof.payment_proof_hash == entitlement.payment_proof_hash:
            raise EntitlementPolicyError("duplicate_renewal_payment_proof")
        renewal = replace(entitlement, valid_until=valid_until, payment_proof_hash=payment_proof.payment_proof_hash, issued_at=datetime.now(UTC), issuer_signatures=())
        signed = self._sign(renewal, issuer_context)
        self.repository.save(signed)
        self._emit("entitlement_renewed", signed, {"old_entitlement_hash": entitlement.entitlement_id_hash})
        return signed

    def upgrade_entitlement(self, entitlement: WalletSubscriptionEntitlement, *, new_plan_code: PlanCode | str, payment_proof: VerifiedPaymentProofRef, issuer_context: IssuerContext, step_up_fresh: bool = False) -> WalletSubscriptionEntitlement:
        new_plan = normalize_plan_code(new_plan_code)
        if plan_rank(new_plan) <= plan_rank(normalize_plan_code(entitlement.plan_code)):
            raise EntitlementPolicyError("upgrade_requires_higher_plan")
        if not step_up_fresh and new_plan in {PlanCode.PRO, PlanCode.BUSINESS, PlanCode.ENTERPRISE}:
            raise EntitlementPolicyError("upgrade_step_up_required")
        upgraded = self._reprofile(entitlement, new_plan, issuer_context, payment_proof.payment_proof_hash)
        self.repository.save(upgraded)
        self._emit("entitlement_upgraded", upgraded, {"old_plan": entitlement.plan_code, "new_plan": new_plan.value, "child_keys_not_modified": True})
        return upgraded

    def schedule_downgrade(self, entitlement: WalletSubscriptionEntitlement, *, new_plan_code: PlanCode | str, effective_at: datetime, issuer_context: IssuerContext) -> WalletSubscriptionEntitlement:
        new_plan = normalize_plan_code(new_plan_code)
        if plan_rank(new_plan) >= plan_rank(normalize_plan_code(entitlement.plan_code)):
            raise EntitlementPolicyError("downgrade_requires_lower_plan")
        scheduled = replace(entitlement, status=WalletEntitlementStatus.DOWNGRADE_PENDING, metadata={**entitlement.metadata, "downgrade_to_plan": new_plan.value, "downgrade_effective_at": effective_at.isoformat().replace("+00:00", "Z")}, issuer_signatures=())
        signed = self._sign(scheduled, issuer_context)
        self.repository.save(signed)
        self._emit("entitlement_downgrade_scheduled", signed, {"new_plan": new_plan.value})
        return signed

    def apply_downgrade(self, entitlement: WalletSubscriptionEntitlement, *, new_plan_code: PlanCode | str, issuer_context: IssuerContext, child_hashes: list[str] | None = None) -> WalletSubscriptionEntitlement:
        new_plan = normalize_plan_code(new_plan_code)
        downgraded = self._reprofile(entitlement, new_plan, issuer_context, entitlement.payment_proof_hash)
        for child_hash in child_hashes or []:
            self.repository.freeze_child(entitlement.entitlement_id_hash, child_hash)
            self._emit("entitlement_child_key_frozen", downgraded, {"affected_child_object_hash": child_hash})
        self.repository.save(downgraded)
        self._emit("entitlement_downgraded", downgraded, {"old_plan": entitlement.plan_code, "new_plan": new_plan.value, "offline_pack_invalidated": True})
        return downgraded

    def suspend_entitlement(self, entitlement: WalletSubscriptionEntitlement, *, reason: str, issuer_context: IssuerContext) -> WalletSubscriptionEntitlement:
        return self._status_transition(entitlement, WalletEntitlementStatus.SUSPENDED, issuer_context, "entitlement_suspended", reason)

    def resume_entitlement(self, entitlement: WalletSubscriptionEntitlement, *, issuer_context: IssuerContext) -> WalletSubscriptionEntitlement:
        return self._status_transition(entitlement, WalletEntitlementStatus.ACTIVE, issuer_context, "entitlement_resumed", "resumed")

    def expire_entitlement(self, entitlement: WalletSubscriptionEntitlement, *, issuer_context: IssuerContext) -> WalletSubscriptionEntitlement:
        return self._status_transition(entitlement, WalletEntitlementStatus.EXPIRED, issuer_context, "entitlement_expired", "expired")

    def revoke_entitlement(self, entitlement: WalletSubscriptionEntitlement, *, reason: str, issuer_context: IssuerContext) -> WalletSubscriptionEntitlement:
        revoked = self._status_transition(entitlement, WalletEntitlementStatus.REVOKED, issuer_context, "entitlement_revoked", reason)
        self._emit("entitlement_delegated_pass_frozen", revoked, {"reason_code": reason})
        self._emit("entitlement_offline_pack_invalidated", revoked, {"reason_code": reason})
        return revoked

    def lock_for_recovery(self, entitlement: WalletSubscriptionEntitlement, *, issuer_context: IssuerContext) -> WalletSubscriptionEntitlement:
        return self._status_transition(entitlement, WalletEntitlementStatus.RECOVERY_LOCKED, issuer_context, "entitlement_recovery_locked", "recovery_locked")

    def resolve_effective_entitlement(
        self,
        *,
        entitlement: WalletSubscriptionEntitlement,
        access_certificate: EntitlementRestriction | None = None,
        business_role: EntitlementRestriction | None = None,
        delegated_pass: EntitlementRestriction | None = None,
        child_api_key: EntitlementRestriction | None = None,
        policy_context: dict[str, Any] | None = None,
    ) -> EffectiveEntitlement:
        reasons: list[str] = []
        if entitlement.status not in ACTIVE_ENTITLEMENT_STATUSES:
            return EffectiveEntitlement(entitlement.entitlement_id_hash, entitlement.subject_type, entitlement.principal_hash, entitlement.plan_code, entitlement.status.value, frozenset(), frozenset(), entitlement.limits, entitlement.assurance, False, "deny", (f"entitlement_{entitlement.status.value}",))
        scopes = entitlement.scopes
        metric_groups = entitlement.metric_groups
        limits = entitlement.limits
        requires_step_up = entitlement.assurance.high_risk_step_up_required
        for restriction in (access_certificate, business_role, delegated_pass, child_api_key):
            if restriction is None:
                continue
            if restriction.revoked:
                return EffectiveEntitlement(entitlement.entitlement_id_hash, entitlement.subject_type, entitlement.principal_hash, entitlement.plan_code, "revoked", frozenset(), frozenset(), limits, entitlement.assurance, False, "deny", (restriction.reason or "restriction_revoked",))
            if restriction.scopes is not None:
                scopes &= restriction.scopes
            if restriction.metric_groups is not None:
                metric_groups &= restriction.metric_groups
            limits = limits.narrowed_with(restriction.limits)
            requires_step_up = requires_step_up or restriction.requires_step_up
        if policy_context and policy_context.get("recovery_locked"):
            scopes = frozenset(scope for scope in scopes if scope.startswith("recovery:"))
            metric_groups = frozenset()
            reasons.append("recovery_only")
        return EffectiveEntitlement(entitlement.entitlement_id_hash, entitlement.subject_type, entitlement.principal_hash, entitlement.plan_code, entitlement.status.value, scopes, metric_groups, limits, entitlement.assurance, requires_step_up, "allow", tuple(reasons or ["effective_entitlement_resolved"]))

    def validate_protected_access(self, entitlement: WalletSubscriptionEntitlement, context: AccessCheckContext) -> AccessDecision:
        if context.revoked or entitlement.status == WalletEntitlementStatus.REVOKED:
            return AccessDecision(PolicyDecision.REVOKED, "entitlement_revoked")
        if entitlement.principal_hash != context.principal_hash:
            return AccessDecision(PolicyDecision.DENY, "principal_binding_mismatch")
        if not context.pop_session_active:
            return AccessDecision(PolicyDecision.INVALID_SESSION, "pop_session_required")
        if not context.policy_allowed:
            return AccessDecision(PolicyDecision.DENY, "policy_engine_denied")
        if entitlement.assurance.access_certificate_required and not context.access_certificate_present:
            return AccessDecision(PolicyDecision.ONLINE_CHECK_REQUIRED, "access_certificate_required")
        if entitlement.assurance.high_risk_step_up_required and not context.step_up_fresh:
            return AccessDecision(PolicyDecision.STEP_UP_REQUIRED, "fresh_step_up_required")
        effective = self.resolve_effective_entitlement(entitlement=entitlement)
        if context.requested_scope and context.requested_scope not in effective.scopes:
            return AccessDecision(PolicyDecision.INSUFFICIENT_SCOPE, "scope_not_allowed", requested_scope=context.requested_scope)
        if context.requested_metric_group and context.requested_metric_group not in effective.metric_groups:
            return AccessDecision(PolicyDecision.METRIC_NOT_ALLOWED, "metric_not_allowed", requested_metric_group=context.requested_metric_group)
        if context.history_days is not None and effective.limits.history_days is not None and context.history_days > effective.limits.history_days:
            return AccessDecision(PolicyDecision.DENY, "history_range_not_allowed")
        if context.interval_seconds is not None and effective.limits.minimum_interval_seconds is not None and context.interval_seconds < effective.limits.minimum_interval_seconds:
            return AccessDecision(PolicyDecision.DENY, "interval_not_allowed")
        if context.quota_remaining is not None and context.quota_cost > context.quota_remaining:
            return AccessDecision(PolicyDecision.QUOTA_EXCEEDED, "quota_exceeded")
        return AccessDecision(PolicyDecision.ALLOW, "entitlement_policy_allowed")

    def verify_entitlement(self, entitlement: WalletSubscriptionEntitlement, public_key: str) -> bool:
        if not entitlement.issuer_signatures:
            return False
        signature = entitlement.issuer_signatures[0]
        if signature.alg != "ed25519":
            raise EntitlementSignatureVerificationError("unsupported_signature_suite")
        return verify_subscription_entitlement_signature(entitlement.signed_payload(), public_key, signature.sig).valid

    def _build_unsigned_entitlement(self, *, principal: PrincipalState, payment_proof: VerifiedPaymentProofRef, plan_code: PlanCode | str, payment_method: EntitlementPaymentMethod, valid_from: datetime, valid_until: datetime, issuer_context: IssuerContext, parent_entitlement_hash: str | None, workspace_id_hash: str | None, assurance: EntitlementAssurance | None, status: WalletEntitlementStatus) -> WalletSubscriptionEntitlement:
        if valid_until <= valid_from:
            raise EntitlementPolicyError("invalid_validity_window")
        plan = normalize_plan_code(plan_code)
        limits = _limits_for_plan(plan)
        entitlement_id_hash = hash_canonical_json_prefixed({"principal_hash": principal.principal_hash, "payment_proof_hash": payment_proof.payment_proof_hash, "plan_code": plan.value, "schema_epoch": issuer_context.schema_epoch})
        return WalletSubscriptionEntitlement(
            type=ENTITLEMENT_TYPE,
            version=ENTITLEMENT_VERSION,
            entitlement_id_hash=entitlement_id_hash,
            subject_type=principal.subject_type,
            principal_hash=principal.principal_hash,
            parent_entitlement_hash=parent_entitlement_hash,
            workspace_id_hash=workspace_id_hash,
            plan_code=plan.value,
            status=status,
            wallet_bound=principal.subject_type in {EntitlementSubjectType.BITCOIN_WALLET_PRINCIPAL, EntitlementSubjectType.LIGHTNING_WALLET_PRINCIPAL},
            payment_method=payment_method,
            payment_proof_hash=payment_proof.payment_proof_hash,
            metric_groups=frozenset(get_plan_metric_groups(plan)),
            scopes=frozenset(get_plan_scopes(plan)),
            limits=limits,
            assurance=assurance or _assurance_for_plan(plan),
            issued_at=datetime.now(UTC),
            valid_from=valid_from,
            valid_until=valid_until,
            grace_until=None,
            schema_epoch=issuer_context.schema_epoch,
            policy_epoch=issuer_context.policy_epoch,
            crypto_epoch=issuer_context.crypto_epoch,
            issuer_key_id=issuer_context.issuer_key_id,
            issuer_signatures=(),
            metadata={"network": payment_proof.network, "product_code": payment_proof.product_code},
        )

    def _sign(self, entitlement: WalletSubscriptionEntitlement, issuer_context: IssuerContext) -> WalletSubscriptionEntitlement:
        reject_forbidden_secret_keys(entitlement.public_payload())
        signature = sign_subscription_entitlement(entitlement.signed_payload(), issuer_context.issuer_private_key, issuer_context.issuer_key_id, issuer_context.crypto_epoch)
        metadata = IssuerSignatureMetadata(signature.alg, signature.key_id, signature.signature, signature.crypto_epoch, signature.public_key_fingerprint)
        return replace(entitlement, issuer_signatures=(metadata,))

    def _reprofile(self, entitlement: WalletSubscriptionEntitlement, plan: PlanCode, issuer_context: IssuerContext, payment_proof_hash: str | None) -> WalletSubscriptionEntitlement:
        profiled = replace(
            entitlement,
            plan_code=plan.value,
            status=WalletEntitlementStatus.ACTIVE,
            payment_proof_hash=payment_proof_hash,
            metric_groups=frozenset(get_plan_metric_groups(plan)),
            scopes=frozenset(get_plan_scopes(plan)),
            limits=_limits_for_plan(plan),
            assurance=_assurance_for_plan(plan),
            issued_at=datetime.now(UTC),
            policy_epoch=issuer_context.policy_epoch,
            crypto_epoch=issuer_context.crypto_epoch,
            issuer_key_id=issuer_context.issuer_key_id,
            issuer_signatures=(),
        )
        return self._sign(profiled, issuer_context)

    def _status_transition(self, entitlement: WalletSubscriptionEntitlement, status: WalletEntitlementStatus, issuer_context: IssuerContext, event_type: str, reason: str) -> WalletSubscriptionEntitlement:
        updated = replace(entitlement, status=status, metadata={**entitlement.metadata, "reason_code": reason}, issuer_signatures=())
        signed = self._sign(updated, issuer_context)
        self.repository.save(signed)
        self._emit(event_type, signed, {"reason_code": reason})
        return signed

    def _validate_principal(self, principal: PrincipalState) -> None:
        if not principal.principal_hash.startswith("hmac-sha256:"):
            raise EntitlementPolicyError("principal_hash_required")
        if principal.revoked or principal.status != "active":
            raise EntitlementPolicyError("principal_revoked_or_inactive")
        if principal.subject_type in {EntitlementSubjectType.CHILD_API_KEY, EntitlementSubjectType.DELEGATED_PASS}:
            raise EntitlementPolicyError("child_subject_requires_parent_entitlement")

    def _validate_payment_proof(self, proof: VerifiedPaymentProofRef, plan_code: PlanCode | str, principal_hash: str) -> None:
        if not proof.payment_proof_hash.startswith("sha256:"):
            raise EntitlementPolicyError("payment_proof_hash_required")
        if not proof.verified or not proof.settled:
            raise EntitlementPolicyError("payment_proof_not_settled_or_verified")
        if proof.expires_at is not None and proof.expires_at <= datetime.now(UTC):
            raise EntitlementPolicyError("payment_proof_expired")
        if normalize_plan_code(proof.plan_code) != normalize_plan_code(plan_code):
            raise EntitlementPolicyError("payment_plan_mismatch")
        if proof.principal_hash is not None and proof.principal_hash != principal_hash:
            raise EntitlementPolicyError("payerdata_auth_binding_mismatch")

    def _emit(self, event_type: str, entitlement: WalletSubscriptionEntitlement, extra: dict[str, Any] | None = None) -> None:
        if self.audit_emitter is None:
            return
        payload = {
            "principal_hash": entitlement.principal_hash,
            "entitlement_hash": entitlement.entitlement_id_hash,
            "plan_code": entitlement.plan_code,
            "payment_proof_hash": entitlement.payment_proof_hash,
            "policy_epoch": entitlement.policy_epoch,
            "issuer_key_id": entitlement.issuer_key_id,
            "reason_code": (extra or {}).get("reason_code"),
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            **(extra or {}),
        }
        reject_forbidden_secret_keys(payload)
        self.audit_emitter(event_type, payload)


def _limits_for_plan(plan: PlanCode) -> EntitlementLimits:
    limits = get_plan_limits(plan)
    return EntitlementLimits(
        requests_per_minute=limits.requests_per_minute,
        requests_per_day=limits.requests_per_day,
        daily_metric_credits=limits.daily_metric_credits,
        monthly_metric_credits=limits.monthly_metric_credits,
        history_days=limits.max_history_days,
        minimum_interval_seconds=_parse_interval_seconds(limits.min_interval),
        child_api_keys=limits.child_api_keys,
        delegated_passes=limits.child_api_keys,
        concurrent_sessions=limits.websocket_streams,
    )


def _assurance_for_plan(plan: PlanCode) -> EntitlementAssurance:
    return EntitlementAssurance(
        minimum_proof_strength="high" if plan in {PlanCode.BUSINESS, PlanCode.ENTERPRISE} else "standard",
        high_risk_step_up_required=True,
        access_certificate_required=plan in {PlanCode.PRO, PlanCode.BUSINESS, PlanCode.ENTERPRISE},
        hardware_wallet_required=plan is PlanCode.ENTERPRISE,
        quorum_policy={"required": 2} if plan is PlanCode.ENTERPRISE else None,
        sovereign_mode=False,
    )


def _parse_interval_seconds(value: str | None) -> int | None:
    if value is None:
        return None
    suffix = value[-1]
    amount = int(value[:-1])
    return amount * {"s": 1, "m": 60, "h": 3600, "d": 86400}[suffix]


def payment_proof_fingerprint(value: str) -> str:
    return sha256_prefixed(value)
