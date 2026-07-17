"""LNURL-auth audit adapter for the Bastion tamper-evident Audit Chain.

This module deliberately publishes LNURL-auth security transitions into the
existing :mod:`app.services.access.audit_chain` component.  It does not create a
second LNURL-specific ledger: production callers should pass the existing
``AccessAuditChain`` instance, while tests may use the in-memory chain adapter in
this file to validate canonicalization, redaction, idempotency, and hash-linking
without a database.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol

from app.domain.access.errors import AccessAuditError
from app.services.access.audit_chain import AUDIT_GENESIS
from app.services.access.crypto.hashing import canonical_json, sha256_prefixed


class LNURLAuthAuditEventType(StrEnum):
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


class AuditOutcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    DENIED = "denied"
    EXPIRED = "expired"
    REVOKED = "revoked"
    REPLAY_REJECTED = "replay_rejected"
    RATE_LIMITED = "rate_limited"
    STEP_UP_REQUIRED = "step_up_required"
    DEGRADED = "degraded"
    PENDING = "pending"


class AuditSeverity(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"


LNURL_AUTH_AUDIT_EVENT_TYPES: frozenset[str] = frozenset(event.value for event in LNURLAuthAuditEventType)
LNURL_AUDIT_REASON_CODES: frozenset[str] = frozenset(
    {
        "challenge_not_found",
        "challenge_expired",
        "challenge_already_used",
        "k1_unknown",
        "k1_expired",
        "k1_reused",
        "signature_invalid",
        "linking_key_invalid",
        "unsupported_action",
        "domain_mismatch",
        "origin_mismatch",
        "principal_revoked",
        "principal_suspended",
        "device_not_bound",
        "device_revoked",
        "entitlement_inactive",
        "subscription_expired",
        "policy_denied",
        "step_up_required",
        "risk_too_high",
        "verification_strength_insufficient",
        "legacy_method_not_allowed",
        "rate_limit_exceeded",
        "internal_verification_error",
    }
)

_FORBIDDEN_KEY_PARTS = (
    "raw_k1",
    "raw_nonce",
    "raw_signature",
    "raw_sig",
    "raw_key",
    "linking_key",
    "private_key",
    "wallet_seed",
    "bitcoin_seed",
    "seed_phrase",
    "mnemonic",
    "xprv",
    "session_token",
    "access_pass",
    "bearer_token",
    "invoice_preimage",
    "recovery_phrase",
    "recovery_secret",
    "raw_session",
)
_FORBIDDEN_EXACT_KEYS = {"k1", "nonce", "sig", "signature", "seed", "preimage", "secret"}
_SAFE_HASH_KEYS = {
    "k1_hash",
    "challenge_hash",
    "signature_hash",
    "linking_key_hash",
    "lnurl_key_hash",
    "principal_hash",
    "session_hash",
    "device_key_fingerprint",
    "auth_domain_hash",
    "policy_hash",
    "proof_fingerprint",
    "callback_fingerprint",
    "resource_hash",
    "intent_hash",
}

_ALIAS_EVENT_TYPES = {
    "lnurl_auth_callback_success": LNURLAuthAuditEventType.LNURL_AUTH_CALLBACK_SUCCEEDED.value,
    "lnurl_auth_callback_failed": LNURLAuthAuditEventType.LNURL_AUTH_CALLBACK_FAILED.value,
    "lnurl_auth_challenge_cancelled": LNURLAuthAuditEventType.LNURL_AUTH_CHALLENGE_CANCELLED.value,
    "lnurl_auth_challenge_expired": LNURLAuthAuditEventType.LNURL_AUTH_CHALLENGE_EXPIRED.value,
    "lnurl_session_bridge_started": LNURLAuthAuditEventType.LNURL_AUTH_SESSION_REQUESTED.value,
    "lnurl_session_policy_allowed": LNURLAuthAuditEventType.LNURL_AUTH_POLICY_ALLOWED.value,
    "lnurl_session_policy_denied": LNURLAuthAuditEventType.LNURL_AUTH_SESSION_DENIED.value,
    "lnurl_session_created": LNURLAuthAuditEventType.LNURL_AUTH_SESSION_CREATED.value,
    "lnurl_step_up_created": LNURLAuthAuditEventType.LNURL_AUTH_STEP_UP_SUCCEEDED.value,
    "lnurl_principal_linked": LNURLAuthAuditEventType.LIGHTNING_PRINCIPAL_LINKED.value,
    "lnurl_step_up_requested": LNURLAuthAuditEventType.LNURL_AUTH_STEP_UP_REQUESTED.value,
    "lnurl_step_up_challenge_created": LNURLAuthAuditEventType.LNURL_AUTH_CHALLENGE_CREATED.value,
    "lnurl_step_up_proof_verified": LNURLAuthAuditEventType.LNURL_AUTH_STEP_UP_SUCCEEDED.value,
    "lnurl_step_up_proof_failed": LNURLAuthAuditEventType.LNURL_AUTH_STEP_UP_FAILED.value,
    "lnurl_step_up_policy_allowed": LNURLAuthAuditEventType.LNURL_AUTH_POLICY_ALLOWED.value,
    "lnurl_step_up_policy_denied": LNURLAuthAuditEventType.LNURL_AUTH_STEP_UP_POLICY_DENIED.value,
    "lnurl_step_up_approved": LNURLAuthAuditEventType.LNURL_AUTH_STEP_UP_SUCCEEDED.value,
    "lnurl_step_up_expired": LNURLAuthAuditEventType.LNURL_AUTH_STEP_UP_EXPIRED.value,
    "lnurl_step_up_replay_rejected": LNURLAuthAuditEventType.LNURL_AUTH_STEP_UP_REPLAYED.value,
}


@dataclass(frozen=True)
class AuditEventReference:
    event_id: str
    event_type: str
    event_hash: str
    previous_event_hash: str | None
    sequence: int
    occurred_at: datetime
    idempotency_key: str


@dataclass(frozen=True)
class InMemoryAuditEvent:
    reference: AuditEventReference
    canonical_event: dict[str, Any]


class AuditChainProtocol(Protocol):
    def record_event(
        self,
        *,
        event_type: str,
        actor_hash: str | None = None,
        object_hash: str | None = None,
        session_hash: str | None = None,
        device_key_fingerprint: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Any: ...


class InMemoryLNURLAuditChain:
    """Test adapter with the same hash-linking invariant as AccessAuditChain."""

    def __init__(self) -> None:
        self.events: list[InMemoryAuditEvent] = []

    def append(self, canonical_event: dict[str, Any], *, idempotency_key: str) -> AuditEventReference:
        previous_hash = self.events[-1].reference.event_hash if self.events else None
        event_hash = compute_lnurl_audit_hash(previous_hash, canonical_event)
        sequence = len(self.events) + 1
        reference = AuditEventReference(
            event_id=f"lnurl-audit-{sequence}",
            event_type=str(canonical_event["event_type"]),
            event_hash=event_hash,
            previous_event_hash=previous_hash,
            sequence=sequence,
            occurred_at=_parse_utc(str(canonical_event["occurred_at"])),
            idempotency_key=idempotency_key,
        )
        self.events.append(InMemoryAuditEvent(reference=reference, canonical_event=canonical_event))
        return reference

    def verify_chain(self, events: Sequence[InMemoryAuditEvent] | None = None) -> dict[str, Any]:
        sequence = list(events if events is not None else self.events)
        previous: str | None = None
        for index, event in enumerate(sequence, start=1):
            expected = compute_lnurl_audit_hash(previous, event.canonical_event)
            if event.reference.previous_event_hash != previous or event.reference.event_hash != expected:
                return {
                    "valid": False,
                    "checked_events": index,
                    "first_broken_event_id": event.reference.event_id,
                    "expected_hash": expected,
                    "actual_hash": event.reference.event_hash,
                }
            previous = event.reference.event_hash
        return {
            "valid": True,
            "checked_events": len(sequence),
            "first_broken_event_id": None,
            "expected_hash": None,
            "actual_hash": None,
        }


class LNURLAuditService:
    """Privacy-preserving adapter into Bastion's existing Access Audit Chain."""

    def __init__(
        self,
        audit_chain: AuditChainProtocol | None = None,
        *,
        memory_chain: InMemoryLNURLAuditChain | None = None,
        fail_closed: bool = True,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.audit_chain = audit_chain
        self.memory_chain = memory_chain or (InMemoryLNURLAuditChain() if audit_chain is None else None)
        self.fail_closed = fail_closed
        self.clock = clock or (lambda: datetime.now(UTC))
        self._idempotency: dict[str, AuditEventReference] = {}

    def record_lnurl_auth_event(
        self,
        *,
        event_type: LNURLAuthAuditEventType | str,
        outcome: AuditOutcome | str,
        principal_hash: str | None = None,
        challenge_hash: str | None = None,
        device_key_fingerprint: str | None = None,
        session_hash: str | None = None,
        action: str | None = None,
        auth_domain_hash: str | None = None,
        verification_strength: str | None = None,
        policy_hash: str | None = None,
        policy_epoch: int | None = None,
        crypto_epoch: int | None = None,
        request_correlation_id: str | None = None,
        reason_code: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        severity: AuditSeverity | str | None = None,
        bastion_action: str | None = None,
        policy_decision: str | None = None,
        revocation: Mapping[str, Any] | None = None,
        occurred_at: datetime | None = None,
        idempotency_key: str | None = None,
    ) -> AuditEventReference:
        normalized_type = normalize_lnurl_audit_event_type(event_type)
        normalized_outcome = _normalize_enum(AuditOutcome, outcome, "invalid_lnurl_audit_outcome")
        safe_metadata = sanitize_lnurl_audit_metadata(metadata)
        safe_revocation = sanitize_lnurl_audit_metadata(revocation)
        safe_reason = _validate_reason_code(reason_code)
        occurred = _isoformat_utc(occurred_at or self.clock())
        event_severity = str(severity or _severity_for_event(normalized_type, normalized_outcome))
        canonical_event = build_lnurl_canonical_audit_event(
            event_type=normalized_type,
            outcome=normalized_outcome,
            severity=event_severity,
            principal_hash=principal_hash,
            challenge_hash=_safe_identifier(challenge_hash),
            device_key_fingerprint=_safe_identifier(device_key_fingerprint),
            session_hash=_safe_identifier(session_hash),
            action=action,
            bastion_action=bastion_action,
            auth_domain_hash=_safe_identifier(auth_domain_hash),
            verification_strength=verification_strength,
            policy_hash=_safe_identifier(policy_hash),
            policy_epoch=policy_epoch,
            policy_decision=policy_decision,
            crypto_epoch=crypto_epoch,
            request_correlation_id=request_correlation_id,
            reason_code=safe_reason,
            revocation=safe_revocation,
            metadata=safe_metadata,
            occurred_at=occurred,
        )
        idem = idempotency_key or _default_idempotency_key(canonical_event)
        if idem in self._idempotency:
            return self._idempotency[idem]
        try:
            reference = self._persist(canonical_event, idempotency_key=idem)
        except Exception as exc:
            if self.fail_closed:
                raise AccessAuditError("lnurl_audit_record_failed") from exc
            reference = _failed_reference(normalized_type, idem, self.clock())
        self._idempotency[idem] = reference
        return reference

    def as_event_emitter(self) -> Callable[[str, Mapping[str, Any]], AuditEventReference]:
        """Return a callable compatible with existing LNURL service audit hooks."""

        def emit(event: str, payload: Mapping[str, Any]) -> AuditEventReference:
            normalized = normalize_lnurl_audit_event_type(event)
            return self.record_lnurl_auth_event(
                event_type=normalized,
                outcome=_infer_outcome(normalized, payload),
                principal_hash=_first_str(payload, "principal_hash"),
                challenge_hash=_first_str(payload, "challenge_hash", "k1_hash", "challenge_id_hash", "challenge_id"),
                device_key_fingerprint=_first_str(payload, "device_key_fingerprint"),
                session_hash=_first_str(payload, "session_hash", "session_fingerprint"),
                action=_first_str(payload, "action", "lnurl_action"),
                auth_domain_hash=_first_str(payload, "auth_domain_hash", "auth_domain"),
                verification_strength=_first_str(payload, "verification_strength"),
                policy_hash=_first_str(payload, "policy_hash", "policy_intent_hash"),
                policy_epoch=_first_int(payload, "policy_epoch"),
                crypto_epoch=_first_int(payload, "crypto_epoch"),
                reason_code=_first_str(payload, "reason_code"),
                metadata=payload,
            )

        return emit

    def _persist(self, canonical_event: dict[str, Any], *, idempotency_key: str) -> AuditEventReference:
        if self.audit_chain is not None:
            event = self.audit_chain.record_event(
                event_type=str(canonical_event["event_type"]),
                actor_hash=_optional_nested(canonical_event, "actor", "principal_hash"),
                object_hash=_optional_nested(canonical_event, "object", "object_hash"),
                session_hash=_optional_nested(canonical_event, "session", "session_hash"),
                device_key_fingerprint=_optional_nested(canonical_event, "device", "device_key_fingerprint"),
                metadata=canonical_event,
            )
            event_id = str(getattr(event, "id", idempotency_key))
            sequence = int(getattr(event, "id", 0) or 0)
            occurred = getattr(event, "created_at", self.clock())
            return AuditEventReference(
                event_id=event_id,
                event_type=str(canonical_event["event_type"]),
                event_hash=str(getattr(event, "event_hash")),
                previous_event_hash=getattr(event, "previous_event_hash", None),
                sequence=sequence,
                occurred_at=occurred,
                idempotency_key=idempotency_key,
            )
        assert self.memory_chain is not None
        return self.memory_chain.append(canonical_event, idempotency_key=idempotency_key)


def build_lnurl_canonical_audit_event(
    *,
    event_type: str,
    outcome: str,
    severity: str,
    principal_hash: str | None,
    challenge_hash: str | None,
    device_key_fingerprint: str | None,
    session_hash: str | None,
    action: str | None,
    bastion_action: str | None,
    auth_domain_hash: str | None,
    verification_strength: str | None,
    policy_hash: str | None,
    policy_epoch: int | None,
    policy_decision: str | None,
    crypto_epoch: int | None,
    request_correlation_id: str | None,
    reason_code: str | None,
    revocation: Mapping[str, Any] | None,
    metadata: Mapping[str, Any] | None,
    occurred_at: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "type": "bastion_audit_event",
        "version": 1,
        "event_type": normalize_lnurl_audit_event_type(event_type),
        "event_family": "lnurl_auth",
        "outcome": outcome,
        "severity": severity,
        "actor": _compact({"actor_type": "lightning_wallet_principal", "principal_hash": principal_hash}),
        "object": _compact({"object_type": "lnurl_auth_challenge", "object_hash": challenge_hash}),
        "auth": _compact(
            {
                "method": "lnurl_auth",
                "action": action,
                "bastion_action": bastion_action,
                "verification_strength": verification_strength,
                "auth_domain_hash": auth_domain_hash,
            }
        ),
        "device": _compact({"device_key_fingerprint": device_key_fingerprint}),
        "session": _compact({"session_hash": session_hash}),
        "policy": _compact({"policy_hash": policy_hash, "policy_epoch": policy_epoch, "decision": policy_decision}),
        "crypto": _compact({"crypto_epoch": crypto_epoch, "hash_suite": "sha256"}),
        "revocation": dict(revocation or {}),
        "reason_code": reason_code,
        "request_correlation_id": request_correlation_id,
        "metadata": dict(metadata or {}),
        "occurred_at": occurred_at,
    }
    return sanitize_lnurl_audit_metadata(payload)


def compute_lnurl_audit_hash(previous_event_hash: str | None, canonical_event: Mapping[str, Any]) -> str:
    previous = previous_event_hash or AUDIT_GENESIS
    return sha256_prefixed(previous + canonical_json(canonical_event))


def normalize_lnurl_audit_event_type(event_type: LNURLAuthAuditEventType | str) -> str:
    raw = str(event_type.value if isinstance(event_type, LNURLAuthAuditEventType) else event_type)
    normalized = _ALIAS_EVENT_TYPES.get(raw.strip().lower(), raw.strip().lower())
    if normalized not in LNURL_AUTH_AUDIT_EVENT_TYPES:
        raise AccessAuditError("invalid_lnurl_audit_event_type")
    return normalized


def sanitize_lnurl_audit_metadata(metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    if metadata is None:
        return {}
    return _sanitize_mapping(metadata)


def _sanitize_mapping(metadata: Mapping[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in metadata.items():
        key_str = str(key)
        lowered = key_str.lower()
        if lowered not in _SAFE_HASH_KEYS and (
            lowered in _FORBIDDEN_EXACT_KEYS or any(part in lowered for part in _FORBIDDEN_KEY_PARTS)
        ):
            raise ValueError("forbidden_lnurl_audit_secret_key")
        sanitized[key_str] = _sanitize_value(value, lowered)
    return sanitized


def _sanitize_value(value: Any, key_name: str | None = None) -> Any:
    if isinstance(value, str) and key_name not in _SAFE_HASH_KEYS and _looks_like_unlabeled_secret(value):
        raise ValueError("forbidden_lnurl_audit_secret_value")
    if isinstance(value, Mapping):
        return _sanitize_mapping(value)
    if isinstance(value, list | tuple):
        return [_sanitize_value(item, key_name) for item in value]
    if isinstance(value, datetime):
        return _isoformat_utc(value)
    return value


def _safe_identifier(value: str | None) -> str | None:
    if value is None:
        return None
    if value.startswith(("sha256:", "hmac-sha256:")):
        return value
    return sha256_prefixed(value)


def _looks_like_unlabeled_secret(value: str) -> bool:
    stripped = value.strip().lower()
    if len(stripped) == 64 and all(char in "0123456789abcdef" for char in stripped):
        return True
    if len(stripped) > 120 and stripped.startswith("30") and all(char in "0123456789abcdef" for char in stripped):
        return True
    return False


def _validate_reason_code(reason_code: str | None) -> str | None:
    if reason_code is None:
        return None
    normalized = reason_code.strip().lower()
    if not normalized:
        return None
    if normalized not in LNURL_AUDIT_REASON_CODES and not normalized.startswith("lnurl_"):
        raise AccessAuditError("invalid_lnurl_audit_reason_code")
    return normalized


def _normalize_enum(enum_type: type[StrEnum], value: StrEnum | str, error_code: str) -> str:
    normalized = str(value.value if isinstance(value, enum_type) else value).strip().lower()
    if normalized not in {item.value for item in enum_type}:
        raise AccessAuditError(error_code)
    return normalized


def _severity_for_event(event_type: str, outcome: str) -> AuditSeverity:
    if event_type in {
        LNURLAuthAuditEventType.LNURL_AUTH_REPLAY_REJECTED.value,
        LNURLAuthAuditEventType.LNURL_AUTH_K1_REUSED.value,
        LNURLAuthAuditEventType.LNURL_AUTH_DOMAIN_MISMATCH.value,
        LNURLAuthAuditEventType.LNURL_AUTH_COMPATIBILITY_DOWNGRADE_DETECTED.value,
        LNURLAuthAuditEventType.LIGHTNING_PRINCIPAL_REVOKED.value,
    }:
        return AuditSeverity.HIGH
    if event_type in {LNURLAuthAuditEventType.LNURL_AUTH_LOCKDOWN_TRIGGERED.value}:
        return AuditSeverity.CRITICAL
    if outcome in {AuditOutcome.FAILURE.value, AuditOutcome.DENIED.value, AuditOutcome.RATE_LIMITED.value}:
        return AuditSeverity.WARNING
    return AuditSeverity.INFO


def _infer_outcome(event_type: str, payload: Mapping[str, Any]) -> AuditOutcome:
    if (result := _first_str(payload, "outcome", "result")):
        try:
            return AuditOutcome(result)
        except ValueError:
            pass
    if any(token in event_type for token in ("succeeded", "created", "verified", "bound", "allowed", "consumed", "linked")):
        return AuditOutcome.SUCCESS
    if "expired" in event_type:
        return AuditOutcome.EXPIRED
    if "revoked" in event_type:
        return AuditOutcome.REVOKED
    if "replay" in event_type or "reused" in event_type:
        return AuditOutcome.REPLAY_REJECTED
    if "rate_limited" in event_type:
        return AuditOutcome.RATE_LIMITED
    if "denied" in event_type:
        return AuditOutcome.DENIED
    if "requested" in event_type:
        return AuditOutcome.PENDING
    return AuditOutcome.FAILURE


def _default_idempotency_key(canonical_event: Mapping[str, Any]) -> str:
    material = {
        "event_type": canonical_event.get("event_type"),
        "outcome": canonical_event.get("outcome"),
        "actor": canonical_event.get("actor"),
        "object": canonical_event.get("object"),
        "session": canonical_event.get("session"),
        "policy_epoch": (canonical_event.get("policy") or {}).get("policy_epoch"),
        "reason_code": canonical_event.get("reason_code"),
    }
    return sha256_prefixed(canonical_json(material))


def _compact(value: Mapping[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if item is not None}


def _first_str(payload: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _first_int(payload: Mapping[str, Any], key: str) -> int | None:
    value = payload.get(key)
    return value if isinstance(value, int) else None


def _optional_nested(payload: Mapping[str, Any], section: str, key: str) -> str | None:
    section_value = payload.get(section)
    if isinstance(section_value, Mapping):
        value = section_value.get(key)
        return value if isinstance(value, str) else None
    return None


def _failed_reference(event_type: str, idempotency_key: str, occurred_at: datetime) -> AuditEventReference:
    return AuditEventReference(
        event_id="lnurl-audit-unpersisted",
        event_type=event_type,
        event_hash="",
        previous_event_hash=None,
        sequence=0,
        occurred_at=occurred_at,
        idempotency_key=idempotency_key,
    )


def _isoformat_utc(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


__all__ = [
    "AuditEventReference",
    "AuditOutcome",
    "AuditSeverity",
    "InMemoryLNURLAuditChain",
    "LNURLAuditService",
    "LNURLAuthAuditEventType",
    "LNURL_AUTH_AUDIT_EVENT_TYPES",
    "LNURL_AUDIT_REASON_CODES",
    "build_lnurl_canonical_audit_event",
    "compute_lnurl_audit_hash",
    "normalize_lnurl_audit_event_type",
    "sanitize_lnurl_audit_metadata",
]
