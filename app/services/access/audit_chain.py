"""Tamper-evident Access Audit Chain for Proof-of-Access Auth.

Audit events are stored as sanitized canonical JSON and linked by SHA-256 hashes.
The chain never stores raw Access Passes, raw session tokens, recovery phrases,
Bitcoin seed/private-key material, passwords, JWTs, bearer tokens, or raw API
keys.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.access import AccessAuditEvent
from app.domain.access.errors import AccessAuditError
from app.services.access.crypto.hashing import canonical_json, sha256_hex

AUDIT_GENESIS = "GENESIS"
_FORBIDDEN_AUDIT_KEY_PARTS = (
    "raw_pass",
    "access_pass",
    "pass_token",
    "session_token",
    "raw_session",
    "recovery_phrase",
    "recovery_seed",
    "seed_phrase",
    "bitcoin_seed",
    "bitcoin_private_key",
    "private_key",
    "mnemonic",
    "password",
    "jwt",
    "bearer",
    "secret",
    "api_key_raw",
)


class AccessAuditEventType(StrEnum):
    PAYMENT_INTENT_CREATED = "payment_intent_created"
    PAYMENT_INTENT_EXPIRED = "payment_intent_expired"
    PAYMENT_SETTLED = "payment_settled"
    CERTIFICATE_ISSUED = "certificate_issued"
    CERTIFICATE_EXPIRED = "certificate_expired"
    CERTIFICATE_REVOKED = "certificate_revoked"
    ENTITLEMENT_ISSUED = "entitlement_issued"
    ENTITLEMENT_RENEWED = "entitlement_renewed"
    ENTITLEMENT_UPGRADED = "entitlement_upgraded"
    ENTITLEMENT_DOWNGRADED = "entitlement_downgraded"
    ENTITLEMENT_EXPIRED = "entitlement_expired"
    CHALLENGE_CREATED = "challenge_created"
    CHALLENGE_USED = "challenge_used"
    CHALLENGE_EXPIRED = "challenge_expired"
    SESSION_CREATED = "session_created"
    SESSION_REFRESHED = "session_refreshed"
    SESSION_EXPIRED = "session_expired"
    SESSION_REVOKED = "session_revoked"
    POLICY_ALLOWED = "policy_allowed"
    POLICY_DENIED = "policy_denied"
    POLICY_STEP_UP_REQUIRED = "policy_step_up_required"
    POLICY_UPGRADE_REQUIRED = "policy_upgrade_required"
    METRIC_USAGE_RECORDED = "metric_usage_recorded"
    CHILD_API_KEY_CREATED = "child_api_key_created"
    CHILD_API_KEY_ROTATED = "child_api_key_rotated"
    CHILD_API_KEY_REVOKED = "child_api_key_revoked"
    CHILD_API_KEY_FROZEN = "child_api_key_frozen"
    CHILD_KEY_SCOPE_DENIED = "child_key_scope_denied"
    CHILD_KEY_DOWNGRADE_FROZEN = "child_key_downgrade_frozen"
    DELEGATED_PASS_CREATED = "delegated_pass_created"
    DELEGATED_PASS_REVOKED = "delegated_pass_revoked"
    DELEGATED_PASS_FROZEN = "delegated_pass_frozen"
    DELEGATED_PASS_SCOPE_DENIED = "delegated_pass_scope_denied"
    DELEGATED_PASS_DOWNGRADE_FROZEN = "delegated_pass_downgrade_frozen"
    RECOVERY_SETUP_CREATED = "recovery_setup_created"
    RECOVERY_STARTED = "recovery_started"
    RECOVERY_FACTOR_SUBMITTED = "recovery_factor_submitted"
    RECOVERY_FACTOR_VERIFIED = "recovery_factor_verified"
    RECOVERY_COMPLETED = "recovery_completed"
    RECOVERY_FACTOR_FAILED = "recovery_factor_failed"
    RECOVERY_QUORUM_SATISFIED = "recovery_quorum_satisfied"
    RECOVERY_COOLDOWN_STARTED = "recovery_cooldown_started"
    RECOVERY_FAILED = "recovery_failed"
    RECOVERY_CANCELLED = "recovery_cancelled"
    RECOVERY_ROTATED = "recovery_rotated"
    RECOVERY_DENIED = "recovery_denied"
    BITCOIN_SEED_INPUT_REJECTED = "bitcoin_seed_input_rejected"
    LOCKDOWN_STARTED = "lockdown_started"
    ACCESS_LOCKDOWN_STARTED = "access_lockdown_started"
    LOCKDOWN_RECOVERY_ONLY = "lockdown_recovery_only"
    LOCKDOWN_RELEASED = "lockdown_released"
    REVOCATION_CREATED = "revocation_created"
    DEVICE_ADDED = "device_added"
    DEVICE_REVOKED = "device_revoked"
    HUMAN_INTENT_CREATED = "human_intent_created"
    HUMAN_INTENT_SIGNED = "human_intent_signed"
    HUMAN_INTENT_USED = "human_intent_used"
    HUMAN_INTENT_EXPIRED = "human_intent_expired"
    HUMAN_INTENT_REJECTED = "human_intent_rejected"
    LEGACY_AUTH_DISABLED = "legacy_auth_disabled"
    LEGACY_AUTH_ATTEMPT_BLOCKED = "legacy_auth_attempt_blocked"
    LNURL_AUTH_CHALLENGE_CREATED = "lnurl_auth_challenge_created"
    LNURL_AUTH_CHALLENGE_EXPIRED = "lnurl_auth_challenge_expired"
    LNURL_AUTH_CHALLENGE_CANCELLED = "lnurl_auth_challenge_cancelled"
    LNURL_AUTH_CHALLENGE_CONSUMED = "lnurl_auth_challenge_consumed"
    LNURL_AUTH_CHALLENGE_REJECTED = "lnurl_auth_challenge_rejected"
    LNURL_AUTH_CALLBACK_RECEIVED = "lnurl_auth_callback_received"
    LNURL_AUTH_CALLBACK_SUCCEEDED = "lnurl_auth_callback_succeeded"
    LNURL_AUTH_CALLBACK_FAILED = "lnurl_auth_callback_failed"
    LNURL_AUTH_SIGNATURE_INVALID = "lnurl_auth_signature_invalid"
    LNURL_AUTH_KEY_INVALID = "lnurl_auth_key_invalid"
    LNURL_AUTH_ACTION_INVALID = "lnurl_auth_action_invalid"
    LNURL_AUTH_DOMAIN_MISMATCH = "lnurl_auth_domain_mismatch"
    LNURL_AUTH_K1_UNKNOWN = "lnurl_auth_k1_unknown"
    LNURL_AUTH_K1_EXPIRED = "lnurl_auth_k1_expired"
    LNURL_AUTH_K1_REUSED = "lnurl_auth_k1_reused"
    LNURL_AUTH_REPLAY_REJECTED = "lnurl_auth_replay_rejected"
    LIGHTNING_PRINCIPAL_CREATED = "lightning_principal_created"
    LIGHTNING_PRINCIPAL_VERIFIED = "lightning_principal_verified"
    LIGHTNING_PRINCIPAL_LINKED = "lightning_principal_linked"
    LIGHTNING_PRINCIPAL_LINK_FAILED = "lightning_principal_link_failed"
    LIGHTNING_PRINCIPAL_SUSPENDED = "lightning_principal_suspended"
    LIGHTNING_PRINCIPAL_REVOKED = "lightning_principal_revoked"
    LNURL_DEVICE_BINDING_REQUESTED = "lnurl_device_binding_requested"
    LNURL_DEVICE_BOUND = "lnurl_device_bound"
    LNURL_DEVICE_BINDING_FAILED = "lnurl_device_binding_failed"
    LNURL_DEVICE_REVOKED = "lnurl_device_revoked"
    LNURL_AUTH_SESSION_REQUESTED = "lnurl_auth_session_requested"
    LNURL_AUTH_SESSION_CREATED = "lnurl_auth_session_created"
    LNURL_AUTH_SESSION_DENIED = "lnurl_auth_session_denied"
    LNURL_AUTH_SESSION_EXPIRED = "lnurl_auth_session_expired"
    LNURL_AUTH_SESSION_REVOKED = "lnurl_auth_session_revoked"
    LNURL_AUTH_SESSION_FROZEN = "lnurl_auth_session_frozen"
    LNURL_AUTH_STEP_UP_REQUESTED = "lnurl_auth_step_up_requested"
    LNURL_AUTH_STEP_UP_SUCCEEDED = "lnurl_auth_step_up_succeeded"
    LNURL_AUTH_STEP_UP_FAILED = "lnurl_auth_step_up_failed"
    LNURL_AUTH_STEP_UP_EXPIRED = "lnurl_auth_step_up_expired"
    LNURL_AUTH_STEP_UP_REPLAYED = "lnurl_auth_step_up_replayed"
    LNURL_AUTH_STEP_UP_POLICY_DENIED = "lnurl_auth_step_up_policy_denied"
    LNURL_AUTH_POLICY_ALLOWED = "lnurl_auth_policy_allowed"
    LNURL_AUTH_POLICY_DENIED = "lnurl_auth_policy_denied"
    LNURL_AUTH_RATE_LIMITED = "lnurl_auth_rate_limited"
    LNURL_AUTH_RISK_ESCALATED = "lnurl_auth_risk_escalated"
    LNURL_AUTH_LOCKDOWN_TRIGGERED = "lnurl_auth_lockdown_triggered"
    LNURL_AUTH_COMPATIBILITY_DOWNGRADE_DETECTED = "lnurl_auth_compatibility_downgrade_detected"
    LNURL_PAY_REQUEST_CREATED = "lnurl_pay_request_created"
    LNURL_PAY_REQUEST_DENIED = "lnurl_pay_request_denied"
    LNURL_PAY_REQUEST_FAILED = "lnurl_pay_request_failed"
    LNURL_PAY_IDEMPOTENCY_CONFLICT = "lnurl_pay_idempotency_conflict"
    LNURL_INVOICE_ISSUED = "lnurl_invoice_issued"


ACCESS_AUDIT_EVENT_TYPES: frozenset[str] = frozenset(event.value for event in AccessAuditEventType)


def sanitize_audit_metadata(metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return metadata after recursively rejecting forbidden raw-secret keys."""

    if metadata is None:
        return {}
    return _sanitize_mapping(metadata)


