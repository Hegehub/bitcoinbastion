"""Domain types for advisory Access Integrity Score 2.0."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class AccessIntegrityBand(StrEnum):
    EXCELLENT = "excellent"
    STRONG = "strong"
    GUARDED = "guarded"
    RESTRICTED = "restricted"
    CRITICAL = "critical"


class AccessIntegritySignalCategory(StrEnum):
    WALLET_PROOF = "wallet_proof"
    LNURL_AUTH = "lnurl_auth"
    DEVICE = "device"
    SESSION = "session"
    ENTITLEMENT = "entitlement"
    POLICY = "policy"
    REVOCATION = "revocation"
    RECOVERY = "recovery"
    PRIVACY = "privacy"
    DELEGATION = "delegation"
    BUSINESS_QUORUM = "business_quorum"
    ACCESS_CERTIFICATE = "access_certificate"
    OFFLINE_VALIDITY = "offline_validity"
    TRANSPARENCY = "transparency"
    OBSERVABILITY = "observability"


class AccessIntegritySignalStatus(StrEnum):
    HEALTHY = "healthy"
    ACCEPTABLE = "acceptable"
    DEGRADED = "degraded"
    UNSAFE = "unsafe"
    UNAVAILABLE = "unavailable"
    NOT_APPLICABLE = "not_applicable"


class AccessIntegrityRecommendation(StrEnum):
    NONE = "none"
    REFRESH_WALLET_PROOF = "refresh_wallet_proof"
    PERFORM_LNURL_STEP_UP = "perform_lnurl_step_up"
    BIND_TRUSTED_DEVICE = "bind_trusted_device"
    REVOKE_STALE_DEVICE = "revoke_stale_device"
    ROTATE_SESSION = "rotate_session"
    CONFIGURE_RECOVERY_CAPSULE = "configure_recovery_capsule"
    SYNCHRONIZE_REVOCATION_REGISTRY = "synchronize_revocation_registry"
    REDUCE_CHILD_KEY_SCOPE = "reduce_child_key_scope"
    REPLACE_LEGACY_SIGNATURE = "replace_legacy_signature"
    USE_DEDICATED_AUTH_ADDRESS = "use_dedicated_auth_address"
    ENABLE_HARDWARE_WALLET_STEP_UP = "enable_hardware_wallet_step_up"
    CONFIGURE_BUSINESS_QUORUM = "configure_business_quorum"
    RENEW_SUBSCRIPTION = "renew_subscription"
    REFRESH_OFFLINE_VALIDITY_PACK = "refresh_offline_validity_pack"
    REQUIRE_ACCESS_CERTIFICATE = "require_access_certificate"
    ENTER_READ_ONLY = "enter_read_only"
    START_LOCKDOWN = "start_lockdown"


@dataclass(frozen=True, slots=True)
class AccessIntegritySignal:
    signal_id: str
    category: AccessIntegritySignalCategory
    status: AccessIntegritySignalStatus
    score_delta: float
    maximum_points: float
    evidence_code: str
    explanation: str
    remediation: AccessIntegrityRecommendation = AccessIntegrityRecommendation.NONE
    observed_at: datetime | None = None
    expires_at: datetime | None = None
    evidence_fingerprint: str | None = None
    sensitive_details_redacted: bool = True
    hard_cap: int | None = None


@dataclass(frozen=True, slots=True)
class AccessIntegrityContext:
    principal_hash: str
    actor_type: str
    evidence: dict[str, Any] = field(default_factory=dict)
    calculated_at: datetime | None = None
    policy_epoch: int = 1
    revocation_epoch: int = 0
    crypto_epoch: int = 1
    schema_epoch: int = 1


@dataclass(frozen=True, slots=True)
class AccessIntegrityScore:
    version: str
    principal_hash: str
    actor_type: str
    score: int
    band: AccessIntegrityBand
    confidence: float
    calculated_at: datetime
    evidence_fresh_until: datetime | None
    signals: tuple[AccessIntegritySignal, ...]
    recommendations: tuple[AccessIntegrityRecommendation, ...]
    policy_hints: tuple[str, ...]
    critical_flags: tuple[str, ...]
    evidence_fingerprint: str
    crypto_epoch: int
    policy_epoch: int
    schema_epoch: int
