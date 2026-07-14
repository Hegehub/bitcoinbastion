"""Unified Wallet Principal lifecycle service.

The service starts after a wallet proof has already been verified by the wallet
proof verifier layer. It creates and manages pseudonymous Bitcoin Wallet
Principals, prepares safe device/policy context, records proof associations, and
exposes narrow audit/revocation hooks. It does not verify signatures, issue PoP
sessions, grant API access, check subscriptions, or implement LNURL callbacks.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from typing import Protocol

from app.domain.wallet_auth.networks import WalletNetwork
from app.domain.wallet_auth.principals import WalletPrincipalStatus
from app.domain.wallet_auth.proofs import WalletProofType, WalletVerificationStrength
from app.services.wallet_auth.principal_repository import (
    InMemoryWalletPrincipalRepository,
    WalletPrincipalRepository,
    WalletPrincipalRepositoryConflictError,
    apply_successful_verification,
    build_principal_record,
)
from app.services.wallet_auth.principal_types import (
    DeviceBindingContext,
    PrincipalCreationResult,
    PrincipalPolicyContext,
    PrincipalStateTransitionResult,
    PrincipalType,
    VerifiedWalletProof,
    WalletPrincipalReasonCode,
    WalletPrincipalRecord,
    WalletProofAssociation,
)
from app.services.wallet_auth.privacy_commitments import compute_hmac_lookup_hash

AuditEmitter = Callable[[str, dict[str, object]], None]


class WalletPrincipalRevocationRegistry(Protocol):
    def is_revoked(self, *, target_type: str, target_hash: str) -> bool: ...
    def revoke(self, *, target_type: str, target_hash: str, reason_code: str, policy_epoch: int) -> None: ...


class WalletPrincipalError(ValueError):
    """Base safe principal error."""

    def __init__(self, reason_code: str) -> None:
        self.reason_code = reason_code
        super().__init__(reason_code)


class WalletPrincipalNotFoundError(WalletPrincipalError): ...
class WalletPrincipalAlreadyRevokedError(WalletPrincipalError): ...
class WalletPrincipalSuspendedError(WalletPrincipalError): ...
class WalletPrincipalRecoveryLockedError(WalletPrincipalError): ...
class WalletPrincipalInvalidTransitionError(WalletPrincipalError): ...
class WalletPrincipalProofRequiredError(WalletPrincipalError): ...
class WalletPrincipalProofMismatchError(WalletPrincipalError): ...
class WalletPrincipalNetworkMismatchError(WalletPrincipalError): ...
class WalletPrincipalRepositoryConflictServiceError(WalletPrincipalError): ...
class WalletPrincipalPrivacyViolationError(WalletPrincipalError): ...


_ALLOWED_PROOF_TYPES = frozenset(
    {
        WalletProofType.BIP322,
        WalletProofType.LEGACY_MESSAGE_SIGNATURE,
        WalletProofType.HARDWARE_WALLET,
        WalletProofType.AIR_GAPPED,
        WalletProofType.MULTISIG_QUORUM,
        WalletProofType.ACCESS_CERTIFICATE_BRIDGE,
        WalletProofType.LNURL_AUTH,
    }
)
_ALLOWED_TRANSITIONS: dict[WalletPrincipalStatus, frozenset[WalletPrincipalStatus]] = {
    WalletPrincipalStatus.PENDING_VERIFICATION: frozenset({WalletPrincipalStatus.ACTIVE}),
    WalletPrincipalStatus.ACTIVE: frozenset(
        {
            WalletPrincipalStatus.SUSPENDED,
            WalletPrincipalStatus.RECOVERY_LOCKED,
            WalletPrincipalStatus.REVOKED,
        }
    ),
    WalletPrincipalStatus.SUSPENDED: frozenset(
        {
            WalletPrincipalStatus.ACTIVE,
            WalletPrincipalStatus.RECOVERY_LOCKED,
            WalletPrincipalStatus.REVOKED,
        }
    ),
    WalletPrincipalStatus.RECOVERY_LOCKED: frozenset({WalletPrincipalStatus.REVOKED}),
    WalletPrincipalStatus.REVOKED: frozenset(),
}


class PrincipalService:
    def __init__(
        self,
        *,
        repository: WalletPrincipalRepository | None = None,
        server_pepper: str | bytes,
        audit_emitter: AuditEmitter | None = None,
        revocation_registry: WalletPrincipalRevocationRegistry | None = None,
        proof_max_age_seconds: int = 900,
    ) -> None:
        self.repository = repository or InMemoryWalletPrincipalRepository()
        self.server_pepper = server_pepper
        self.audit_emitter = audit_emitter
        self.revocation_registry = revocation_registry
        self.proof_max_age_seconds = proof_max_age_seconds

    async def find_principal_by_hash(self, principal_hash: str) -> WalletPrincipalRecord | None:
        _validate_principal_hash(principal_hash)
        return await self.repository.get_by_principal_hash(principal_hash)

    async def get_principal(self, principal_hash: str) -> WalletPrincipalRecord:
        record = await self.find_principal_by_hash(principal_hash)
        if record is None:
            raise WalletPrincipalNotFoundError(WalletPrincipalReasonCode.PRINCIPAL_NOT_FOUND.value)
        return record

    async def find_bitcoin_principal_by_wallet_commitment(
        self, *, wallet_identifier_commitment: str, network: WalletNetwork
    ) -> WalletPrincipalRecord | None:
        _validate_commitment(wallet_identifier_commitment, "wallet_identifier_commitment")
        return await self.repository.get_by_wallet_commitment(
            principal_type=PrincipalType.BITCOIN_WALLET_PRINCIPAL,
            wallet_commitment=wallet_identifier_commitment,
            network=network,
        )

    async def create_bitcoin_principal(self, *, proof: VerifiedWalletProof) -> PrincipalCreationResult:
        self._validate_verified_proof(proof)
        principal_hash = self.derive_principal_hash(
            principal_type=PrincipalType.BITCOIN_WALLET_PRINCIPAL,
            wallet_identifier_commitment=proof.wallet_identifier_commitment,
            network=proof.network,
        )
        now = _now()
        record = build_principal_record(principal_hash=principal_hash, proof=proof, now=now)
        try:
            created = await self.repository.create(record, wallet_commitment=proof.wallet_identifier_commitment)
            await self.associate_wallet_proof(principal_hash=created.principal_hash, proof=proof)
            await self.repository.commit()
        except WalletPrincipalRepositoryConflictError as exc:
            await self.repository.rollback()
            raise WalletPrincipalRepositoryConflictServiceError(
                WalletPrincipalReasonCode.REPOSITORY_CONFLICT.value
            ) from exc
        self._emit_audit("wallet_principal_created", created, proof=proof, reason="created")
        return _creation_result(created, proof=proof, created=True)

    async def find_or_create_bitcoin_principal(self, *, proof: VerifiedWalletProof) -> PrincipalCreationResult:
        self._validate_verified_proof(proof)
        existing = await self.find_bitcoin_principal_by_wallet_commitment(
            wallet_identifier_commitment=proof.wallet_identifier_commitment,
            network=proof.network,
        )
        if existing is not None:
            refreshed = await self.record_successful_verification(existing.principal_hash, proof=proof)
            self._emit_audit("wallet_principal_found", refreshed, proof=proof, reason="found")
            return _creation_result(refreshed, proof=proof, created=False)
        try:
            return await self.create_bitcoin_principal(proof=proof)
        except WalletPrincipalRepositoryConflictServiceError:
            # Transaction-safe retry path for concurrent find-or-create races.
            existing = await self.find_bitcoin_principal_by_wallet_commitment(
                wallet_identifier_commitment=proof.wallet_identifier_commitment,
                network=proof.network,
            )
            if existing is None:
                raise
            refreshed = await self.record_successful_verification(existing.principal_hash, proof=proof)
            return _creation_result(refreshed, proof=proof, created=False)

    async def verify_principal_status(self, principal_hash: str) -> WalletPrincipalRecord:
        record = await self.get_principal(principal_hash)
        if self.revocation_registry and self.revocation_registry.is_revoked(
            target_type="wallet_principal", target_hash=record.principal_hash
        ):
            raise WalletPrincipalAlreadyRevokedError(WalletPrincipalReasonCode.ALREADY_REVOKED.value)
        if record.status is WalletPrincipalStatus.ACTIVE:
            return record
        if record.status is WalletPrincipalStatus.PENDING_VERIFICATION:
            raise WalletPrincipalProofRequiredError(WalletPrincipalReasonCode.PROOF_REQUIRED.value)
        if record.status is WalletPrincipalStatus.SUSPENDED:
            raise WalletPrincipalSuspendedError(WalletPrincipalReasonCode.SUSPENDED.value)
        if record.status is WalletPrincipalStatus.RECOVERY_LOCKED:
            raise WalletPrincipalRecoveryLockedError(WalletPrincipalReasonCode.RECOVERY_LOCKED.value)
        raise WalletPrincipalAlreadyRevokedError(WalletPrincipalReasonCode.ALREADY_REVOKED.value)

    async def record_successful_verification(
        self, principal_hash: str, *, proof: VerifiedWalletProof
    ) -> WalletPrincipalRecord:
        self._validate_verified_proof(proof)
        record = await self.get_principal(principal_hash)
        if record.network is not proof.network:
            raise WalletPrincipalNetworkMismatchError(WalletPrincipalReasonCode.NETWORK_MISMATCH.value)
        if record.address_hash != proof.wallet_identifier_commitment:
            raise WalletPrincipalProofMismatchError(WalletPrincipalReasonCode.PROOF_MISMATCH.value)
        refreshed = apply_successful_verification(record=record, proof=proof, now=_now())
        await self.repository.update(refreshed)
        await self.associate_wallet_proof(principal_hash=principal_hash, proof=proof)
        await self.repository.commit()
        self._emit_audit("wallet_principal_verification_refreshed", refreshed, proof=proof, reason="refreshed")
        return refreshed

    async def associate_wallet_proof(self, *, principal_hash: str, proof: VerifiedWalletProof) -> bool:
        self._validate_verified_proof(proof)
        record = await self.get_principal(principal_hash)
        if record.network is not proof.network:
            raise WalletPrincipalNetworkMismatchError(WalletPrincipalReasonCode.NETWORK_MISMATCH.value)
        association = WalletProofAssociation(
            principal_hash=principal_hash,
            proof_type=proof.proof_type,
            proof_hash=proof.proof_hash,
            action=proof.action,
            verification_strength=proof.verification_strength,
            script_type=proof.script_type,
            network=proof.network,
            verifier_name=proof.verifier_name,
            verifier_version=proof.verifier_version,
            verified_at=proof.verified_at,
            limitations=proof.limitations,
            policy_hints=proof.policy_hints,
            policy_hash=proof.policy_hash,
        )
        added = await self.repository.add_proof_association(association)
        if added:
            self._emit_audit("wallet_proof_associated", record, proof=proof, reason="associated")
        return added

    async def list_principal_proof_methods(self, principal_hash: str) -> tuple[WalletProofType, ...]:
        await self.get_principal(principal_hash)
        return await self.repository.list_proof_methods(principal_hash)

    async def suspend_principal(self, principal_hash: str, *, reason_code: str) -> PrincipalStateTransitionResult:
        return await self._transition(principal_hash, WalletPrincipalStatus.SUSPENDED, reason_code, "wallet_principal_suspended")

    async def activate_principal(self, principal_hash: str, *, reason_code: str) -> PrincipalStateTransitionResult:
        return await self._transition(principal_hash, WalletPrincipalStatus.ACTIVE, reason_code, "wallet_principal_activated")

    async def recovery_lock_principal(self, principal_hash: str, *, reason_code: str) -> PrincipalStateTransitionResult:
        return await self._transition(principal_hash, WalletPrincipalStatus.RECOVERY_LOCKED, reason_code, "wallet_principal_recovery_locked")

    async def revoke_principal(self, principal_hash: str, *, reason_code: str) -> PrincipalStateTransitionResult:
        record = await self.get_principal(principal_hash)
        if record.status is WalletPrincipalStatus.REVOKED:
            return PrincipalStateTransitionResult(
                principal_hash=principal_hash,
                previous_status=WalletPrincipalStatus.REVOKED,
                new_status=WalletPrincipalStatus.REVOKED,
                reason_code=reason_code,
                changed=False,
            )
        result = await self._transition(principal_hash, WalletPrincipalStatus.REVOKED, reason_code, "wallet_principal_revoked")
        if self.revocation_registry:
            self.revocation_registry.revoke(
                target_type="wallet_principal",
                target_hash=principal_hash,
                reason_code=reason_code,
                policy_epoch=(await self.get_principal(principal_hash)).policy_epoch,
            )
        return result

    async def prepare_device_binding_context(self, principal_hash: str) -> DeviceBindingContext:
        record = await self.get_principal(principal_hash)
        return DeviceBindingContext(
            principal_hash=record.principal_hash,
            principal_type=record.principal_type,
            status=record.status,
            network=record.network,
            current_proof_method=record.primary_proof_method,
            verification_strength=record.current_proof_strength,
            last_verified_at=record.last_verified_at,
            recovery_state="locked" if record.status is WalletPrincipalStatus.RECOVERY_LOCKED else "not_locked",
            revocation_state_summary="revoked" if record.status is WalletPrincipalStatus.REVOKED else "not_checked",
            allowed_binding_methods=("device_key", "hardware_evidence_step_up"),
        )

    async def build_policy_actor_context(self, principal_hash: str) -> PrincipalPolicyContext:
        record = await self.get_principal(principal_hash)
        return PrincipalPolicyContext(
            actor_type=record.principal_type.value,
            principal_hash=record.principal_hash,
            principal_status=record.status.value,
            auth_method=record.primary_proof_method.value,
            verification_strength=record.current_proof_strength.value,
            network=record.network.value if record.network else None,
            device_bound=False,
            session_active=False,
            entitlement_status="unknown",
            revoked=record.status is WalletPrincipalStatus.REVOKED,
            recovery_locked=record.status is WalletPrincipalStatus.RECOVERY_LOCKED,
            policy_epoch=record.policy_epoch,
        )

    def derive_principal_hash(
        self, *, principal_type: PrincipalType, wallet_identifier_commitment: str, network: WalletNetwork
    ) -> str:
        _validate_commitment(wallet_identifier_commitment, "wallet_identifier_commitment")
        payload = f"{principal_type.value}\x00{network.value}\x00{wallet_identifier_commitment}"
        return compute_hmac_lookup_hash(self.server_pepper, f"principal:{principal_type.value}", payload)

    async def _transition(
        self,
        principal_hash: str,
        new_status: WalletPrincipalStatus,
        reason_code: str,
        audit_event: str,
    ) -> PrincipalStateTransitionResult:
        record = await self.get_principal(principal_hash)
        if new_status not in _ALLOWED_TRANSITIONS[record.status]:
            self._emit_audit(
                "wallet_principal_state_transition_denied",
                record,
                proof=None,
                reason="invalid_transition",
                previous_status=record.status,
                new_status=new_status,
            )
            raise WalletPrincipalInvalidTransitionError(WalletPrincipalReasonCode.INVALID_TRANSITION.value)
        now = _now()
        updated = replace(
            record,
            status=new_status,
            updated_at=now,
            revoked_at=now if new_status is WalletPrincipalStatus.REVOKED else record.revoked_at,
            metadata={**dict(record.metadata), "last_state_reason_code": reason_code},
        )
        await self.repository.update(updated)
        await self.repository.commit()
        self._emit_audit(
            audit_event,
            updated,
            proof=None,
            reason=reason_code,
            previous_status=record.status,
            new_status=new_status,
        )
        return PrincipalStateTransitionResult(
            principal_hash=principal_hash,
            previous_status=record.status,
            new_status=new_status,
            reason_code=reason_code,
            changed=True,
        )

    def _validate_verified_proof(self, proof: VerifiedWalletProof) -> None:
        if not isinstance(proof, VerifiedWalletProof):
            raise WalletPrincipalProofRequiredError(WalletPrincipalReasonCode.PROOF_REQUIRED.value)
        if proof.proof_type not in _ALLOWED_PROOF_TYPES:
            raise WalletPrincipalProofMismatchError(WalletPrincipalReasonCode.PROOF_MISMATCH.value)
        if proof.proof_type is WalletProofType.LEGACY_MESSAGE_SIGNATURE and proof.verification_strength is not WalletVerificationStrength.COMPATIBILITY:
            raise WalletPrincipalProofMismatchError(WalletPrincipalReasonCode.PROOF_MISMATCH.value)
        if not proof.is_fresh(now=_now(), max_age_seconds=self.proof_max_age_seconds):
            raise WalletPrincipalProofRequiredError(WalletPrincipalReasonCode.PROOF_REQUIRED.value)

    def _emit_audit(
        self,
        event_type: str,
        record: WalletPrincipalRecord,
        *,
        proof: VerifiedWalletProof | None,
        reason: str,
        previous_status: WalletPrincipalStatus | None = None,
        new_status: WalletPrincipalStatus | None = None,
    ) -> None:
        if self.audit_emitter is None:
            return
        payload: dict[str, object] = {
            "principal_hash": record.principal_hash,
            "principal_type": record.principal_type.value,
            "network": record.network.value if record.network else None,
            "verification_strength": record.current_proof_strength.value,
            "reason_code": reason,
            "previous_status": previous_status.value if previous_status else None,
            "new_status": new_status.value if new_status else record.status.value,
            "policy_epoch": record.policy_epoch,
            "timestamp": _now().isoformat(),
        }
        if proof is not None:
            payload.update(
                {
                    "proof_type": proof.proof_type.value,
                    "proof_hash": proof.proof_hash,
                    "verifier_name": proof.verifier_name,
                    "verifier_version": proof.verifier_version,
                }
            )
        self.audit_emitter(event_type, payload)


def _creation_result(record: WalletPrincipalRecord, *, proof: VerifiedWalletProof, created: bool) -> PrincipalCreationResult:
    if record.last_verified_at is None:
        raise WalletPrincipalProofRequiredError(WalletPrincipalReasonCode.PROOF_REQUIRED.value)
    return PrincipalCreationResult(
        principal_hash=record.principal_hash,
        principal_type=record.principal_type,
        status=record.status,
        network=proof.network,
        proof_method=proof.proof_type,
        verification_strength=proof.verification_strength,
        highest_verified_strength=record.highest_verified_strength,
        created=created,
        last_verified_at=record.last_verified_at,
    )


def _validate_principal_hash(value: str) -> None:
    if not value.startswith("hmac-sha256:"):
        raise WalletPrincipalPrivacyViolationError(WalletPrincipalReasonCode.PRIVACY_VIOLATION.value)


def _validate_commitment(value: str, field_name: str) -> None:
    if not (value.startswith("hmac-sha256:") or value.startswith("sha256:")):
        raise WalletPrincipalPrivacyViolationError(f"{field_name}_must_be_commitment")


def _now() -> datetime:
    return datetime.now(UTC)
