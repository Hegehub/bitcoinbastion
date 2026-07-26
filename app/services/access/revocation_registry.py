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
from enum import StrEnum
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.access import (
    AccessCertificate,
    AccessRevocation,
    AccessSession,
    ChildApiKey,
    DelegatedPass,
)
from app.services.wallet_auth.privacy_commitments import compute_hmac_lookup_hash


class RevocationTargetType(StrEnum):
    """Stable names understood by the single Access revocation registry."""

    ACCESS_CERTIFICATE = "access_certificate"
    SUBSCRIPTION_ENTITLEMENT = "subscription_entitlement"
    METRIC_ENTITLEMENT = "metric_entitlement"
    ACCESS_DEVICE = "access_device"
    ACCESS_SESSION = "access_session"
    CHILD_API_KEY = "child_api_key"
    DELEGATED_PASS = "delegated_pass"
    OFFLINE_VALIDITY_PACK = "offline_validity_pack"
    ISSUER_KEY = "issuer_key"
    RECOVERY_QUORUM = "recovery_quorum"
    WALLET_PRINCIPAL = "wallet_principal"
    BITCOIN_WALLET_PRINCIPAL = "bitcoin_wallet_principal"
    LIGHTNING_WALLET_PRINCIPAL = "lightning_wallet_principal"
    WALLET_PROOF = "wallet_proof"
    WALLET_DEVICE = "wallet_device"
    WALLET_SESSION = "wallet_session"
    WALLET_STEP_UP_PROOF = "wallet_step_up_proof"
    WALLET_RECOVERY_CAPSULE = "wallet_recovery_capsule"
    MULTI_WALLET_QUORUM = "multi_wallet_quorum"
    WALLET_PRIVACY_COMMITMENT = "wallet_privacy_commitment"
    LNURL_AUTH_KEY = "lnurl_auth_key"
    LNURL_AUTH_CHALLENGE = "lnurl_auth_challenge"
    LNURL_K1 = "lnurl_k1"
    LNURL_AUTH_ATTEMPT = "lnurl_auth_attempt"
    LNURL_PAY_REQUEST = "lnurl_pay_request"
    LNURL_PAYMENT_PROOF = "lnurl_payment_proof"
    LNURL_VERIFY_REFERENCE = "lnurl_verify_reference"
    LNURL_WITHDRAW_REQUEST = "lnurl_withdraw_request"
    LNURL_WITHDRAW_ATTEMPT = "lnurl_withdraw_attempt"
    LIGHTNING_ADDRESS = "lightning_address"
    LNURL_PAYERDATA_BINDING = "lnurl_payerdata_binding"
    LNURL_SUCCESS_ACTION_REFERENCE = "lnurl_success_action_reference"
    LNURL_RECOVERY_FACTOR = "lnurl_recovery_factor"
    LNURL_RECOVERY_CHALLENGE = "lnurl_recovery_challenge"
    RECOVERY_ATTEMPT = "recovery_attempt"
    RECOVERY_CAPSULE = "recovery_capsule"
    BUSINESS_WORKSPACE = "business_workspace"
    BUSINESS_ROLE_BINDING = "business_role_binding"
    PAYREGISTER_DEVICE = "payregister_device"
    PAYREGISTER_TERMINAL = "payregister_terminal"
    PAYREGISTER_CASHIER_SHIFT = "payregister_cashier_shift"
    PAYREGISTER_LIGHTNING_ADDRESS = "payregister_lightning_address"
    PAYREGISTER_REFUND_REQUEST = "payregister_refund_request"


class RevocationScope(StrEnum):
    OBJECT_ONLY = "object_only"
    ACTOR_AND_SESSIONS = "actor_and_sessions"
    ACTOR_AND_DEVICES = "actor_and_devices"
    ACTOR_AND_CHILDREN = "actor_and_children"
    ACTOR_FULL_TREE = "actor_full_tree"
    PRODUCT_ONLY = "product_only"
    WORKSPACE_ONLY = "workspace_only"
    DOMAIN_ONLY = "domain_only"
    GLOBAL = "global"
    EMERGENCY_LOCKDOWN = "emergency_lockdown"


