"""Tamper-evident Access Audit Chain for Proof-of-Access Auth.

Audit events are stored as sanitized canonical JSON and linked by SHA-256 hashes.
The chain never stores raw Access Passes, raw session tokens, recovery phrases,
Bitcoin seed/private-key material, passwords, JWTs, bearer tokens, or raw API
keys.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from hmac import compare_digest
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
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
    "raw_k1",
    "linking_key",
    "wallet_address",
    "raw_signature",
    "der_signature",
    "bolt11",
    "invoice",
    "preimage",
    "payerdata",
    "payer_data",
    "email",
    "comment",
    "xprv",
    "tprv",
    "wif",
    "server_pepper",
    "issuer_private",
)
_SAFE_AUDIT_KEY_SUFFIXES = ("_hash", "_fingerprint", "_commitment")
_SAFE_AUDIT_EXACT_KEYS = {"comment_allowed", "payer_data_present", "payer_data_auth_verified"}

CANONICAL_CHAIN_ID = "access-security"
AUDIT_EVENT_VERSION = 1
AUDIT_APPEND_MAX_RETRIES = 3


class AuditSeverity(StrEnum):
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"


class AuditRetentionClass(StrEnum):
    TRANSIENT = "transient"
    OPERATIONAL = "operational"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    LEGAL_HOLD = "legal_hold"


class AccessAuditEventType(StrEnum):
    PAYMENT_INTENT_CREATED = "payment_intent_created"
    PAYMENT_INTENT_EXPIRED = "payment_intent_expired"
    PAYMENT_SETTLED = "payment_settled"
    CERTIFICATE_ISSUED = "certificate_issued"
    CERTIFICATE_EXPIRED = "certificate_expired"
    CERTIFICATE_REVOKED = "certificate_revoked"
    PRINCIPAL_CERTIFICATE_REQUESTED = "principal_certificate_requested"
    PRINCIPAL_CERTIFICATE_POLICY_ALLOWED = "principal_certificate_policy_allowed"
    PRINCIPAL_CERTIFICATE_POLICY_DENIED = "principal_certificate_policy_denied"
    PRINCIPAL_CERTIFICATE_STEP_UP_REQUIRED = "principal_certificate_step_up_required"
    PRINCIPAL_CERTIFICATE_QUORUM_REQUIRED = "principal_certificate_quorum_required"
    PRINCIPAL_CERTIFICATE_ISSUED = "principal_certificate_issued"
    PRINCIPAL_CERTIFICATE_EXPORTED = "principal_certificate_exported"
    PRINCIPAL_CERTIFICATE_ROTATED = "principal_certificate_rotated"
    PRINCIPAL_CERTIFICATE_FROZEN = "principal_certificate_frozen"
    PRINCIPAL_CERTIFICATE_REVOKED = "principal_certificate_revoked"
    CERTIFICATE_PRINCIPAL_UNLINKED = "certificate_principal_unlinked"
    CERTIFICATE_DEVICE_REBOUND = "certificate_device_rebound"
    CERTIFICATE_ENTITLEMENT_NARROWED = "certificate_entitlement_narrowed"
    CERTIFICATE_CRYPTO_EPOCH_MIGRATED = "certificate_crypto_epoch_migrated"
    OFFLINE_PACK_REQUESTED = "offline_pack_requested"
    OFFLINE_PACK_POLICY_ALLOWED = "offline_pack_policy_allowed"
    OFFLINE_PACK_POLICY_DENIED = "offline_pack_policy_denied"
    OFFLINE_PACK_ISSUED = "offline_pack_issued"
    OFFLINE_PACK_EXPORTED = "offline_pack_exported"
    OFFLINE_PACK_VERIFIED = "offline_pack_verified"
    OFFLINE_PACK_VERIFICATION_FAILED = "offline_pack_verification_failed"
    OFFLINE_OPERATION_QUEUED = "offline_operation_queued"
    OFFLINE_PACK_RECONCILIATION_STARTED = "offline_pack_reconciliation_started"
    OFFLINE_PACK_RECONCILED = "offline_pack_reconciled"
    OFFLINE_PACK_RECONCILIATION_FAILED = "offline_pack_reconciliation_failed"
    OFFLINE_PACK_EXPIRED = "offline_pack_expired"
    OFFLINE_PACK_REVOKED = "offline_pack_revoked"
    OFFLINE_CLOCK_ROLLBACK_DETECTED = "offline_clock_rollback_detected"
    OFFLINE_EVENT_CHAIN_INVALID = "offline_event_chain_invalid"
    ISSUER_OBJECT_SIGNED = "issuer_object_signed"
    ISSUER_OBJECT_SIGNATURE_FAILED = "issuer_object_signature_failed"
    ISSUER_OBJECT_VERIFIED = "issuer_object_verified"
    ISSUER_OBJECT_VERIFICATION_FAILED = "issuer_object_verification_failed"
    ISSUER_KEY_ACTIVATED = "issuer_key_activated"
    ISSUER_KEY_RETIRED = "issuer_key_retired"
    ISSUER_KEY_REVOKED = "issuer_key_revoked"
    ISSUER_KEY_COMPROMISED = "issuer_key_compromised"
    CRYPTO_EPOCH_ACTIVATED = "crypto_epoch_activated"
    CRYPTO_EPOCH_DEPRECATED = "crypto_epoch_deprecated"
    CRYPTO_POLICY_UNSATISFIED = "crypto_policy_unsatisfied"
    OBJECT_MARKED_FOR_REISSUE = "object_marked_for_reissue"
    OBJECT_REISSUED = "object_reissued"
    PQ_PROVIDER_UNAVAILABLE = "pq_provider_unavailable"
    PQ_SIGNATURE_CREATED = "pq_signature_created"
    PQ_SIGNATURE_VERIFICATION_FAILED = "pq_signature_verification_failed"
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
    LNURL_RECOVERY_FACTOR_REQUESTED = "lnurl_recovery_factor_requested"
    LNURL_RECOVERY_CHALLENGE_CREATED = "lnurl_recovery_challenge_created"
    LNURL_RECOVERY_CALLBACK_RECEIVED = "lnurl_recovery_callback_received"
    LNURL_RECOVERY_FACTOR_VERIFIED = "lnurl_recovery_factor_verified"
    LNURL_RECOVERY_FACTOR_REJECTED = "lnurl_recovery_factor_rejected"
    LNURL_RECOVERY_K1_EXPIRED = "lnurl_recovery_k1_expired"
    LNURL_RECOVERY_K1_REUSED = "lnurl_recovery_k1_reused"
    LNURL_RECOVERY_PRINCIPAL_MISMATCH = "lnurl_recovery_principal_mismatch"
    LNURL_RECOVERY_FACTOR_REVOKED = "lnurl_recovery_factor_revoked"
    LNURL_RECOVERY_ADDITIONAL_FACTOR_REQUIRED = "lnurl_recovery_additional_factor_required"
    QUORUM_CREATED = "quorum_created"
    QUORUM_APPROVAL_RECORDED = "quorum_approval_recorded"
    QUORUM_APPROVAL_REJECTED = "quorum_approval_rejected"
    QUORUM_SATISFIED = "quorum_satisfied"
    QUORUM_POLICY_DENIED = "quorum_policy_denied"
    QUORUM_CONSUMED = "quorum_consumed"
    QUORUM_EXPIRED = "quorum_expired"
    QUORUM_REVOKED = "quorum_revoked"
    QUORUM_DUPLICATE_PARTICIPANT_REJECTED = "quorum_duplicate_participant_rejected"
    RECOVERY_QUORUM_BOUND = "recovery_quorum_bound"
    LNURL_PAY_REQUEST_CREATED = "lnurl_pay_request_created"
    LNURL_PAY_REQUEST_DENIED = "lnurl_pay_request_denied"
    LNURL_PAY_REQUEST_FAILED = "lnurl_pay_request_failed"
    LNURL_PAY_IDEMPOTENCY_CONFLICT = "lnurl_pay_idempotency_conflict"
    LNURL_INVOICE_ISSUED = "lnurl_invoice_issued"


ACCESS_AUDIT_EVENT_TYPES: frozenset[str] = frozenset(event.value for event in AccessAuditEventType)

# Domain adapters validate semantics, while this canonical writer owns linking,
# persistence and verification. These stable values intentionally live here so
# projections (LNURL, wallet, PayRegister and SIEM) cannot form competing ledgers.
WALLET_LNURL_AUDIT_EVENT_TYPES: frozenset[str] = frozenset(
    """wallet_challenge_created wallet_challenge_expired wallet_challenge_reused
    wallet_proof_verification_started wallet_proof_verification_success wallet_proof_verification_failed
    wallet_proof_network_mismatch wallet_proof_origin_mismatch wallet_proof_too_weak
    wallet_legacy_signature_used wallet_legacy_signature_rejected wallet_principal_created
    wallet_principal_verified wallet_principal_suspended wallet_principal_reactivated wallet_principal_revoked
    wallet_principal_recovery_locked wallet_registration_success wallet_registration_failed wallet_login_success
    wallet_login_failed wallet_device_binding_started wallet_device_bound wallet_device_binding_failed
    wallet_device_suspended wallet_device_revoked wallet_new_device_step_up_required wallet_session_created
    wallet_session_creation_failed wallet_session_expired wallet_session_frozen wallet_session_revoked
    wallet_session_replay_rejected wallet_request_signature_failed wallet_request_signature_verified
    wallet_step_up_required wallet_step_up_started wallet_step_up_success wallet_step_up_failed
    wallet_step_up_expired wallet_step_up_replayed lnurl_auth_qr_issued lnurl_auth_callback_success
    lnurl_auth_k1_unexpected lnurl_auth_domain_mismatch lnurl_auth_action_mismatch lnurl_auth_principal_created
    lnurl_auth_principal_linked lnurl_auth_principal_link_failed lnurl_auth_session_created
    lnurl_auth_step_up_required lnurl_auth_step_up_success lnurl_auth_step_up_failed
    lnurl_pay_request_created lnurl_pay_request_failed lnurl_pay_metadata_built lnurl_pay_callback_received
    lnurl_invoice_issued lnurl_invoice_issue_failed lnurl_payment_pending lnurl_payment_settled
    lnurl_payment_expired lnurl_payment_failed lnurl_payment_duplicate_callback lnurl_payment_proof_created
    lnurl_payment_proof_failed lnurl_entitlement_issuance_started lnurl_entitlement_issued
    lnurl_entitlement_issue_failed lnurl_success_action_created lnurl_success_action_opened
    lnurl_comment_received lnurl_payerdata_received lnurl_payerdata_auth_verified lnurl_payerdata_auth_failed
    lnurl_verify_started lnurl_verify_success lnurl_verify_unsettled lnurl_verify_failed
    lnurl_verify_response_invalid lnurl_verify_preimage_mismatch lnurl_verify_payment_request_mismatch
    lightning_address_resolution_requested lightning_address_resolved lightning_address_not_found
    lightning_address_disabled lightning_address_policy_denied lightning_address_domain_mismatch
    lightning_address_payment_request_created lnurl_withdraw_request_started lnurl_withdraw_policy_denied
    lnurl_withdraw_request_created lnurl_withdraw_qr_issued lnurl_withdraw_callback_received
    lnurl_withdraw_k1_unexpected lnurl_withdraw_k1_expired lnurl_withdraw_k1_reused
    lnurl_withdraw_invoice_invalid lnurl_withdraw_invoice_received lnurl_withdraw_payment_started
    lnurl_withdraw_paid lnurl_withdraw_failed lnurl_withdraw_expired lnurl_withdraw_revoked
    lnurl_withdraw_limit_exceeded lnurl_withdraw_step_up_required subscription_payment_bound_to_principal
    subscription_entitlement_issuance_started subscription_entitlement_issued subscription_entitlement_renewed
    subscription_entitlement_upgraded subscription_entitlement_downgraded subscription_entitlement_expired
    subscription_entitlement_frozen metric_entitlement_denied quota_exceeded entitlement_signature_failed
    policy_evaluation_started policy_quota_exceeded policy_metric_not_allowed policy_recovery_required
    policy_online_check_required policy_error revocation_repeated_idempotently revocation_check_failed
    wallet_session_revoked lnurl_k1_revoked lnurl_payment_request_revoked lnurl_withdraw_request_revoked
    subscription_entitlement_revoked access_certificate_revoked offline_validity_pack_revoked
    emergency_lockdown_started emergency_lockdown_completed emergency_lockdown_failed
    emergency_lockdown_release_requested emergency_lockdown_released emergency_lockdown_release_denied
    recovery_capsule_created recovery_quorum_progressed recovery_cooldown_completed recovery_abuse_detected
    recovery_seed_input_rejected recovery_private_key_input_rejected support_only_recovery_rejected
    access_certificate_issue_started access_certificate_issued access_certificate_issue_failed
    access_certificate_bound_to_wallet_principal access_certificate_bound_to_lightning_principal
    offline_validity_pack_issued offline_validity_pack_expired issuer_key_rotated crypto_epoch_advanced
    pq_signature_requested pq_signature_unsupported pq_signature_verified pq_signature_failed
    payregister_lnurl_payment_created payregister_lnurl_invoice_issued payregister_lnurl_payment_settled
    payregister_receipt_packet_created payregister_cashier_context_bound payregister_shift_pass_verified
    payregister_refund_requested payregister_refund_policy_denied payregister_refund_approved
    payregister_refund_paid payregister_terminal_revoked payregister_owner_step_up_required
    payregister_owner_step_up_success payregister_owner_step_up_failed""".split()
)
WALLET_LNURL_AUDIT_EVENT_TYPES |= frozenset(
    """access_integrity_calculated access_integrity_band_changed access_integrity_critical_signal
    access_integrity_step_up_recommended access_integrity_read_only_recommended
    access_integrity_lockdown_recommended access_integrity_cache_invalidated
    access_integrity_policy_hint_consumed""".split()
)
WALLET_LNURL_AUDIT_EVENT_TYPES |= frozenset(
    """recovery_capsule_creation_denied recovery_factor_rejected recovery_factor_replay_rejected
    recovery_duplicate_factor_rejected recovery_cooldown_extended recovery_ready_for_completion
    recovery_completion_requested recovery_completion_allowed recovery_completion_denied recovery_expired
    recovery_locked recovery_revoked recovery_sessions_revoked recovery_devices_frozen recovery_roles_frozen
    recovery_transparency_checkpoint_required""".split()
)
ACCESS_AUDIT_EVENT_TYPES = ACCESS_AUDIT_EVENT_TYPES | WALLET_LNURL_AUDIT_EVENT_TYPES


@dataclass(frozen=True, slots=True)
class AuditChainVerificationResult:
    valid: bool
    chain_id: str
    checked_events: int
    first_sequence: int | None
    last_sequence: int | None
    expected_head_hash: str | None
    actual_head_hash: str | None
    first_invalid_event_id: int | None
    failure_reason: str | None
    verification_started_at: datetime
    verification_completed_at: datetime


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
    chain_id: str = CANONICAL_CHAIN_ID,
    sequence_number: int = 1,
    event_version: int = AUDIT_EVENT_VERSION,
    event_category: str = "security",
    event_status: str = "success",
    severity: AuditSeverity | str = AuditSeverity.INFO,
    retention_class: AuditRetentionClass | str = AuditRetentionClass.SECURITY,
    idempotency_key_hash: str | None = None,
) -> dict[str, Any]:
    """Build deterministic, sanitized audit event material."""

    normalized_type = _validate_event_type(event_type)
    occurred = _isoformat_utc(occurred_at or datetime.now(UTC))
    return {
        "event_version": event_version,
        "chain_id": chain_id,
        "sequence_number": sequence_number,
        "event_type": normalized_type,
        "event_category": event_category,
        "event_status": event_status,
        "severity": str(severity),
        "retention_class": str(retention_class),
        "idempotency_key_hash": idempotency_key_hash,
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
    chain_id = str(canonical_event.get("chain_id", CANONICAL_CHAIN_ID))
    sequence = int(canonical_event.get("sequence_number", 1))
    return sha256_hex(previous + chain_id + str(sequence) + canonical_json(canonical_event))


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
        chain_id: str = CANONICAL_CHAIN_ID,
        event_category: str = "security",
        event_status: str = "success",
        severity: AuditSeverity | str = AuditSeverity.INFO,
        retention_class: AuditRetentionClass | str = AuditRetentionClass.SECURITY,
        idempotency_key_hash: str | None = None,
        occurred_at: datetime | None = None,
    ) -> AccessAuditEvent:
        if idempotency_key_hash:
            existing = self.db.execute(
                select(AccessAuditEvent).where(
                    AccessAuditEvent.chain_id == chain_id,
                    AccessAuditEvent.idempotency_key_hash == idempotency_key_hash,
                )
            ).scalar_one_or_none()
            if existing is not None:
                return existing
        for attempt in range(AUDIT_APPEND_MAX_RETRIES):
            try:
                with self.db.begin_nested():
                    latest = self.db.execute(
                        select(AccessAuditEvent)
                        .where(AccessAuditEvent.chain_id == chain_id)
                        .order_by(AccessAuditEvent.sequence_number.desc())
                        .limit(1)
                        .with_for_update()
                    ).scalar_one_or_none()
                    previous_hash = latest.event_hash if latest else None
                    sequence_number = (latest.sequence_number if latest else 0) + 1
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
                        occurred_at=occurred_at,
                        chain_id=chain_id,
                        sequence_number=sequence_number,
                        event_category=event_category,
                        event_status=event_status,
                        severity=severity,
                        retention_class=retention_class,
                        idempotency_key_hash=idempotency_key_hash,
                    )
                    event = AccessAuditEvent(
                        event_hash=compute_event_hash(previous_hash, canonical_event),
                        previous_event_hash=previous_hash,
                        event_type=canonical_event["event_type"],
                        event_version=AUDIT_EVENT_VERSION,
                        chain_id=chain_id,
                        sequence_number=sequence_number,
                        idempotency_key_hash=idempotency_key_hash,
                        event_category=event_category,
                        event_status=event_status,
                        severity=str(severity),
                        retention_class=str(retention_class),
                        actor_hash=actor_hash,
                        object_hash=object_hash,
                        canonical_event_json=canonical_event,
                        created_at=datetime.now(UTC),
                    )
                    self.db.add(event)
                    self.db.flush()
                return event
            except IntegrityError as exc:
                if idempotency_key_hash:
                    existing = self.db.execute(
                        select(AccessAuditEvent).where(
                            AccessAuditEvent.chain_id == chain_id,
                            AccessAuditEvent.idempotency_key_hash == idempotency_key_hash,
                        )
                    ).scalar_one_or_none()
                    if existing is not None:
                        return existing
                if attempt + 1 == AUDIT_APPEND_MAX_RETRIES:
                    raise AccessAuditError("access_audit_append_conflict") from exc
            except ValueError:
                raise
            except Exception as exc:
                raise AccessAuditError("access_audit_record_failed") from exc
        raise AccessAuditError("access_audit_append_conflict")

    def get_latest_event_hash(self) -> str | None:
        return self.db.execute(
            select(AccessAuditEvent.event_hash).order_by(AccessAuditEvent.id.desc()).limit(1)
        ).scalar_one_or_none()

    def verify_chain_detailed(
        self,
        chain_id: str = CANONICAL_CHAIN_ID,
        start_sequence: int | None = None,
        end_sequence: int | None = None,
    ) -> AuditChainVerificationResult:
        started = datetime.now(UTC)
        statement = select(AccessAuditEvent).where(AccessAuditEvent.chain_id == chain_id)
        if start_sequence is not None:
            statement = statement.where(AccessAuditEvent.sequence_number >= start_sequence)
        if end_sequence is not None:
            statement = statement.where(AccessAuditEvent.sequence_number <= end_sequence)
        rows = list(self.db.execute(statement.order_by(AccessAuditEvent.sequence_number)).scalars())
        previous = None
        expected_sequence = start_sequence or 1
        if start_sequence and start_sequence > 1:
            predecessor = self.db.execute(
                select(AccessAuditEvent).where(
                    AccessAuditEvent.chain_id == chain_id,
                    AccessAuditEvent.sequence_number == start_sequence - 1,
                )
            ).scalar_one_or_none()
            previous = predecessor.event_hash if predecessor else None
        failure = None
        invalid_id = None
        for row in rows:
            expected_hash = compute_event_hash(previous, dict(row.canonical_event_json))
            if row.sequence_number != expected_sequence:
                failure = "missing_or_duplicate_sequence"
            elif row.previous_event_hash != previous:
                failure = "broken_previous_hash"
            elif not compare_digest(row.event_hash, expected_hash):
                failure = "event_hash_mismatch"
            if failure:
                invalid_id = row.id
                break
            previous = row.event_hash
            expected_sequence += 1
        actual_head = rows[-1].event_hash if rows else previous
        return AuditChainVerificationResult(
            not failure,
            chain_id,
            len(rows),
            rows[0].sequence_number if rows else None,
            rows[-1].sequence_number if rows else None,
            previous,
            actual_head,
            invalid_id,
            failure,
            started,
            datetime.now(UTC),
        )

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
        event_type = (
            AccessAuditEventType.POLICY_ALLOWED.value
            if allowed
            else AccessAuditEventType.POLICY_DENIED.value
        )
        return self.record_event(event_type=event_type, **kwargs)

    def record_revocation_created(self, **kwargs: Any) -> AccessAuditEvent:
        return self.record_event(event_type=AccessAuditEventType.REVOCATION_CREATED.value, **kwargs)

    def record_lockdown_started(self, **kwargs: Any) -> AccessAuditEvent:
        return self.record_event(event_type=AccessAuditEventType.LOCKDOWN_STARTED.value, **kwargs)

    def record_recovery_started(self, **kwargs: Any) -> AccessAuditEvent:
        return self.record_event(event_type=AccessAuditEventType.RECOVERY_STARTED.value, **kwargs)

    def record_legacy_auth_disabled(self, **kwargs: Any) -> AccessAuditEvent:
        return self.record_event(
            event_type=AccessAuditEventType.LEGACY_AUTH_DISABLED.value, **kwargs
        )


def _validate_event_type(event_type: str) -> str:
    normalized = event_type.strip().lower()
    if normalized not in ACCESS_AUDIT_EVENT_TYPES:
        raise AccessAuditError("invalid_access_audit_event_type")
    return normalized


def _sanitize_mapping(metadata: Mapping[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in metadata.items():
        lowered = str(key).lower()
        safe_identifier = (
            lowered.endswith(_SAFE_AUDIT_KEY_SUFFIXES) or lowered in _SAFE_AUDIT_EXACT_KEYS
        )
        if not safe_identifier and any(
            forbidden in lowered for forbidden in _FORBIDDEN_AUDIT_KEY_PARTS
        ):
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
    if isinstance(value, str) and _looks_like_forbidden_secret(value):
        raise ValueError("forbidden_audit_secret_value")
    return value


def _looks_like_forbidden_secret(value: str) -> bool:
    candidate = value.strip()
    lowered = candidate.lower()
    if lowered.startswith(("xprv", "tprv", "bbp_live_", "lnbc", "lntb", "lnbcrt")):
        return True
    if re.fullmatch(r"[5KL][1-9A-HJ-NP-Za-km-z]{50,51}", candidate):
        return True
    # A probable mnemonic is rejected by shape, not by embedding a word list.
    words = candidate.split()
    return len(words) in {12, 15, 18, 21, 24} and all(
        re.fullmatch(r"[a-z]+", word) for word in words
    )


def _isoformat_utc(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
