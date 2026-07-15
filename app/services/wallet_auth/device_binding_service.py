"""Wallet and LNURL device binding service.

This service binds a client-generated public Device Key to an already verified
principal/proof context. It does not verify wallet signatures, LNURL callbacks,
issue PoP sessions, grant API access, or replace the Policy Engine.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from app.db.repositories.wallet_device_repository import (
    InMemoryWalletDeviceRepository,
    WalletDeviceRecord,
    WalletDeviceRepository,
    WalletDeviceRepositoryConflictError,
)
from app.domain.wallet_auth.devices import WalletDeviceBindingMethod, WalletDeviceClass, WalletDeviceStatus
from app.domain.wallet_auth.networks import WalletNetwork
from app.domain.wallet_auth.principals import WalletPrincipalStatus
from app.domain.wallet_auth.proofs import WalletProofType, WalletVerificationStrength
from app.services.wallet_auth.device_key_validation import (
    DeviceKeyFingerprintMismatchError,
    DeviceKeyInvalidError,
    NormalizedDevicePublicKey,
    validate_attestation_metadata,
    validate_device_public_key,
)
from app.services.wallet_auth.principal_types import PrincipalType, WalletPrincipalRecord
from app.services.wallet_auth.privacy_commitments import compute_hmac_lookup_hash

EventPublisher = Callable[[str, dict[str, object]], None]


class DeviceBindingError(ValueError):
    def __init__(self, reason_code: str) -> None:
        self.reason_code = reason_code
        super().__init__(reason_code)


class DeviceBindingProofRequiredError(DeviceBindingError): ...
class DeviceBindingProofExpiredError(DeviceBindingError): ...
class DeviceBindingActionMismatchError(DeviceBindingError): ...
class DevicePrincipalMismatchError(DeviceBindingError): ...
class DeviceBindingKeyInvalidError(DeviceBindingError): ...
class DeviceBindingKeyFingerprintMismatchError(DeviceBindingError): ...
class DeviceAlreadyBoundError(DeviceBindingError): ...
class DeviceBindingConflictError(DeviceBindingError): ...
class DeviceLimitExceededError(DeviceBindingError): ...
class DeviceBindingTooWeakError(DeviceBindingError): ...
class DeviceNotActiveError(DeviceBindingError): ...
class DeviceKeyRotationNotAllowedError(DeviceBindingError): ...


class PrincipalLookup(Protocol):
    async def get_principal(self, principal_hash: str) -> WalletPrincipalRecord: ...
    async def verify_principal_status(self, principal_hash: str) -> WalletPrincipalRecord: ...


class DeviceBindingRevocationChecker(Protocol):
    def is_revoked(self, *, target_type: str, target_hash: str) -> bool: ...


@dataclass(frozen=True, slots=True)
class VerifiedPrincipalProofContext:
    principal_hash: str
    principal_type: PrincipalType
    proof_type: WalletProofType
    verification_strength: WalletVerificationStrength
    proof_fingerprint: str
    challenge_id_hash: str
    intent_hash: str
    action: str
    verified_at: datetime
    expires_at: datetime
    verifier_name: str
    verifier_version: str
    network: WalletNetwork | None = None
    auth_domain: str | None = None
    policy_hash: str | None = None
    quorum_id_hash: str | None = None
    recovery_attempt_hash: str | None = None
    expected_device_key_fingerprint: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("principal_hash", "proof_fingerprint", "challenge_id_hash", "intent_hash"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not (value.startswith("hmac-sha256:") or value.startswith("sha256:")):
                raise ValueError(f"{field_name}_must_be_hash")
        if self.verified_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("device_binding_proof_time_must_be_timezone_aware")

    def is_fresh(self, *, now: datetime) -> bool:
        return self.verified_at <= now < self.expires_at


@dataclass(frozen=True, slots=True)
class DeviceRiskAssessment:
    risk_score: int
    risk_level: str
    reason_codes: tuple[str, ...]


class DeviceBindingService:
    def __init__(
        self,
        *,
        repository: WalletDeviceRepository | None = None,
        principal_lookup: PrincipalLookup,
        server_pepper: str | bytes,
        event_publisher: EventPublisher | None = None,
        revocation_checker: DeviceBindingRevocationChecker | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.repository = repository or InMemoryWalletDeviceRepository()
        self.principal_lookup = principal_lookup
        self.server_pepper = server_pepper
        self.event_publisher = event_publisher
        self.revocation_checker = revocation_checker
        self.clock = clock or (lambda: datetime.now(UTC))

    async def register_initial_device(
        self,
        *,
        proof_context: VerifiedPrincipalProofContext,
        device_public_key: str | bytes,
        key_algorithm: str = "ed25519",
        device_class: WalletDeviceClass = WalletDeviceClass.UNKNOWN,
        client_name: str | None = None,
        client_version: str | None = None,
        expected_fingerprint: str | None = None,
        max_devices: int | None = None,
        attestation_metadata: dict[str, object] | None = None,
    ) -> WalletDeviceRecord:
        method = _initial_binding_method(proof_context)
        return await self._bind_device(
            proof_context=proof_context,
            device_public_key=device_public_key,
            key_algorithm=key_algorithm,
            device_class=device_class,
            binding_method=method,
            compatible_actions={"register", "lnurl_auth_register"},
            client_name=client_name,
            client_version=client_version,
            expected_fingerprint=expected_fingerprint,
            max_devices=max_devices,
            attestation_metadata=attestation_metadata,
            event_name="lnurl_device_bound" if method is WalletDeviceBindingMethod.LNURL_AUTH_REGISTRATION else "wallet_device_bound",
        )

    async def bind_new_device(
        self,
        *,
        proof_context: VerifiedPrincipalProofContext,
        device_public_key: str | bytes,
        key_algorithm: str = "ed25519",
        device_class: WalletDeviceClass = WalletDeviceClass.UNKNOWN,
        client_name: str | None = None,
        client_version: str | None = None,
        expected_fingerprint: str | None = None,
        max_devices: int | None = None,
    ) -> WalletDeviceRecord:
        method = _new_device_binding_method(proof_context)
        return await self._bind_device(
            proof_context=proof_context,
            device_public_key=device_public_key,
            key_algorithm=key_algorithm,
            device_class=device_class,
            binding_method=method,
            compatible_actions={"new_device", "device_add", "step_up", "auth"},
            client_name=client_name,
            client_version=client_version,
            expected_fingerprint=expected_fingerprint,
            max_devices=max_devices,
            event_name="lnurl_device_bound" if method is WalletDeviceBindingMethod.LNURL_AUTH_NEW_DEVICE else "wallet_device_bound",
        )

    async def get_device(self, device_id: int) -> WalletDeviceRecord:
        record = await self.repository.get_by_id(device_id)
        if record is None:
            raise DeviceNotActiveError("wallet_device_not_found")
        return record

    async def list_devices(self, principal_hash: str, *, limit: int = 100) -> tuple[WalletDeviceRecord, ...]:
        return await self.repository.list_for_principal(principal_hash, limit=limit)

    async def record_device_activity(self, *, principal_hash: str, device_key_fingerprint: str) -> WalletDeviceRecord:
        record = await self.repository.update_last_seen(
            principal_hash=principal_hash,
            device_key_fingerprint=device_key_fingerprint,
            seen_at=self.clock(),
        )
        return record

    async def suspend_device(self, *, principal_hash: str, device_key_fingerprint: str, reason_code: str) -> WalletDeviceRecord:
        record = await self.repository.update_status(
            principal_hash=principal_hash,
            device_key_fingerprint=device_key_fingerprint,
            status=WalletDeviceStatus.SUSPENDED,
            reason_code=reason_code,
            now=self.clock(),
        )
        self._publish("wallet_device_suspended", record, reason_code=reason_code)
        return record

    async def reactivate_device(
        self,
        *,
        principal_hash: str,
        device_key_fingerprint: str,
        proof_context: VerifiedPrincipalProofContext,
    ) -> WalletDeviceRecord:
        current = await self.repository.get_by_principal_and_fingerprint(
            principal_hash=principal_hash, device_key_fingerprint=device_key_fingerprint
        )
        if current is None:
            raise DeviceNotActiveError("wallet_device_not_found")
        if current.status is WalletDeviceStatus.REVOKED:
            raise DeviceNotActiveError("wallet_device_revoked")
        self._validate_context(proof_context, compatible_actions={"step_up", "device_add", "auth"})
        record = await self.repository.update_status(
            principal_hash=principal_hash,
            device_key_fingerprint=device_key_fingerprint,
            status=WalletDeviceStatus.ACTIVE,
            reason_code="reactivated",
            now=self.clock(),
        )
        self._publish("wallet_device_reactivated", record, reason_code="reactivated")
        return record

    async def revoke_device(self, *, principal_hash: str, device_key_fingerprint: str, reason_code: str) -> WalletDeviceRecord:
        record = await self.repository.update_status(
            principal_hash=principal_hash,
            device_key_fingerprint=device_key_fingerprint,
            status=WalletDeviceStatus.REVOKED,
            reason_code=reason_code,
            now=self.clock(),
        )
        self._publish("wallet_device_revoked", record, reason_code=reason_code)
        return record

    async def rotate_device_key(
        self,
        *,
        principal_hash: str,
        old_device_key_fingerprint: str,
        new_device_public_key: str | bytes,
        proof_context: VerifiedPrincipalProofContext,
        key_algorithm: str = "ed25519",
    ) -> WalletDeviceRecord:
        if proof_context.action not in {"device_key_rotate", "trusted_device_key_rotation", "step_up", "auth"}:
            raise DeviceKeyRotationNotAllowedError("device_key_rotation_action_mismatch")
        self._validate_context(proof_context, compatible_actions={proof_context.action})
        current = await self.assert_device_active(
            principal_hash=principal_hash, device_key_fingerprint=old_device_key_fingerprint
        )
        normalized = self._validate_key(new_device_public_key, key_algorithm=key_algorithm)
        if self.revocation_checker and self.revocation_checker.is_revoked(
            target_type="wallet_device_key", target_hash=normalized.fingerprint
        ):
            raise DeviceKeyRotationNotAllowedError("device_key_revoked_fingerprint_reuse")
        record = await self.repository.rotate_key(
            principal_hash=principal_hash,
            old_fingerprint=current.device_key_fingerprint,
            new_fingerprint=normalized.fingerprint,
            new_public_key_b64=normalized.public_key_b64,
            key_algorithm=normalized.algorithm,
            now=self.clock(),
        )
        self._publish("wallet_device_key_rotated", record, reason_code="key_rotated")
        return record

    async def assert_device_active(self, *, principal_hash: str, device_key_fingerprint: str) -> WalletDeviceRecord:
        record = await self.repository.get_by_principal_and_fingerprint(
            principal_hash=principal_hash, device_key_fingerprint=device_key_fingerprint
        )
        if record is None:
            raise DeviceNotActiveError("wallet_device_not_found")
        if record.status is not WalletDeviceStatus.ACTIVE:
            raise DeviceNotActiveError(f"wallet_device_{record.status.value}")
        return record

    async def evaluate_binding_eligibility(
        self,
        *,
        proof_context: VerifiedPrincipalProofContext,
        device_class: WalletDeviceClass,
        binding_method: WalletDeviceBindingMethod,
    ) -> DeviceRiskAssessment:
        principal = await self.principal_lookup.get_principal(proof_context.principal_hash)
        return _risk_assessment(
            principal=principal,
            proof_context=proof_context,
            device_class=device_class,
            binding_method=binding_method,
        )

    async def _bind_device(
        self,
        *,
        proof_context: VerifiedPrincipalProofContext,
        device_public_key: str | bytes,
        key_algorithm: str,
        device_class: WalletDeviceClass,
        binding_method: WalletDeviceBindingMethod,
        compatible_actions: set[str],
        client_name: str | None,
        client_version: str | None,
        expected_fingerprint: str | None,
        max_devices: int | None,
        event_name: str,
        attestation_metadata: dict[str, object] | None = None,
    ) -> WalletDeviceRecord:
        self._publish_raw("wallet_device_binding_requested", proof_context, binding_method=binding_method, reason_code="requested")
        self._validate_context(proof_context, compatible_actions=compatible_actions)
        principal = await self.principal_lookup.verify_principal_status(proof_context.principal_hash)
        if principal.principal_hash != proof_context.principal_hash or principal.principal_type is not proof_context.principal_type:
            raise DevicePrincipalMismatchError("device_principal_mismatch")
        normalized = self._validate_key(
            device_public_key,
            key_algorithm=key_algorithm,
            expected_fingerprint=expected_fingerprint or proof_context.expected_device_key_fingerprint,
        )
        _validate_strength_for_device(proof_context, device_class=device_class, binding_method=binding_method)
        if max_devices is not None and await self.repository.count_active_devices(principal.principal_hash) >= max_devices:
            raise DeviceLimitExceededError("device_limit_exceeded")
        risk = _risk_assessment(
            principal=principal,
            proof_context=proof_context,
            device_class=device_class,
            binding_method=binding_method,
        )
        now = self.clock()
        device_id_hash = compute_hmac_lookup_hash(
            self.server_pepper,
            "wallet_device_id",
            f"{principal.principal_hash}\x00{normalized.fingerprint}",
        )
        record = WalletDeviceRecord(
            id=0,
            principal_hash=principal.principal_hash,
            device_id_hash=device_id_hash,
            device_key_fingerprint=normalized.fingerprint,
            device_public_key_b64=normalized.public_key_b64,
            key_algorithm=normalized.algorithm,
            device_class=device_class,
            binding_method=binding_method,
            proof_type=proof_context.proof_type,
            verification_strength=proof_context.verification_strength,
            status=WalletDeviceStatus.ACTIVE,
            risk_score=risk.risk_score,
            risk_level=risk.risk_level,
            risk_reason_codes=risk.reason_codes,
            network=proof_context.network,
            auth_domain=proof_context.auth_domain,
            client_name=_sanitize_client_text(client_name),
            client_version=_sanitize_client_text(client_version),
            first_seen_at=now,
            last_seen_at=now,
            last_proof_at=proof_context.verified_at,
            created_at=now,
            updated_at=now,
            metadata={
                "challenge_id_hash": proof_context.challenge_id_hash,
                "intent_hash": proof_context.intent_hash,
                "policy_hash": proof_context.policy_hash,
                "verifier_name": proof_context.verifier_name,
                "verifier_version": proof_context.verifier_version,
                "attestation": validate_attestation_metadata(attestation_metadata),
            },
        )
        try:
            created = await self.repository.create_device(record)
            await self.repository.commit()
        except WalletDeviceRepositoryConflictError as exc:
            await self.repository.rollback()
            self._publish_raw("wallet_device_binding_failed", proof_context, binding_method=binding_method, reason_code=str(exc))
            raise DeviceBindingConflictError("device_binding_conflict") from exc
        self._publish(event_name, created, reason_code="bound")
        return created

    def _validate_key(
        self,
        device_public_key: str | bytes,
        *,
        key_algorithm: str,
        expected_fingerprint: str | None = None,
    ) -> NormalizedDevicePublicKey:
        try:
            return validate_device_public_key(
                device_public_key,
                algorithm=key_algorithm,
                expected_fingerprint=expected_fingerprint,
            )
        except DeviceKeyFingerprintMismatchError as exc:
            raise DeviceBindingKeyFingerprintMismatchError("device_key_fingerprint_mismatch") from exc
        except DeviceKeyInvalidError as exc:
            raise DeviceBindingKeyInvalidError(str(exc)) from exc

    def _validate_context(self, proof_context: VerifiedPrincipalProofContext, *, compatible_actions: set[str]) -> None:
        now = self.clock()
        if not proof_context.is_fresh(now=now):
            raise DeviceBindingProofExpiredError("device_binding_proof_expired")
        if proof_context.action not in compatible_actions:
            raise DeviceBindingActionMismatchError("device_binding_action_mismatch")
        if self.revocation_checker:
            for target_type, target_hash in (
                ("wallet_proof", proof_context.proof_fingerprint),
                ("wallet_challenge", proof_context.challenge_id_hash),
            ):
                if self.revocation_checker.is_revoked(target_type=target_type, target_hash=target_hash):
                    raise DeviceBindingProofRequiredError("device_binding_proof_revoked_or_reused")

    def _publish(self, event_type: str, record: WalletDeviceRecord, *, reason_code: str) -> None:
        if self.event_publisher is None:
            return
        self.event_publisher(
            event_type,
            {
                "principal_hash": record.principal_hash,
                "device_id_hash": record.device_id_hash,
                "device_key_fingerprint": record.device_key_fingerprint,
                "device_class": record.device_class.value,
                "binding_method": record.binding_method.value,
                "proof_type": record.proof_type.value,
                "verification_strength": record.verification_strength.value,
                "reason_code": reason_code,
                "occurred_at": self.clock().isoformat(),
            },
        )

    def _publish_raw(
        self,
        event_type: str,
        context: VerifiedPrincipalProofContext,
        *,
        binding_method: WalletDeviceBindingMethod,
        reason_code: str,
    ) -> None:
        if self.event_publisher is None:
            return
        self.event_publisher(
            event_type,
            {
                "principal_hash": context.principal_hash,
                "device_key_fingerprint": context.expected_device_key_fingerprint,
                "binding_method": binding_method.value,
                "proof_type": context.proof_type.value,
                "verification_strength": context.verification_strength.value,
                "reason_code": reason_code,
                "occurred_at": self.clock().isoformat(),
            },
        )


def _initial_binding_method(context: VerifiedPrincipalProofContext) -> WalletDeviceBindingMethod:
    if context.proof_type is WalletProofType.LNURL_AUTH or context.principal_type is PrincipalType.LIGHTNING_WALLET_PRINCIPAL:
        return WalletDeviceBindingMethod.LNURL_AUTH_REGISTRATION
    return WalletDeviceBindingMethod.WALLET_PROOF_REGISTRATION


def _new_device_binding_method(context: VerifiedPrincipalProofContext) -> WalletDeviceBindingMethod:
    if context.proof_type is WalletProofType.LNURL_AUTH or context.principal_type is PrincipalType.LIGHTNING_WALLET_PRINCIPAL:
        return WalletDeviceBindingMethod.LNURL_AUTH_NEW_DEVICE
    return WalletDeviceBindingMethod.WALLET_PROOF_NEW_DEVICE


def _validate_strength_for_device(
    context: VerifiedPrincipalProofContext,
    *,
    device_class: WalletDeviceClass,
    binding_method: WalletDeviceBindingMethod,
) -> None:
    if context.verification_strength is WalletVerificationStrength.COMPATIBILITY:
        if device_class in {WalletDeviceClass.HARDWARE_WALLET, WalletDeviceClass.PAYREGISTER_DEVICE, WalletDeviceClass.SERVER_BOT}:
            raise DeviceBindingTooWeakError("device_binding_too_weak")
        if binding_method in {
            WalletDeviceBindingMethod.RECOVERY_CAPSULE_RESTORE,
            WalletDeviceBindingMethod.MULTISIG_QUORUM_APPROVAL,
            WalletDeviceBindingMethod.ACCESS_CERTIFICATE_BRIDGE,
        }:
            raise DeviceBindingTooWeakError("device_binding_too_weak")
    if context.verification_strength is WalletVerificationStrength.SOVEREIGN and not (
        context.quorum_id_hash or context.recovery_attempt_hash
    ):
        raise DeviceBindingTooWeakError("device_binding_sovereign_context_required")


def _risk_assessment(
    *,
    principal: WalletPrincipalRecord,
    proof_context: VerifiedPrincipalProofContext,
    device_class: WalletDeviceClass,
    binding_method: WalletDeviceBindingMethod,
) -> DeviceRiskAssessment:
    score = 35
    reasons: list[str] = []
    if principal.status is WalletPrincipalStatus.ACTIVE:
        score -= 5
        reasons.append("principal_active")
    if proof_context.verification_strength in {WalletVerificationStrength.HIGH_ASSURANCE, WalletVerificationStrength.SOVEREIGN}:
        score -= 10
        reasons.append("fresh_high_assurance_proof")
    if proof_context.verification_strength is WalletVerificationStrength.COMPATIBILITY:
        score += 25
        reasons.append("compatibility_proof")
    if device_class is WalletDeviceClass.UNKNOWN:
        score += 15
        reasons.append("unknown_device_class")
    if device_class is WalletDeviceClass.BROWSER_EXTENSION:
        score += 10
        reasons.append("browser_extension_not_root_of_trust")
    if binding_method is WalletDeviceBindingMethod.RECOVERY_CAPSULE_RESTORE:
        score += 20
        reasons.append("recovery_flow")
    remaining = proof_context.expires_at - datetime.now(UTC)
    if remaining < timedelta(seconds=30):
        score += 10
        reasons.append("proof_near_expiry")
    bounded = max(0, min(100, score))
    level = "low" if bounded < 35 else "medium" if bounded < 70 else "high"
    return DeviceRiskAssessment(risk_score=bounded, risk_level=level, reason_codes=tuple(reasons))


def _sanitize_client_text(value: str | None) -> str | None:
    if value is None:
        return None
    sanitized = "".join(ch for ch in value.strip() if ch.isprintable())[:80]
    return sanitized or None
