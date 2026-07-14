"""Wallet principal service types.

Wallet principals are pseudonymous cryptographic actors. They are not human
identity records, customer accounts, e-mail accounts, or bearer credentials.
Bitcoin and Lightning principal namespaces are intentionally separate so a
Bitcoin wallet proof cannot be confused with a future LNURL-auth Lightning
linking-key proof.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from app.domain.wallet_auth.networks import WalletNetwork
from app.domain.wallet_auth.principals import WalletPrincipalStatus
from app.domain.wallet_auth.proofs import WalletProofType, WalletScriptType, WalletVerificationStrength
from app.services.wallet_auth.privacy_commitments import reject_forbidden_wallet_secret_input
from app.services.wallet_auth.verifiers.base import WalletProofVerificationResult


class PrincipalType(StrEnum):
    BITCOIN_WALLET_PRINCIPAL = "bitcoin_wallet_principal"
    LIGHTNING_WALLET_PRINCIPAL = "lightning_wallet_principal"
    ACCESS_CERTIFICATE_PRINCIPAL = "access_certificate_principal"
    DELEGATED_PRINCIPAL = "delegated_principal"
    BUSINESS_PRINCIPAL = "business_principal"
    PAYREGISTER_PRINCIPAL = "payregister_principal"
    BOT_PRINCIPAL = "bot_principal"


class WalletPrincipalReasonCode(StrEnum):
    PRINCIPAL_CREATED = "wallet_principal_created"
    PRINCIPAL_FOUND = "wallet_principal_found"
    VERIFICATION_REFRESHED = "wallet_principal_verification_refreshed"
    PROOF_ASSOCIATED = "wallet_proof_associated"
    PRINCIPAL_NOT_FOUND = "wallet_principal_not_found"
    PROOF_REQUIRED = "wallet_principal_proof_required"
    PROOF_MISMATCH = "wallet_principal_proof_mismatch"
    NETWORK_MISMATCH = "wallet_principal_network_mismatch"
    INVALID_TRANSITION = "wallet_principal_invalid_transition"
    ALREADY_REVOKED = "wallet_principal_already_revoked"
    SUSPENDED = "wallet_principal_suspended"
    RECOVERY_LOCKED = "wallet_principal_recovery_locked"
    PRIVACY_VIOLATION = "wallet_principal_privacy_violation"
    REPOSITORY_CONFLICT = "wallet_principal_repository_conflict"


@dataclass(frozen=True, slots=True)
class VerifiedWalletProof:
    proof_type: WalletProofType
    normalized_wallet_identifier: str
    wallet_identifier_commitment: str
    network: WalletNetwork
    script_type: WalletScriptType
    verification_strength: WalletVerificationStrength
    verified_at: datetime
    proof_hash: str
    verifier_name: str
    verifier_version: str
    limitations: tuple[str, ...] = ()
    policy_hints: tuple[str, ...] = ()
    script_pubkey_hash: str | None = None
    action: str = "wallet_principal_create"
    policy_hash: str | None = None
    expires_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.verified_at.tzinfo is None:
            raise ValueError("wallet_principal_verified_at_timezone_required")
        if self.expires_at is not None and self.expires_at.tzinfo is None:
            raise ValueError("wallet_principal_expires_at_timezone_required")
        _require_commitment(self.wallet_identifier_commitment, "wallet_identifier_commitment")
        _require_commitment(self.proof_hash, "proof_hash")
        if self.script_pubkey_hash is not None and not self.script_pubkey_hash.startswith("sha256:"):
            raise ValueError("wallet_principal_script_pubkey_hash_required")
        _reject_identity_like(self.normalized_wallet_identifier, "normalized_wallet_identifier")

    @classmethod
    def from_verification_result(
        cls,
        *,
        result: WalletProofVerificationResult,
        normalized_wallet_identifier: str,
        action: str = "wallet_principal_create",
        policy_hash: str | None = None,
    ) -> VerifiedWalletProof:
        if not result.verified:
            raise ValueError("wallet_principal_verified_proof_required")
        return cls(
            proof_type=result.proof_type,
            normalized_wallet_identifier=normalized_wallet_identifier,
            wallet_identifier_commitment=result.wallet_identifier_hash,
            network=result.wallet_network,
            script_type=result.script_type,
            verification_strength=result.verification_strength,
            verified_at=result.verified_at,
            proof_hash=result.proof_fingerprint,
            verifier_name=result.verifier_id,
            verifier_version=result.verifier_version,
            limitations=tuple(result.limitations),
            policy_hints=tuple(result.policy_hints),
            action=action,
            policy_hash=policy_hash,
        )

    def is_fresh(self, *, now: datetime, max_age_seconds: int = 900) -> bool:
        checked_now = now if now.tzinfo else now.replace(tzinfo=UTC)
        if self.expires_at is not None and self.expires_at <= checked_now:
            return False
        return checked_now - self.verified_at <= timedelta(seconds=max_age_seconds)


@dataclass(frozen=True, slots=True)
class WalletPrincipalRecord:
    principal_hash: str
    principal_type: PrincipalType
    status: WalletPrincipalStatus
    network: WalletNetwork | None
    primary_proof_method: WalletProofType
    current_proof_strength: WalletVerificationStrength
    highest_verified_strength: WalletVerificationStrength
    address_hash: str | None
    script_pubkey_hash: str | None
    schema_epoch: int
    crypto_epoch: int
    policy_epoch: int
    created_at: datetime
    updated_at: datetime
    last_verified_at: datetime | None
    last_high_assurance_at: datetime | None = None
    revoked_at: datetime | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def safe_summary(self) -> dict[str, object]:
        return {
            "principal_hash": self.principal_hash,
            "principal_type": self.principal_type.value,
            "status": self.status.value,
            "network": self.network.value if self.network else None,
            "primary_proof_method": self.primary_proof_method.value,
            "current_proof_strength": self.current_proof_strength.value,
            "highest_verified_strength": self.highest_verified_strength.value,
            "last_verified_at": self.last_verified_at.isoformat() if self.last_verified_at else None,
            "revoked": self.status is WalletPrincipalStatus.REVOKED,
        }


@dataclass(frozen=True, slots=True)
class WalletProofAssociation:
    principal_hash: str
    proof_type: WalletProofType
    proof_hash: str
    action: str
    verification_strength: WalletVerificationStrength
    script_type: WalletScriptType
    network: WalletNetwork
    verifier_name: str
    verifier_version: str
    verified_at: datetime
    limitations: tuple[str, ...] = ()
    policy_hints: tuple[str, ...] = ()
    policy_hash: str | None = None


@dataclass(frozen=True, slots=True)
class PrincipalCreationResult:
    principal_hash: str
    principal_type: PrincipalType
    status: WalletPrincipalStatus
    network: WalletNetwork
    proof_method: WalletProofType
    verification_strength: WalletVerificationStrength
    highest_verified_strength: WalletVerificationStrength
    created: bool
    last_verified_at: datetime

    def safe_summary(self) -> dict[str, object]:
        return {
            "principal_hash": self.principal_hash,
            "principal_type": self.principal_type.value,
            "status": self.status.value,
            "network": self.network.value,
            "proof_method": self.proof_method.value,
            "verification_strength": self.verification_strength.value,
            "highest_verified_strength": self.highest_verified_strength.value,
            "created": self.created,
            "last_verified_at": self.last_verified_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class PrincipalStateTransitionResult:
    principal_hash: str
    previous_status: WalletPrincipalStatus
    new_status: WalletPrincipalStatus
    reason_code: str
    changed: bool


@dataclass(frozen=True, slots=True)
class PrincipalPolicyContext:
    actor_type: str
    principal_hash: str
    principal_status: str
    auth_method: str
    verification_strength: str
    network: str | None
    device_bound: bool
    session_active: bool
    entitlement_status: str
    revoked: bool
    recovery_locked: bool
    policy_epoch: int

    def as_dict(self) -> dict[str, object]:
        return {
            "actor_type": self.actor_type,
            "principal_hash": self.principal_hash,
            "principal_status": self.principal_status,
            "auth_method": self.auth_method,
            "verification_strength": self.verification_strength,
            "network": self.network,
            "device_bound": self.device_bound,
            "session_active": self.session_active,
            "entitlement_status": self.entitlement_status,
            "revoked": self.revoked,
            "recovery_locked": self.recovery_locked,
            "policy_epoch": self.policy_epoch,
        }


@dataclass(frozen=True, slots=True)
class DeviceBindingContext:
    principal_hash: str
    principal_type: PrincipalType
    status: WalletPrincipalStatus
    network: WalletNetwork | None
    current_proof_method: WalletProofType
    verification_strength: WalletVerificationStrength
    last_verified_at: datetime | None
    recovery_state: str
    revocation_state_summary: str
    allowed_binding_methods: tuple[str, ...]


_STRENGTH_RANK = {
    WalletVerificationStrength.COMPATIBILITY: 0,
    WalletVerificationStrength.STANDARD: 1,
    WalletVerificationStrength.HIGH_ASSURANCE: 2,
    WalletVerificationStrength.SOVEREIGN: 3,
}


def max_strength(
    first: WalletVerificationStrength, second: WalletVerificationStrength
) -> WalletVerificationStrength:
    return first if _STRENGTH_RANK[first] >= _STRENGTH_RANK[second] else second


def _require_commitment(value: str, field_name: str) -> None:
    if not (value.startswith("hmac-sha256:") or value.startswith("sha256:")):
        raise ValueError(f"{field_name}_must_be_commitment")


def _reject_identity_like(value: str, field_name: str) -> None:
    reject_forbidden_wallet_secret_input(value, field_name)
    lowered = value.lower()
    if "@" in value and "." in value:
        raise ValueError("wallet_principal_email_or_lightning_address_not_identifier")
    if lowered.startswith(("global_user", "user_", "customer_")):
        raise ValueError("wallet_principal_global_user_id_not_allowed")
