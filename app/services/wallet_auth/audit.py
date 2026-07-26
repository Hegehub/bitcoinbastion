"""Wallet-domain builders for the canonical Access security Audit Chain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.db.models.access import AccessAuditEvent
from app.services.access.audit_chain import AccessAuditChain, AuditRetentionClass, AuditSeverity


@dataclass(frozen=True, slots=True)
class WalletAuditEvent:
    event_type: str
    event_status: str
    principal_hash: str | None = None
    subject_hash: str | None = None
    device_fingerprint: str | None = None
    session_hash: str | None = None
    reason_code: str = "verified"
    action: str | None = None
    proof_type: str | None = None
    verification_strength: str | None = None
    policy_hash: str | None = None
    policy_epoch: int | None = None
    idempotency_key_hash: str | None = None


class WalletAuditWriter:
    """Projection adapter; all durable linking remains in ``AccessAuditChain``."""

    def __init__(self, chain: AccessAuditChain) -> None:
        self.chain = chain

    def record(
        self, event: WalletAuditEvent, *, safe_metadata: dict[str, Any] | None = None
    ) -> AccessAuditEvent:
        details = {
            "reason_code": event.reason_code,
            "action": event.action,
            "proof_type": event.proof_type,
            "verification_strength": event.verification_strength,
            "policy_hash": event.policy_hash,
            "policy_epoch": event.policy_epoch,
            **(safe_metadata or {}),
        }
        return self.chain.record_event(
            event_type=event.event_type,
            actor_hash=event.principal_hash,
            object_hash=event.subject_hash,
            device_key_fingerprint=event.device_fingerprint,
            session_hash=event.session_hash,
            metadata=details,
            event_category="authentication",
            event_status=event.event_status,
            severity=AuditSeverity.HIGH if event.event_status == "failure" else AuditSeverity.INFO,
            retention_class=AuditRetentionClass.SECURITY,
            idempotency_key_hash=event.idempotency_key_hash,
        )