class RevocationEntryStatus(StrEnum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"
    REVERSED = "reversed"
    PENDING_PROPAGATION = "pending_propagation"
    PARTIALLY_PROPAGATED = "partially_propagated"


REVOCATION_TARGET_TYPES: frozenset[str] = frozenset(
    {
        *(item.value for item in RevocationTargetType),
        "pass",
        "certificate",
        "entitlement",
        "device",
        "session",
        "child_api_key",
        "delegated_pass",
        "offline_pack",
        "workspace_access",
        "offline_validity_pack",
        "telegram_child_pass",
        "issuer_key",
        "business_role",
        "recovery_attempt",
        "recovery_factor",
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
        "suspected_key_compromise",
        "confirmed_key_compromise",
        "device_stolen",
        "nonce_reuse_detected",
        "signature_verification_failure",
        "malicious_wallet_behavior",
        "policy_violation",
        "audit_integrity_failure",
        "wallet_control_lost",
        "wallet_proof_rotated",
        "wallet_principal_compromised",
        "lnurl_linking_key_compromised",
        "lnurl_k1_reuse_detected",
        "lnurl_auth_domain_migration",
        "lnurl_wallet_compatibility_revoked",
        "lightning_address_disabled",
        "payerdata_binding_revoked",
        "payment_reversed",
        "payment_invalidated",
        "entitlement_expired",
        "entitlement_downgraded",
        "entitlement_fraud",
        "invoice_settlement_disputed",
        "withdraw_request_cancelled",
        "withdraw_k1_compromised",
        "payout_policy_denied",
        "refund_cancelled",
        "payout_limit_exceeded",
        "role_removed",
        "operator_terminated",
        "cashier_shift_closed",
        "terminal_decommissioned",
        "workspace_lockdown",
        "business_owner_action",
        "recovery_started",
        "recovery_completed",
        "recovery_failed",
        "recovery_capsule_rotated",
        "quorum_policy_changed",
        "user_requested",
        "crypto_epoch_migration",
        "policy_epoch_migration",
        "system_migration",
        "emergency_lockdown",
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
    suspended: bool = False
    scope: str = RevocationScope.OBJECT_ONLY
    status: str = RevocationEntryStatus.ACTIVE
    expires_at: datetime | None = None

    def __bool__(self) -> bool:
        return self.revoked


@dataclass(frozen=True, slots=True)
class RevocationResolution:
    revoked: bool
    suspended: bool
    scope: str | None
    reason_code: str | None
    revocation_epoch: int | None
    effective_at: datetime | None
    source_target_type: str | None
    inherited_from_parent: bool
    propagation_status: str
    policy_effect: str
    safe_public_reason: str


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
        scope: RevocationScope | str = RevocationScope.OBJECT_ONLY,
        expires_at: datetime | None = None,
        propagation_status: RevocationEntryStatus | str = RevocationEntryStatus.ACTIVE,
    ) -> RevocationStatus:
        target_type = self._validate_target_type(target_type)
        reason = self._validate_reason(reason)
        self._validate_target_hash(target_hash)
        scope = RevocationScope(scope)
        propagation_status = RevocationEntryStatus(propagation_status)
        existing = self._get_existing(db, target_type=target_type, target_hash=target_hash)
        if existing is not None and self._status_from_model(existing).revoked:
            return self._status_from_model(existing)
        epoch = self.next_revocation_epoch(db)
        entry_metadata = dict(metadata or {})
        if scope is not RevocationScope.OBJECT_ONLY:
            entry_metadata["scope"] = scope.value
        if propagation_status is not RevocationEntryStatus.ACTIVE:
            entry_metadata["status"] = propagation_status.value
        if expires_at is not None:
            entry_metadata["expires_at"] = _iso(expires_at)
        revocation = AccessRevocation(
            target_type=target_type,
            target_hash=target_hash,
            reason=reason,
            revocation_epoch=epoch,
            created_by_hash=actor_hash,
            signature_id=None,
            metadata_json=self._redact_metadata(entry_metadata),
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

    def reverse_revocation(
        self, db: Session, *, target_type: str, target_hash: str, actor_hash: str | None = None
    ) -> RevocationStatus:
        """Append a reversal marker; old sessions/artifacts are never reactivated."""
        target_type = self._validate_target_type(target_type)
        current = self._get_existing(db, target_type=target_type, target_hash=target_hash)
        if current is None or not self._status_from_model(current).revoked:
            return RevocationStatus(
                False,
                target_type,
                target_hash,
                decision_hint="not_revoked",
                status=RevocationEntryStatus.REVERSED,
            )
        row = AccessRevocation(
            target_type=target_type,
            target_hash=target_hash,
            reason=current.reason,
            revocation_epoch=self.next_revocation_epoch(db),
            created_by_hash=actor_hash,
            signature_id=None,
            metadata_json={
                "status": RevocationEntryStatus.REVERSED.value,
                "reverses_epoch": current.revocation_epoch,
                "requires_reauthentication": True,
            },
            created_at=datetime.now(UTC),
        )
        db.add(row)
        db.flush()
        self._emit_audit(
            "revocation_reversed",
            target_type=target_type,
            target_hash=target_hash,
            reason=current.reason,
            actor_hash=actor_hash,
            revocation_epoch=row.revocation_epoch,
            metadata=row.metadata_json,
        )
        return self._status_from_model(row)

    def resolve_revocation_status(
        self,
        db: Session,
        *,
        target_type: str,
        target_hash: str,
        parent_targets: tuple[tuple[str, str], ...] = (),
        at_time: datetime | None = None,
        critical: bool = False,
        authoritative_available: bool = True,
    ) -> RevocationResolution:
        """Resolve direct then bounded parent inheritance; never traverses an unbounded graph."""
        if critical and not authoritative_available:
            return RevocationResolution(
                True,
                False,
                None,
                "revocation_state_unavailable",
                None,
                None,
                None,
                False,
                "unknown",
                "deny",
                "Access cannot be verified.",
            )
        now = at_time or datetime.now(UTC)
        candidates = (
            (target_type, target_hash, False),
            *((kind, digest, True) for kind, digest in parent_targets),
        )
        for kind, digest, inherited in candidates:
            status = self.is_revoked(db, target_type=kind, target_hash=digest, at_time=now)
            if not status.revoked:
                continue
            if inherited and status.scope not in {
                RevocationScope.ACTOR_AND_SESSIONS,
                RevocationScope.ACTOR_AND_DEVICES,
                RevocationScope.ACTOR_AND_CHILDREN,
                RevocationScope.ACTOR_FULL_TREE,
                RevocationScope.GLOBAL,
                RevocationScope.EMERGENCY_LOCKDOWN,
            }:
                continue
            effect = "recovery_only" if status.suspended else "deny"
            if (
                status.status
                in {
                    RevocationEntryStatus.PENDING_PROPAGATION,
                    RevocationEntryStatus.PARTIALLY_PROPAGATED,
                }
                and not critical
            ):
                effect = "read_only"
            return RevocationResolution(
                True,
                status.suspended,
                status.scope,
                status.reason,
                status.revocation_epoch,
                status.revoked_at,
                kind,
                inherited,
                status.status,
                effect,
                "Access has been revoked.",
            )
        return RevocationResolution(
            False,
            False,
            None,
            None,
            None,
            None,
            None,
            False,
            "complete",
            "allow",
            "Access is active.",
        )

    @staticmethod
    def derive_private_target_hash(*, pepper: str, target_type: str, identifier: str) -> str:
        if not pepper:
            raise RevocationRegistryError("revocation_pepper_required")
        return compute_hmac_lookup_hash(pepper, f"revocation:{target_type}", identifier)

    def is_revoked(
        self, db: Session, *, target_type: str, target_hash: str, at_time: datetime | None = None
    ) -> RevocationStatus:
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
        return self._status_from_model(existing, at_time=at_time)

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
        certificates = (
            db.execute(
                select(AccessCertificate).where(
                    AccessCertificate.pass_lookup_hash == pass_lookup_hash
                )
            )
            .scalars()
            .all()
        )
        for certificate in certificates:
            self.revoke_target(
                db,
                target_type="certificate",
                target_hash=certificate.certificate_fingerprint,
                reason=reason,
                actor_hash=actor_hash,
            )
            for session in db.execute(
                select(AccessSession).where(
                    AccessSession.certificate_fingerprint == certificate.certificate_fingerprint
                )
            ).scalars():
                status = self.freeze_session(
                    db,
                    session_hash=session.session_hash,
                    reason=reason,
                    actor_hash=actor_hash,
                )
                sessions_revoked += int(status.revoked)
        for child in db.execute(
            select(ChildApiKey).where(ChildApiKey.parent_pass_lookup_hash == pass_lookup_hash)
        ).scalars():
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

    def revoke_actor_tree(
        self,
        db: Session,
        *,
        actor_type: str,
        actor_hash: str,
        reason: str,
        descendants: Mapping[str, tuple[str, ...]] | None = None,
        created_by_hash: str | None = None,
    ) -> dict[str, Any]:
        """Revoke an actor synchronously and append revocations for known descendants.

        The direct parent check is authoritative even if descendant discovery is
        incomplete. Callers pass already bounded/indexed descendant hashes; this
        method deliberately does not crawl arbitrary object graphs.
        """
        parent = self.revoke_target(
            db,
            target_type=actor_type,
            target_hash=actor_hash,
            reason=reason,
            actor_hash=created_by_hash,
            scope=RevocationScope.ACTOR_FULL_TREE,
        )
        counts: dict[str, int] = {}
        for target_type, hashes in (descendants or {}).items():
            counts[target_type] = 0
            for target_hash in dict.fromkeys(hashes):
                child = self.revoke_target(
                    db,
                    target_type=target_type,
                    target_hash=target_hash,
                    reason=reason,
                    actor_hash=created_by_hash,
                    metadata={"inherited_from_actor_hash": actor_hash},
                )
                counts[target_type] += int(child.revoked)
        self._emit_audit(
            "wallet_principal_revoked"
            if "wallet_principal" in actor_type
            else "access_actor_revoked",
            target_type=actor_type,
            target_hash=actor_hash,
            reason=reason,
            actor_hash=created_by_hash,
            revocation_epoch=parent.revocation_epoch,
            metadata={"scope": RevocationScope.ACTOR_FULL_TREE, "descendant_counts": counts},
        )
        return {
            "revoked": parent.revoked,
            "revocation_epoch": parent.revocation_epoch,
            "scope": RevocationScope.ACTOR_FULL_TREE.value,
            "descendant_counts": counts,
            "requires_reauthentication": True,
        }

    def freeze_session(
        self,
        db: Session,
        *,
        session_hash: str,
        reason: str,
        actor_hash: str | None = None,
    ) -> RevocationStatus:
        status = self.revoke_target(
            db,
            target_type="session",
            target_hash=session_hash,
            reason=reason,
            actor_hash=actor_hash,
        )
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
        status = self.revoke_target(
            db,
            target_type="child_api_key",
            target_hash=key_hash,
            reason=reason,
            actor_hash=actor_hash,
        )
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
        self._emit_named_target_event(
            "delegated_pass_revoked", status=status, actor_hash=actor_hash
        )
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
        max_epoch = db.execute(
            select(func.max(AccessRevocation.revocation_epoch))
        ).scalar_one_or_none()
        return int(max_epoch or 0) + 1

    def _get_existing(
        self, db: Session, *, target_type: str, target_hash: str
    ) -> AccessRevocation | None:
        return (
            db.execute(
                select(AccessRevocation)
                .where(
                    AccessRevocation.target_type == target_type,
                    AccessRevocation.target_hash == target_hash,
                )
                .order_by(AccessRevocation.revocation_epoch.desc(), AccessRevocation.id.desc())
            )
            .scalars()
            .first()
        )

    def _status_from_model(
        self, revocation: AccessRevocation, *, at_time: datetime | None = None
    ) -> RevocationStatus:
        metadata = revocation.metadata_json or {}
        status = str(metadata.get("status", RevocationEntryStatus.ACTIVE))
        expires_at = _parse_datetime(metadata.get("expires_at"))
        now = at_time or datetime.now(UTC)
        active = status not in {
            RevocationEntryStatus.REVERSED,
            RevocationEntryStatus.EXPIRED,
        } and not (expires_at and expires_at <= now)
        return RevocationStatus(
            revoked=active,
            target_type=revocation.target_type,
            target_hash=revocation.target_hash,
            reason=revocation.reason,
            revocation_epoch=revocation.revocation_epoch,
            revoked_at=revocation.created_at,
            decision_hint="revoked" if active else "not_revoked",
            suspended=bool(expires_at and active),
            scope=str(metadata.get("scope", RevocationScope.OBJECT_ONLY)),
            status=status if active else (RevocationEntryStatus.EXPIRED if expires_at else status),
            expires_at=expires_at,
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
            if any(
                secret in lowered
                for secret in (
                    "secret",
                    "token",
                    "raw_pass",
                    "access_pass",
                    "private_key",
                    "seed",
                    "signature",
                    "k1",
                    "linking_key",
                    "wallet_address",
                    "invoice",
                    "preimage",
                    "payer_email",
                )
            ):
                redacted[str(key)] = "[REDACTED]"
            else:
                redacted[str(key)] = value
        return redacted

    def _emit_named_target_event(
        self, event_type: str, *, status: RevocationStatus, actor_hash: str | None
    ) -> None:
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


def _iso(value: datetime | None) -> str | None:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z") if value else None


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
