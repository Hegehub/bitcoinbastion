"""Internal, commitment-only Recovery Capsule models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class RecoveryCapsuleStatus(StrEnum):
    CREATED = "created"
    AWAITING_FACTORS = "awaiting_factors"
    FACTOR_VERIFICATION_IN_PROGRESS = "factor_verification_in_progress"
    COOLDOWN = "cooldown"
    READY_FOR_COMPLETION = "ready_for_completion"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    LOCKED = "locked"
    REVOKED = "revoked"


class RecoveryProfile(StrEnum):
    LITE_BASIC = "lite_basic"
    PLUS = "plus"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"
    SOVEREIGN = "sovereign"


class RecoveryFactorType(StrEnum):
    BIP322_WALLET_PROOF = "bip322_wallet_proof"
    LNURL_AUTH_PROOF = "lnurl_auth_proof"
    PAYMENT_PROOF = "payment_proof"
    ACTIVE_SUBSCRIPTION_PROOF = "active_subscription_proof"
    TRUSTED_DEVICE = "trusted_device"
    DEVICE_HISTORY = "device_history"
    RECOVERY_FILE = "recovery_file"
    ACCESS_CERTIFICATE = "access_certificate"
    HARDWARE_WALLET_PROOF = "hardware_wallet_proof"
    AIR_GAPPED_WALLET_PROOF = "air_gapped_wallet_proof"
    OWNER_WALLET_PROOF = "owner_wallet_proof"
    ADMIN_WALLET_PROOF = "admin_wallet_proof"
    RECOVERY_OPERATOR_PROOF = "recovery_operator_proof"
    OFFLINE_RECOVERY_KIT = "offline_recovery_kit"
    TRANSPARENCY_CHECKPOINT = "transparency_checkpoint"
    TIME_DELAY = "time_delay"
    COOLDOWN = "cooldown"
    BUSINESS_ROLE_QUORUM = "business_role_quorum"
    MULTI_WALLET_QUORUM = "multi_wallet_quorum"
    MULTI_METHOD_QUORUM = "multi_method_quorum"


@dataclass(frozen=True, slots=True)
class RecoveryCapsule:
    capsule_id: str
    capsule_hash: str
    schema_version: int
    crypto_epoch: int
    policy_epoch: int
    principal_hash: str
    principal_type: str
    recovery_profile: RecoveryProfile
    status: RecoveryCapsuleStatus
    required_factors: tuple[RecoveryFactorType, ...]
    verified_factors: tuple[RecoveryFactorType, ...]
    required_factor_count: int
    quorum_policy_id: str | None
    trusted_device_requirement: str
    cooldown_started_at: datetime | None
    cooldown_expires_at: datetime | None
    expires_at: datetime
    attempt_count: int
    maximum_attempts: int
    risk_level: str
    recovery_reason: str
    requested_operations: tuple[str, ...]
    revoked_targets: tuple[str, ...]
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    issuer_key_id: str = "recovery-capsule-issuer"
    issuer_signature_metadata: dict[str, Any] = field(default_factory=dict)
    audit_chain_head: str | None = None
    transparency_checkpoint_id: str | None = None
    policy_hash: str = ""


@dataclass(frozen=True, slots=True)
class RecoveryFactorSubmission:
    factor_type: RecoveryFactorType
    proof_reference_hash: str
    factor_fingerprint: str
    submitted_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RecoveryVerificationContext:
    principal_hash: str
    policy_epoch: int
    revocation_state: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RecoveryFactorResult:
    verified: bool
    factor_type: RecoveryFactorType
    factor_fingerprint: str
    verification_strength: str
    verified_at: datetime
    expires_at: datetime | None
    reason_code: str
    limitations: tuple[str, ...] = ()
    audit_metadata: dict[str, Any] = field(default_factory=dict)
    requires_additional_factor: bool = True
    replay_reference_hash: str | None = None


@dataclass(frozen=True, slots=True)
class RecoveryCompletionResult:
    capsule_hash: str
    status: RecoveryCapsuleStatus
    session_mode: str
    revoked_targets: tuple[str, ...]
    requires_fresh_step_up: bool = True
