"""Pure, commitment-only primitives for wallet/LNURL authority quorums."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
import hashlib
import json
from typing import Any


class QuorumType(StrEnum):
    SINGLE_PRINCIPAL = "single_principal"
    MULTI_WALLET = "multi_wallet"
    MULTI_METHOD = "multi_method"
    ROLE_BASED = "role_based"
    RECOVERY = "recovery"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"
    SOVEREIGN = "sovereign"
    PAYREGISTER = "payregister"
    WITHDRAW = "withdraw"
    ISSUER_ROTATION = "issuer_rotation"
    PQ_MIGRATION = "pq_migration"


class QuorumStatus(StrEnum):
    PENDING = "pending"
    PARTIALLY_SATISFIED = "partially_satisfied"
    SATISFIED = "satisfied"
    EXPIRED = "expired"
    DENIED = "denied"
    REVOKED = "revoked"
    CANCELLED = "cancelled"
    CONSUMED = "consumed"
    LOCKED = "locked"


class QuorumParticipantType(StrEnum):
    BITCOIN_WALLET_PRINCIPAL = "bitcoin_wallet_principal"
    LIGHTNING_WALLET_PRINCIPAL = "lightning_wallet_principal"
    WALLET_DEVICE = "wallet_device"
    HARDWARE_WALLET = "hardware_wallet"
    BUSINESS_ROLE = "business_role"
    ACCESS_CERTIFICATE = "access_certificate"
    RECOVERY_CAPSULE = "recovery_capsule"
    OFFLINE_RECOVERY_KIT = "offline_recovery_kit"
    TRANSPARENCY_CHECKPOINT = "transparency_checkpoint"
    ISSUER_KEY = "issuer_key"


class QuorumProofMethod(StrEnum):
    BIP322 = "bip322"
    LNURL_AUTH = "lnurl_auth"
    HARDWARE_WALLET = "hardware_wallet"
    AIR_GAPPED = "air_gapped"
    ACCESS_CERTIFICATE = "access_certificate"
    DEVICE_POP = "device_pop"
    RECOVERY_CAPSULE = "recovery_capsule"
    TRANSPARENCY_CHECKPOINT = "transparency_checkpoint"
    LEGACY_MESSAGE_SIGNATURE = "legacy_message_signature"


class QuorumDecision(StrEnum):
    PENDING = "pending"
    ALLOW = "allow"
    DENY = "deny"
    STEP_UP_REQUIRED = "step_up_required"
    ADDITIONAL_PARTICIPANT_REQUIRED = "additional_participant_required"
    STRONGER_PROOF_REQUIRED = "stronger_proof_required"
    QUORUM_EXPIRED = "quorum_expired"
    QUORUM_REVOKED = "quorum_revoked"
    POLICY_DENIED = "policy_denied"


class QuorumFailureReason(StrEnum):
    DUPLICATE_PRINCIPAL = "duplicate_principal"
    DUPLICATE_UNDERLYING_KEY = "duplicate_underlying_key"
    DUPLICATE_DEVICE = "duplicate_device"
    PROOF_TOO_WEAK = "proof_too_weak"
    PARTICIPANT_NOT_ALLOWED = "participant_not_allowed"
    PARTICIPANT_ROLE_MISMATCH = "participant_role_mismatch"
    PROOF_EXPIRED = "proof_expired"
    PROOF_REVOKED = "proof_revoked"
    PRINCIPAL_REVOKED = "principal_revoked"
    SESSION_INVALID = "session_invalid"
    POLICY_MISMATCH = "policy_mismatch"
    ACTION_MISMATCH = "action_mismatch"
    QUORUM_EXPIRED = "quorum_expired"
    QUORUM_CONSUMED = "quorum_consumed"
    INSUFFICIENT_DISTINCT_METHODS = "insufficient_distinct_methods"
    INSUFFICIENT_DISTINCT_PRINCIPALS = "insufficient_distinct_principals"
    REQUIRED_ROLE_MISSING = "required_role_missing"
    REQUIRED_HARDWARE_PROOF_MISSING = "required_hardware_proof_missing"
    REQUIRED_TRANSPARENCY_CHECKPOINT_MISSING = "required_transparency_checkpoint_missing"


@dataclass(frozen=True, slots=True)
class QuorumParticipantSlot:
    slot_id: str
    required_role: str | None = None
    allowed_principal_types: frozenset[QuorumParticipantType] = field(default_factory=frozenset)
    allowed_proof_methods: frozenset[QuorumProofMethod] = field(default_factory=frozenset)
    required_participant_type: QuorumParticipantType | None = None
    require_hardware_evidence: bool = False

    def canonical_payload(self) -> dict[str, object]:
        return {
            "slot_id": self.slot_id,
            "required_role": self.required_role,
            "allowed_principal_types": sorted(item.value for item in self.allowed_principal_types),
            "allowed_proof_methods": sorted(item.value for item in self.allowed_proof_methods),
            "required_participant_type": (
                self.required_participant_type.value if self.required_participant_type else None
            ),
            "require_hardware_evidence": self.require_hardware_evidence,
        }


@dataclass(frozen=True, slots=True)
class QuorumPolicy:
    policy_id: str
    version: int
    quorum_type: QuorumType
    action: str
    threshold: int
    participant_slots: tuple[QuorumParticipantSlot, ...]
    minimum_distinct_principals: int
    minimum_distinct_methods: int
    allowed_principal_types: frozenset[QuorumParticipantType]
    allowed_proof_methods: frozenset[QuorumProofMethod]
    forbidden_proof_methods: frozenset[QuorumProofMethod] = field(default_factory=frozenset)
    required_roles: frozenset[str] = field(default_factory=frozenset)
    required_methods: frozenset[QuorumProofMethod] = field(default_factory=frozenset)
    required_participant_types: frozenset[QuorumParticipantType] = field(default_factory=frozenset)
    maximum_compatibility_proofs: int = 0
    require_hardware_wallet: bool = False
    require_air_gapped_proof: bool = False
    require_active_pop_session: bool = True
    require_human_intent: bool = True
    require_recovery_capsule: bool = False
    require_transparency_checkpoint: bool = False
    expires_in_seconds: int = 300
    cooldown_seconds: int = 0
    policy_epoch: int = 1
    crypto_epoch: int = 1
    risk_level: str = "critical"
    one_time: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        slots = len(self.participant_slots)
        if self.threshold < 1 or self.threshold > slots:
            raise ValueError("invalid_quorum_threshold")
        if not 1 <= self.minimum_distinct_principals <= self.threshold:
            raise ValueError("invalid_quorum_distinct_principals")
        if not 1 <= self.minimum_distinct_methods <= self.threshold:
            raise ValueError("invalid_quorum_distinct_methods")
        if self.required_methods - self.allowed_proof_methods:
            raise ValueError("required_quorum_method_not_allowed")
        if self.required_methods & self.forbidden_proof_methods:
            raise ValueError("required_quorum_method_forbidden")
        if self.allowed_proof_methods & self.forbidden_proof_methods:
            raise ValueError("allowed_quorum_method_forbidden")
        if self.quorum_type is QuorumType.SOVEREIGN and (
            QuorumProofMethod.LEGACY_MESSAGE_SIGNATURE not in self.forbidden_proof_methods
        ):
            raise ValueError("sovereign_quorum_must_forbid_legacy_signature")
        if self.expires_in_seconds <= 0 or self.expires_in_seconds > 86400:
            raise ValueError("invalid_quorum_expiry")
        if self.maximum_compatibility_proofs < 0:
            raise ValueError("invalid_compatibility_proof_limit")
        slot_ids = [slot.slot_id for slot in self.participant_slots]
        if len(slot_ids) != len(set(slot_ids)):
            raise ValueError("duplicate_quorum_slot")
        _validate_safe_metadata(self.metadata)

    def canonical_payload(self) -> dict[str, object]:
        return {
            "policy_id": self.policy_id,
            "version": self.version,
            "quorum_type": self.quorum_type.value,
            "action": self.action,
            "threshold": self.threshold,
            "participant_slots": [slot.canonical_payload() for slot in self.participant_slots],
            "minimum_distinct_principals": self.minimum_distinct_principals,
            "minimum_distinct_methods": self.minimum_distinct_methods,
            "allowed_principal_types": sorted(item.value for item in self.allowed_principal_types),
            "allowed_proof_methods": sorted(item.value for item in self.allowed_proof_methods),
            "forbidden_proof_methods": sorted(item.value for item in self.forbidden_proof_methods),
            "required_roles": sorted(self.required_roles),
            "required_methods": sorted(item.value for item in self.required_methods),
            "required_participant_types": sorted(
                item.value for item in self.required_participant_types
            ),
            "maximum_compatibility_proofs": self.maximum_compatibility_proofs,
            "require_hardware_wallet": self.require_hardware_wallet,
            "require_air_gapped_proof": self.require_air_gapped_proof,
            "require_active_pop_session": self.require_active_pop_session,
            "require_human_intent": self.require_human_intent,
            "require_recovery_capsule": self.require_recovery_capsule,
            "require_transparency_checkpoint": self.require_transparency_checkpoint,
            "expires_in_seconds": self.expires_in_seconds,
            "cooldown_seconds": self.cooldown_seconds,
            "policy_epoch": self.policy_epoch,
            "crypto_epoch": self.crypto_epoch,
            "risk_level": self.risk_level,
            "one_time": self.one_time,
            "metadata": self.metadata,
        }

    @property
    def policy_hash(self) -> str:
        payload = json.dumps(
            self.canonical_payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
        return f"sha256:{hashlib.sha256(payload).hexdigest()}"


@dataclass(frozen=True, slots=True)
class VerifiedQuorumApproval:
    approval_hash: str
    participant_type: QuorumParticipantType
    principal_type: QuorumParticipantType
    principal_hash: str
    underlying_key_hash: str
    proof_method: QuorumProofMethod
    proof_hash: str
    verification_strength: str
    verified_at: str
    expires_at: str
    intent_hash: str
    action: str
    policy_hash: str
    role: str | None = None
    device_fingerprint: str | None = None
    hardware_evidence_verified: bool = False
    cryptographically_verified: bool = True
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        commitments = {
            "approval_hash": self.approval_hash,
            "principal_hash": self.principal_hash,
            "underlying_key_hash": self.underlying_key_hash,
            "proof_hash": self.proof_hash,
            "intent_hash": self.intent_hash,
            "policy_hash": self.policy_hash,
        }
        for name, value in commitments.items():
            if not value.startswith(("sha256:", "hmac-sha256:", "hmac:")):
                raise ValueError(f"unsafe_quorum_{name}")
        if self.device_fingerprint and not self.device_fingerprint.startswith(
            ("sha256:", "hmac-sha256:", "hmac:")
        ):
            raise ValueError("unsafe_quorum_device_fingerprint")


@dataclass(frozen=True, slots=True)
class QuorumEvaluation:
    status: QuorumStatus
    decision: QuorumDecision
    reason_code: str
    threshold: int
    approval_count: int
    distinct_principals: int
    distinct_methods: int
    filled_slots: tuple[str, ...]
    missing_roles: tuple[str, ...] = ()
    missing_methods: tuple[str, ...] = ()
    missing_participant_types: tuple[str, ...] = ()
    cooldown_until: str | None = None
    policy_hash: str | None = None


def _validate_safe_metadata(value: object) -> None:
    forbidden = {
        "seed",
        "mnemonic",
        "xprv",
        "private_key",
        "raw_signature",
        "raw_k1",
        "linking_key",
        "session_token",
        "wallet_address",
    }
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in forbidden:
                raise ValueError("unsafe_quorum_metadata")
            _validate_safe_metadata(child)
    elif isinstance(value, (list, tuple, set, frozenset)):
        for child in value:
            _validate_safe_metadata(child)
    elif isinstance(value, str) and value.lower().startswith(("xprv", "tprv")):
        raise ValueError("unsafe_quorum_metadata")