def build_canonical_event(
    *,
    event_type: str,
    actor_hash: str | None = None,
    object_hash: str | None = None,
    pass_lookup_hash: str | None = None,
    certificate_fingerprint: str | None = None,
    session_hash: str | None = None,
    device_key_fingerprint: str | None = None,
    workspace_id_hash: str | None = None,
    metadata: dict[str, Any] | None = None,
    occurred_at: datetime | None = None,
) -> dict[str, Any]:
    """Build deterministic, sanitized audit event material."""

    normalized_type = _validate_event_type(event_type)
    occurred = _isoformat_utc(occurred_at or datetime.now(UTC))
    return {
        "event_type": normalized_type,
        "actor_hash": actor_hash,
        "object_hash": object_hash,
        "pass_lookup_hash": pass_lookup_hash,
        "certificate_fingerprint": certificate_fingerprint,
        "session_hash": session_hash,
        "device_key_fingerprint": device_key_fingerprint,
        "workspace_id_hash": workspace_id_hash,
        "metadata": sanitize_audit_metadata(metadata),
        "occurred_at": occurred,
    }


def compute_event_hash(previous_event_hash: str | None, canonical_event: dict[str, Any]) -> str:
    """Compute SHA-256 over previous hash plus canonical event JSON."""

    previous = previous_event_hash or AUDIT_GENESIS
    return sha256_hex(previous + canonical_json(canonical_event))


