"""Emergency Lockdown Mode for Bastion Proof-of-Access Auth."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.access import AccessAuditEvent, AccessDevice, AccessSession, ChildApiKey, DelegatedPass
from app.schemas.access import AccessLockdownRequest, AccessLockdownScope
from app.services.access.audit_chain import AccessAuditChain
from app.services.access.crypto.hashing import secure_nonce_hex
from app.services.access.policy_context import AccessPolicyContext, AccessPolicyDecision
from app.services.access.policy_engine import AccessPolicyEngine
from app.services.access.revocation_registry import RevocationRegistry

LOCKDOWN_STATUS = "locked_down"
LOCKDOWN_REASON = "user_lockdown"
LOCKDOWN_EVENT_TYPE = "access_lockdown_started"


class PolicyEngine(Protocol):
    def evaluate(self, context: AccessPolicyContext | None) -> AccessPolicyDecision: ...


class LockdownError(ValueError):
    pass


@dataclass(frozen=True)
class AccessLockdownResult:
    status: str
    lockdown_id: str
    affected_sessions: int
    affected_child_api_keys: int
    affected_delegated_passes: int
    affected_devices: int
    affected_offline_packs: int
    recovery_only: bool
    audit_event_hash: str
    created_at: datetime


class LockdownService:
    def __init__(
        self,
        db: Session,
        *,
        policy_engine: PolicyEngine | None = None,
        revocation_registry: RevocationRegistry | None = None,
        audit_chain: AccessAuditChain | None = None,
    ) -> None:
        self.db = db
        self.policy_engine = policy_engine or AccessPolicyEngine()
        self.revocation_registry = revocation_registry or RevocationRegistry()
        self.audit_chain = audit_chain or AccessAuditChain(db)

    def start_lockdown(self, access_context: Any, request: AccessLockdownRequest) -> AccessLockdownResult:
        self._validate_request(access_context, request)
        decision = self._policy_decision(access_context, request)
        if not decision.allowed:
            raise LockdownError(decision.reason_code or "lockdown_policy_denied")
        now = datetime.now(UTC)
        lockdown_id = f"lock_{secure_nonce_hex(16)}"
        pass_lookup_hash = getattr(access_context, "pass_lookup_hash", None)
        certificate_fingerprint = getattr(access_context, "certificate_fingerprint", None)
        actor_hash = getattr(access_context, "session_hash", getattr(access_context, "session_id_hash", None))
        workspace_id_hash = getattr(access_context, "workspace_id_hash", None)
        affected_sessions = self.freeze_sessions(pass_lookup_hash=pass_lookup_hash, certificate_fingerprint=certificate_fingerprint, workspace_id_hash=workspace_id_hash, lockdown_id=lockdown_id, actor_hash=actor_hash)
        affected_child_keys = self.revoke_child_api_keys(pass_lookup_hash=pass_lookup_hash, lockdown_id=lockdown_id, actor_hash=actor_hash)
        affected_delegated = self.revoke_delegated_passes(pass_lookup_hash=pass_lookup_hash, lockdown_id=lockdown_id, actor_hash=actor_hash)
        affected_devices = self.freeze_devices(certificate_fingerprint=certificate_fingerprint, pass_lookup_hash=pass_lookup_hash, scope=request.scope, lockdown_id=lockdown_id, actor_hash=actor_hash)
        affected_offline = self.invalidate_offline_packs(lockdown_id=lockdown_id)
        audit_event = self.build_audit_event(
            lockdown_id=lockdown_id,
            actor_hash=actor_hash,
            pass_lookup_hash=pass_lookup_hash,
            workspace_id_hash=workspace_id_hash,
            scope=request.scope.value,
            reason_class=request.reason or LOCKDOWN_REASON,
            affected_counts={
                "sessions": affected_sessions,
                "child_api_keys": affected_child_keys,
                "delegated_passes": affected_delegated,
                "devices": affected_devices,
                "offline_packs": affected_offline,
            },
            recovery_only=request.recovery_mode,
            policy_decision_id=decision.reason_code,
        )
        self.db.flush()
        return AccessLockdownResult(
            status=LOCKDOWN_STATUS,
            lockdown_id=lockdown_id,
            affected_sessions=affected_sessions,
            affected_child_api_keys=affected_child_keys,
            affected_delegated_passes=affected_delegated,
            affected_devices=affected_devices,
            affected_offline_packs=affected_offline,
            recovery_only=request.recovery_mode,
            audit_event_hash=audit_event.event_hash,
            created_at=now,
        )

    def freeze_sessions(self, *, pass_lookup_hash: str | None, certificate_fingerprint: str | None, workspace_id_hash: str | None = None, lockdown_id: str, actor_hash: str | None) -> int:
        query = select(AccessSession).where(AccessSession.status == "active")
        if workspace_id_hash:
            query = query.where(AccessSession.policy_context_json["workspace_id_hash"].as_string() == workspace_id_hash)
        elif certificate_fingerprint:
            query = query.where(AccessSession.certificate_fingerprint == certificate_fingerprint)
        sessions = list(self.db.execute(query).scalars())
        now = datetime.now(UTC)
        for session in sessions:
            session.status = "frozen"
            session.frozen_at = now
            session.updated_at = now
            self.revocation_registry.freeze_session(
                self.db,
                session_hash=session.session_hash,
                reason=LOCKDOWN_REASON,
                actor_hash=actor_hash,
            )
        return len(sessions)

    def revoke_child_api_keys(self, *, pass_lookup_hash: str | None, lockdown_id: str, actor_hash: str | None) -> int:
        if not pass_lookup_hash:
            return 0
        rows = list(self.db.execute(select(ChildApiKey).where(ChildApiKey.parent_pass_lookup_hash == pass_lookup_hash, ChildApiKey.status == "active")).scalars())
        now = datetime.now(UTC)
        for row in rows:
            row.status = "revoked"
            row.revoked_at = now
            row.limits_json = {**(row.limits_json or {}), "lockdown_id": lockdown_id, "revoked_reason": LOCKDOWN_REASON}
            self.revocation_registry.revoke_child_api_key(self.db, key_hash=row.key_id_hash, reason=LOCKDOWN_REASON, actor_hash=actor_hash)
        return len(rows)

    def revoke_delegated_passes(self, *, pass_lookup_hash: str | None, lockdown_id: str, actor_hash: str | None) -> int:
        if not pass_lookup_hash:
            return 0
        rows = list(self.db.execute(select(DelegatedPass).where(DelegatedPass.parent_pass_lookup_hash == pass_lookup_hash, DelegatedPass.status == "active")).scalars())
        now = datetime.now(UTC)
        for row in rows:
            row.status = "revoked"
            row.revoked_at = now
            row.constraints_json = {**(row.constraints_json or {}), "lockdown_id": lockdown_id, "revoked_reason": LOCKDOWN_REASON}
            self.revocation_registry.revoke_delegated_pass(self.db, delegated_pass_hash=row.delegated_pass_hash, reason=LOCKDOWN_REASON, actor_hash=actor_hash)
        return len(rows)

    def freeze_devices(self, *, certificate_fingerprint: str | None, pass_lookup_hash: str | None, scope: AccessLockdownScope, lockdown_id: str, actor_hash: str | None) -> int:
        if not certificate_fingerprint or scope not in {AccessLockdownScope.ALL_LINKED_DEVICES, AccessLockdownScope.CURRENT_PASS, AccessLockdownScope.BUSINESS_WORKSPACE, AccessLockdownScope.ENTERPRISE_WORKSPACE}:
            return 0
        rows = list(self.db.execute(select(AccessDevice).where(AccessDevice.certificate_fingerprint == certificate_fingerprint, AccessDevice.status.in_(["active", "pending"]))).scalars())
        now = datetime.now(UTC)
        for row in rows:
            row.status = "frozen"
            row.updated_at = now
            row.metadata_json = {**(row.metadata_json or {}), "lockdown_id": lockdown_id, "frozen_reason": LOCKDOWN_REASON}
            self.revocation_registry.revoke_device(self.db, device_key_fingerprint=row.device_key_fingerprint, reason=LOCKDOWN_REASON, actor_hash=actor_hash)
        return len(rows)

    def invalidate_offline_packs(self, *, lockdown_id: str) -> int:
        # TODO: wire Offline Validity Pack table when that prompt lands. Fails safe with zero affected.
        return 0

    def build_audit_event(
        self,
        *,
        lockdown_id: str,
        actor_hash: str | None,
        pass_lookup_hash: str | None,
        workspace_id_hash: str | None,
        scope: str,
        reason_class: str,
        affected_counts: dict[str, int],
        recovery_only: bool,
        policy_decision_id: str | None,
    ) -> AccessAuditEvent:
        return self.audit_chain.record_event(
            event_type=LOCKDOWN_EVENT_TYPE,
            actor_hash=actor_hash,
            object_hash=lockdown_id,
            pass_lookup_hash=pass_lookup_hash,
            workspace_id_hash=workspace_id_hash,
            metadata={
                "lockdown_id": lockdown_id,
                "scope": scope,
                "reason_class": reason_class,
                "affected_counts": affected_counts,
                "revocation_epoch": self.revocation_registry.next_revocation_epoch(self.db),
                "policy_decision_id": policy_decision_id,
                "recovery_only": recovery_only,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

    def get_lockdown_status(self, access_context: Any) -> dict[str, Any]:
        pass_lookup_hash = getattr(access_context, "pass_lookup_hash", None)
        active_sessions = 0
        if getattr(access_context, "certificate_fingerprint", None):
            active_sessions = len(list(self.db.execute(select(AccessSession.id).where(AccessSession.certificate_fingerprint == access_context.certificate_fingerprint, AccessSession.status == "active")).scalars()))
        return {"locked_down": active_sessions == 0, "pass_lookup_hash": pass_lookup_hash, "recovery_available": True}

    def _validate_request(self, access_context: Any, request: AccessLockdownRequest) -> None:
        if access_context is None:
            raise LockdownError("access_context_required")
        if not getattr(access_context, "pass_lookup_hash", None) or not getattr(access_context, "certificate_fingerprint", None):
            raise LockdownError("access_context_incomplete")
        recovery_path = bool(getattr(access_context, "is_recovery_limited", False) or getattr(access_context, "recovery_path_verified", False))
        if not recovery_path and not request.confirmation_intent_signature:
            raise LockdownError("step_up_required")
        if request.scope == AccessLockdownScope.BUSINESS_WORKSPACE and str(getattr(access_context, "plan_code", "")) not in {"business_pass", "enterprise_pass"}:
            raise LockdownError("business_plan_required")
        if request.scope == AccessLockdownScope.ENTERPRISE_WORKSPACE and str(getattr(access_context, "plan_code", "")) != "enterprise_pass":
            raise LockdownError("enterprise_plan_required")

    def _policy_decision(self, access_context: Any, request: AccessLockdownRequest) -> AccessPolicyDecision:
        scopes = set(getattr(access_context, "effective_scopes", getattr(access_context, "scopes", [])) or [])
        return self.policy_engine.evaluate(
            AccessPolicyContext(
                certificate_fingerprint=getattr(access_context, "certificate_fingerprint", None),
                pass_lookup_hash=getattr(access_context, "pass_lookup_hash", None),
                plan_code=getattr(access_context, "plan_code", None),
                effective_scopes=scopes,
                request_risk_level="critical",
                session_id_hash=getattr(access_context, "session_hash", getattr(access_context, "session_id_hash", None)),
                session_status="active",
                session_expires_at=getattr(access_context, "expires_at", getattr(access_context, "session_expires_at", None)),
                entitlement_status="active",
                entitlement_valid_until=getattr(access_context, "expires_at", getattr(access_context, "session_expires_at", None)),
                workspace_id_hash=getattr(access_context, "workspace_id_hash", None),
                is_critical_action=True,
                step_up_present=bool(request.confirmation_intent_signature),
                human_intent_verified=bool(request.confirmation_intent_signature),
                metadata={"action": "access.lockdown.start", "scope": request.scope.value},
            )
        )
