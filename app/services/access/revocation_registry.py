"""Revocation registry for Bastion Proof-of-Access Auth.

The registry is a security boundary for hashed/fingerprinted Access material.
It records revocations for passes, certificates, devices, sessions, child keys,
delegated passes, issuer keys, and recovery/business objects without storing raw
Access Passes, raw session tokens, recovery material, private keys, or wallet
secrets.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.access import AccessCertificate, AccessRevocation, AccessSession, ChildApiKey, DelegatedPass

REVOCATION_TARGET_TYPES: frozenset[str] = frozenset(
    {
        "pass",
        "certificate",
        "entitlement",
        "device",
        "session",
        "child_api_key",
        "delegated_pass",
        "offline_pack",
        "issuer_key",
        "business_role",
        "recovery_attempt",
    }
)
REVOCATION_REASONS: frozenset[str] = frozenset(
    {
        "user_lockdown",
        "suspected_compromise",
        "device_lost",
        "session_replay_detected",
        "subscription_expired",
        "subscription_downgraded",
        "child_scope_violation",
        "delegated_pass_expired",
        "business_role_removed",
        "issuer_key_rotation",
        "issuer_key_compromised",
        "recovery_abuse",
        "admin_policy",
        "manual_security_action",
    }
)
AuditEmitter = Callable[[str, dict[str, Any]], None]


class RevocationRegistryError(ValueError):
    """Base revocation error with secret-free messages."""


class InvalidRevocationTargetTypeError(RevocationRegistryError):
    """Raised when a target type is not allow-listed."""


class InvalidRevocationReasonError(RevocationRegistryError):
    """Raised when a revocation reason is not allow-listed."""


@dataclass(frozen=True, slots=True)
class RevocationStatus:
    revoked: bool
    target_type: str
    target_hash: str
    reason: str | None = None
    revocation_epoch: int | None = None
    revoked_at: datetime | None = None
    decision_hint: str | None = None

    def __bool__(self) -> bool:
        return self.revoked


class RevocationRegistry:
    def __init__(self, *, audit_emitter: AuditEmitter | None = None) -> None:
        self.audit_emitter = audit_emitter

    def revoke_target(
        self,
        db: Session,
        *,
        target_type: str,
        target_hash: str,
        reason: str,
        actor_hash: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RevocationStatus:
        target_type = self._validate_target_type(target_type)
        reason = self._validate_reason(reason)
        self._validate_target_hash(target_hash)
        existing = self._get_existing(db, target_type=target_type, target_hash=target_hash)
        if existing is not None:
            return self._status_from_model(existing)
        epoch = self.next_revocation_epoch(db)
        revocation = AccessRevocation(
            target_type=target_type,
            target_hash=target_hash,
            reason=reason,
            revocation_epoch=epoch,
            created_by_hash=actor_hash,
            signature_id=None,
            metadata_json=self._redact_metadata(metadata or {}),
            created_at=datetime.now(UTC),
        )
        db.add(revocation)
        db.flush()
        self._emit_audit(
            "access_target_revoked",
            target_type=target_type,
            target_hash=target_hash,
            reason=reason,
            actor_hash=actor_hash,
            revocation_epoch=epoch,
            metadata=revocation.metadata_json,
        )
        return self._status_from_model(revocation)

    def is_revoked(self, db: Session, *, target_type: str, target_hash: str) -> RevocationStatus:
        target_type = self._validate_target_type(target_type)
        self._validate_target_hash(target_hash)
        existing = self._get_existing(db, target_type=target_type, target_hash=target_hash)
        if existing is None:
            return RevocationStatus(
                revoked=False,
                target_type=target_type,
                target_hash=target_hash,
                decision_hint="not_revoked",
            )
        return self._status_from_model(existing)

    def revoke_pass_tree(
        self,
        db: Session,
        *,
        pass_lookup_hash: str,
        reason: str,
        actor_hash: str | None = None,
    ) -> dict[str, Any]:
        reason = self._validate_reason(reason)
        pass_status = self.revoke_target(
            db,
            target_type="pass",
            target_hash=pass_lookup_hash,
            reason=reason,
            actor_hash=actor_hash,
        )
        sessions_revoked = 0
        child_api_keys_revoked = 0
        delegated_passes_revoked = 0
        warnings: list[str] = []
        certificates = db.execute(
            select(AccessCertificate).where(AccessCertificate.pass_lookup_hash == pass_lookup_hash)
        ).scalars().all()
        for certificate in certificates:
            self.revoke_target(
                db,
                target_type="certificate",
                target_hash=certificate.certificate_fingerprint,
                reason=reason,
                actor_hash=actor_hash,
            )
            for session in db.execute(
                select(AccessSession).where(AccessSession.certificate_fingerprint == certificate.certificate_fingerprint)
            ).scalars():
                status = self.freeze_session(
                    db,
                    session_hash=session.session_hash,
                    reason=reason,
                    actor_hash=actor_hash,
                )
                sessions_revoked += int(status.revoked)
        for child in db.execute(select(ChildApiKey).where(ChildApiKey.parent_pass_lookup_hash == pass_lookup_hash)).scalars():
            status = self.revoke_child_api_key(
                db,
                key_hash=child.key_id_hash,
                reason=reason,
                actor_hash=actor_hash,
            )
            child_api_keys_revoked += int(status.revoked)
        for delegated in db.execute(
            select(DelegatedPass).where(DelegatedPass.parent_pass_lookup_hash == pass_lookup_hash)
        ).scalars():
            status = self.revoke_delegated_pass(
                db,
                delegated_pass_hash=delegated.delegated_pass_hash,
                reason=reason,
                actor_hash=actor_hash,
            )
            delegated_passes_revoked += int(status.revoked)
        summary = {
            "pass_revoked": pass_status.revoked,
            "sessions_revoked": sessions_revoked,
            "child_api_keys_revoked": child_api_keys_revoked,
            "delegated_passes_revoked": delegated_passes_revoked,
            "offline_packs_invalidated": 0,
            "warnings": warnings,
        }
        self._emit_audit(
            "access_pass_tree_revoked",
            target_type="pass",
            target_hash=pass_lookup_hash,
            reason=reason,
            actor_hash=actor_hash,
            revocation_epoch=pass_status.revocation_epoch,
            metadata=summary,
        )
        return summary

    def freeze_session(
        self,
        db: Session,
        *,
        session_hash: str,
        reason: str,
        actor_hash: str | None = None,
    ) -> RevocationStatus:
        status = self.revoke_target(db, target_type="session", target_hash=session_hash, reason=reason, actor_hash=actor_hash)
        self._emit_named_target_event("access_session_frozen", status=status, actor_hash=actor_hash)
        return status

    def revoke_device(
        self,
        db: Session,
        *,
        device_key_fingerprint: str,
        reason: str,
        actor_hash: str | None = None,
    ) -> RevocationStatus:
        status = self.revoke_target(
            db,
            target_type="device",
            target_hash=device_key_fingerprint,
            reason=reason,
            actor_hash=actor_hash,
        )
        self._emit_named_target_event("access_device_revoked", status=status, actor_hash=actor_hash)
        return status

    def revoke_child_api_key(
        self,
        db: Session,
        *,
        key_hash: str,
        reason: str,
        actor_hash: str | None = None,
    ) -> RevocationStatus:
        status = self.revoke_target(db, target_type="child_api_key", target_hash=key_hash, reason=reason, actor_hash=actor_hash)
        self._emit_named_target_event("child_api_key_revoked", status=status, actor_hash=actor_hash)
        return status

    def revoke_delegated_pass(
        self,
        db: Session,
        *,
        delegated_pass_hash: str,
        reason: str,
        actor_hash: str | None = None,
    ) -> RevocationStatus:
        status = self.revoke_target(
            db,
            target_type="delegated_pass",
            target_hash=delegated_pass_hash,
            reason=reason,
            actor_hash=actor_hash,
        )
        self._emit_named_target_event("delegated_pass_revoked", status=status, actor_hash=actor_hash)
        return status

    def check_access_material(
        self,
        db: Session,
        *,
        pass_lookup_hash: str | None = None,
        certificate_fingerprint: str | None = None,
        entitlement_hash: str | None = None,
        device_key_fingerprint: str | None = None,
        session_hash: str | None = None,
        child_api_key_hash: str | None = None,
        delegated_pass_hash: str | None = None,
    ) -> dict[str, Any]:
        candidates = {
            "pass": pass_lookup_hash,
            "certificate": certificate_fingerprint,
            "entitlement": entitlement_hash,
            "device": device_key_fingerprint,
            "session": session_hash,
            "child_api_key": child_api_key_hash,
            "delegated_pass": delegated_pass_hash,
        }
        revoked_targets: list[dict[str, Any]] = []
        for target_type, target_hash in candidates.items():
            if target_hash is None:
                continue
            status = self.is_revoked(db, target_type=target_type, target_hash=target_hash)
            if status.revoked:
                revoked_targets.append(
                    {
                        "target_type": status.target_type,
                        "target_hash": status.target_hash,
                        "reason": status.reason,
                        "revocation_epoch": status.revocation_epoch,
                    }
                )
        return {
            "allowed": not revoked_targets,
            "revoked_targets": revoked_targets,
            "decision": "revoked" if revoked_targets else "not_revoked",
        }

    def next_revocation_epoch(self, db: Session) -> int:
        max_epoch = db.execute(select(func.max(AccessRevocation.revocation_epoch))).scalar_one_or_none()
        return int(max_epoch or 0) + 1

    def _get_existing(self, db: Session, *, target_type: str, target_hash: str) -> AccessRevocation | None:
        return db.execute(
            select(AccessRevocation)
            .where(
                AccessRevocation.target_type == target_type,
                AccessRevocation.target_hash == target_hash,
            )
            .order_by(AccessRevocation.revocation_epoch.desc(), AccessRevocation.id.desc())
        ).scalars().first()

    def _status_from_model(self, revocation: AccessRevocation) -> RevocationStatus:
        return RevocationStatus(
            revoked=True,
            target_type=revocation.target_type,
            target_hash=revocation.target_hash,
            reason=revocation.reason,
            revocation_epoch=revocation.revocation_epoch,
            revoked_at=revocation.created_at,
            decision_hint="revoked",
        )

    def _validate_target_type(self, target_type: str) -> str:
        normalized = target_type.strip().lower()
        if normalized not in REVOCATION_TARGET_TYPES:
            raise InvalidRevocationTargetTypeError("invalid_revocation_target_type")
        return normalized

    def _validate_reason(self, reason: str) -> str:
        normalized = reason.strip().lower()
        if normalized not in REVOCATION_REASONS:
            raise InvalidRevocationReasonError("invalid_revocation_reason")
        return normalized

    def _validate_target_hash(self, target_hash: str) -> None:
        if not isinstance(target_hash, str) or not target_hash.strip():
            raise RevocationRegistryError("invalid_revocation_target_hash")
        lowered = target_hash.lower()
        if lowered.startswith("bbp_live_") or target_hash.startswith("BBP-"):
            raise RevocationRegistryError("raw_access_pass_not_allowed")

    def _redact_metadata(self, metadata: Mapping[str, Any]) -> dict[str, Any]:
        redacted: dict[str, Any] = {}
        for key, value in metadata.items():
            lowered = str(key).lower()
            if any(secret in lowered for secret in ("secret", "token", "raw_pass", "access_pass", "private_key", "seed")):
                redacted[str(key)] = "[REDACTED]"
            else:
                redacted[str(key)] = value
        return redacted

    def _emit_named_target_event(self, event_type: str, *, status: RevocationStatus, actor_hash: str | None) -> None:
        self._emit_audit(
            event_type,
            target_type=status.target_type,
            target_hash=status.target_hash,
            reason=status.reason or "manual_security_action",
            actor_hash=actor_hash,
            revocation_epoch=status.revocation_epoch,
            metadata={},
        )

    def _emit_audit(
        self,
        event_type: str,
        *,
        target_type: str,
        target_hash: str,
        reason: str,
        actor_hash: str | None,
        revocation_epoch: int | None,
        metadata: Mapping[str, Any] | None,
    ) -> None:
        if self.audit_emitter is None:
            return
        self.audit_emitter(
            event_type,
            {
                "target_type": target_type,
                "target_hash": target_hash,
                "reason": reason,
                "actor_hash": actor_hash,
                "revocation_epoch": revocation_epoch,
                "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "metadata": self._redact_metadata(metadata or {}),
            },
        )