class AccessAuditChain:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record_event(
        self,
        *,
        event_type: str,
        actor_hash: str | None = None,
        object_hash: str | None = None,
        pass_lookup_hash: str | None = None,
        certificate_fingerprint: str | None = None,
        session_hash: str | None = None,
        device_key_fingerprint: str | None = None,
        workspace_id_hash: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AccessAuditEvent:
        try:
            previous_hash = self.get_latest_event_hash()
            canonical_event = build_canonical_event(
                event_type=event_type,
                actor_hash=actor_hash,
                object_hash=object_hash,
                pass_lookup_hash=pass_lookup_hash,
                certificate_fingerprint=certificate_fingerprint,
                session_hash=session_hash,
                device_key_fingerprint=device_key_fingerprint,
                workspace_id_hash=workspace_id_hash,
                metadata=metadata,
            )
            event_hash = compute_event_hash(previous_hash, canonical_event)
            event = AccessAuditEvent(
                event_hash=event_hash,
                previous_event_hash=previous_hash,
                event_type=canonical_event["event_type"],
                actor_hash=actor_hash,
                object_hash=object_hash,
                canonical_event_json=canonical_event,
                created_at=datetime.now(UTC),
            )
            self.db.add(event)
            self.db.flush()
            return event
        except ValueError:
            raise
        except Exception as exc:
            raise AccessAuditError("access_audit_record_failed") from exc

    def get_latest_event_hash(self) -> str | None:
        return self.db.execute(
            select(AccessAuditEvent.event_hash).order_by(AccessAuditEvent.id.desc()).limit(1)
        ).scalar_one_or_none()

    def verify_chain(self, limit: int | None = None) -> dict[str, Any]:
        statement = select(AccessAuditEvent).order_by(AccessAuditEvent.id.asc())
        if limit is not None:
            statement = statement.limit(limit)
        previous: str | None = None
        checked = 0
        for event in self.db.execute(statement).scalars():
            checked += 1
            expected = compute_event_hash(previous, dict(event.canonical_event_json))
            if event.previous_event_hash != previous or event.event_hash != expected:
                return {
                    "valid": False,
                    "checked_events": checked,
                    "first_broken_event_id": event.id,
                    "expected_hash": expected,
                    "actual_hash": event.event_hash,
                }
            previous = event.event_hash
        return {
            "valid": True,
            "checked_events": checked,
            "first_broken_event_id": None,
            "expected_hash": None,
            "actual_hash": None,
        }

    def record_payment_settled(self, **kwargs: Any) -> AccessAuditEvent:
        return self.record_event(event_type=AccessAuditEventType.PAYMENT_SETTLED.value, **kwargs)

    def record_certificate_issued(self, **kwargs: Any) -> AccessAuditEvent:
        return self.record_event(event_type=AccessAuditEventType.CERTIFICATE_ISSUED.value, **kwargs)

    def record_entitlement_issued(self, **kwargs: Any) -> AccessAuditEvent:
        return self.record_event(event_type=AccessAuditEventType.ENTITLEMENT_ISSUED.value, **kwargs)

    def record_challenge_created(self, **kwargs: Any) -> AccessAuditEvent:
        return self.record_event(event_type=AccessAuditEventType.CHALLENGE_CREATED.value, **kwargs)

    def record_session_created(self, **kwargs: Any) -> AccessAuditEvent:
        return self.record_event(event_type=AccessAuditEventType.SESSION_CREATED.value, **kwargs)

    def record_policy_decision(self, *, allowed: bool, **kwargs: Any) -> AccessAuditEvent:
        event_type = AccessAuditEventType.POLICY_ALLOWED.value if allowed else AccessAuditEventType.POLICY_DENIED.value
        return self.record_event(event_type=event_type, **kwargs)

    def record_revocation_created(self, **kwargs: Any) -> AccessAuditEvent:
        return self.record_event(event_type=AccessAuditEventType.REVOCATION_CREATED.value, **kwargs)

    def record_lockdown_started(self, **kwargs: Any) -> AccessAuditEvent:
        return self.record_event(event_type=AccessAuditEventType.LOCKDOWN_STARTED.value, **kwargs)

    def record_recovery_started(self, **kwargs: Any) -> AccessAuditEvent:
        return self.record_event(event_type=AccessAuditEventType.RECOVERY_STARTED.value, **kwargs)

    def record_legacy_auth_disabled(self, **kwargs: Any) -> AccessAuditEvent:
        return self.record_event(event_type=AccessAuditEventType.LEGACY_AUTH_DISABLED.value, **kwargs)


def _validate_event_type(event_type: str) -> str:
    normalized = event_type.strip().lower()
    if normalized not in ACCESS_AUDIT_EVENT_TYPES:
        raise AccessAuditError("invalid_access_audit_event_type")
    return normalized


def _sanitize_mapping(metadata: Mapping[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in metadata.items():
        lowered = str(key).lower()
        if any(forbidden in lowered for forbidden in _FORBIDDEN_AUDIT_KEY_PARTS):
            raise ValueError("forbidden_audit_secret_key")
        sanitized[str(key)] = _sanitize_value(value)
    return sanitized


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _sanitize_mapping(value)
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, datetime):
        return _isoformat_utc(value)
    return value


def _isoformat_utc(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
