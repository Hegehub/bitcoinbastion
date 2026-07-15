"""Wallet Proof-of-Possession session orchestration.

This module is the wallet-auth adapter around Bastion's Proof-of-Access session
model. It intentionally does not verify wallet signatures, LNURL callbacks, or
per-request PoP signatures. It creates short-lived, policy-approved session
handles that are only lookup identifiers; protected requests still need Prompt
18 request-signature verification with the stored session public key.
"""

from __future__ import annotations

import secrets
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.wallet_auth import WalletDevice, WalletPrincipal, WalletSession
from app.db.repositories.wallet_device_repository import WalletDeviceRecord
from app.domain.wallet_auth.devices import WalletDeviceStatus
from app.domain.wallet_auth.principals import WalletPrincipalStatus
from app.domain.wallet_auth.proofs import WalletProofType, WalletVerificationStrength
from app.domain.wallet_auth.sessions import WalletSessionStatus
from app.services.wallet_auth.device_key_validation import (
    DeviceKeyInvalidError,
    NormalizedDevicePublicKey,
    constant_time_fingerprint_equal,
    detect_forbidden_private_material,
    validate_device_public_key,
)
from app.services.wallet_auth.principal_types import PrincipalType, WalletPrincipalRecord
from app.services.access.crypto.hashing import sha256_prefixed
from app.services.wallet_auth.privacy_commitments import compute_hmac_lookup_hash

AuditEmitter = Callable[[str, dict[str, object]], None]
Clock = Callable[[], datetime]

DEFAULT_WALLET_SESSION_TTL_SECONDS = 900
MAX_WALLET_SESSION_TTL_SECONDS = 1800
HIGH_RISK_WALLET_SESSION_TTL_SECONDS = 300
RECOVERY_WALLET_SESSION_TTL_SECONDS = 300
COMPATIBILITY_WALLET_SESSION_TTL_SECONDS = 300
DEFAULT_MAX_ACTIVE_SESSIONS_PER_DEVICE = 3
DEFAULT_MAX_ACTIVE_SESSIONS_PER_PRINCIPAL = 5
SESSION_TOKEN_ENTROPY_BYTES = 48
SESSION_TOKEN_PREFIX = "sess_"


class WalletSessionReasonCode(StrEnum):
    INVALID_AUTH_CONTEXT = "wallet_session_invalid_auth_context"
    PRINCIPAL_INACTIVE = "wallet_session_principal_inactive"
    DEVICE_INACTIVE = "wallet_session_device_inactive"
    CHALLENGE_EXPIRED = "wallet_session_challenge_expired"
    CHALLENGE_USED = "wallet_session_challenge_used"
    ORIGIN_MISMATCH = "wallet_session_origin_mismatch"
    KEY_BINDING_MISMATCH = "wallet_session_key_binding_mismatch"
    ENTITLEMENT_INACTIVE = "wallet_session_entitlement_inactive"
    SCOPE_NOT_ALLOWED = "wallet_session_scope_not_allowed"
    POLICY_DENIED = "wallet_session_policy_denied"
    STEP_UP_REQUIRED = "wallet_session_step_up_required"
    LIMIT_REACHED = "wallet_session_limit_reached"
    LOCKDOWN_ACTIVE = "wallet_session_lockdown_active"
    REVOKED = "wallet_session_revoked"
    EXPIRED = "wallet_session_expired"
    TOKEN_FIXATION_REJECTED = "wallet_session_fixation_rejected"
    PRIVATE_KEY_REJECTED = "wallet_session_private_key_rejected"


class WalletSessionError(ValueError):
    """Safe session error carrying only a stable reason code."""

    def __init__(self, reason_code: str | WalletSessionReasonCode) -> None:
        self.reason_code = str(reason_code)
        super().__init__(self.reason_code)


class WalletSessionPolicyError(WalletSessionError): ...
class WalletSessionStateError(WalletSessionError): ...
class WalletSessionKeyBindingError(WalletSessionError): ...
class WalletSessionChallengeError(WalletSessionError): ...
class WalletSessionLimitError(WalletSessionError): ...


@dataclass(frozen=True, slots=True)
class EntitlementSnapshot:
    active: bool
    entitlement_id: str | None
    effective_plan: str
    allowed_scopes: tuple[str, ...]
    expires_at: datetime | None = None

    def allows(self, requested_scopes: Sequence[str]) -> bool:
        if "*" in self.allowed_scopes:
            return True
        return set(requested_scopes).issubset(set(self.allowed_scopes))


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    decision: str
    decision_hash: str
    reason_code: str = "policy_allow"

    @property
    def allowed(self) -> bool:
        return self.decision == "allow"


@dataclass(frozen=True, slots=True)
class VerifiedWalletAuthenticationContext:
    """Trusted input produced by verifier, principal, device, and challenge services."""

    principal_hash: str
    principal_type: PrincipalType
    principal_status: WalletPrincipalStatus
    proof_fingerprint: str
    proof_type: WalletProofType
    verification_strength: WalletVerificationStrength
    proof_verified_at: datetime
    challenge_id: str
    challenge_hash: str
    challenge_action: str
    challenge_origin: str
    challenge_used: bool
    device_binding_id: int
    device_key_fingerprint: str
    device_status: WalletDeviceStatus
    device_risk_score: int
    requested_scopes: tuple[str, ...]
    auth_method: str
    policy_hash: str
    policy_epoch: int
    crypto_epoch: int
    origin: str
    expected_session_public_key_fingerprint: str
    expected_device_key_fingerprint: str | None = None
    network: str | None = None
    entitlement_required: bool = True
    recovery_only_requested: bool = False
    access_certificate_fingerprint: str | None = None
    proof_expires_at: datetime | None = None

    def __post_init__(self) -> None:
        _require_hash(self.principal_hash, "principal_hash")
        _require_hash(self.proof_fingerprint, "proof_fingerprint")
        _require_hash(self.challenge_hash, "challenge_hash")
        _require_hash(self.expected_session_public_key_fingerprint, "expected_session_public_key_fingerprint")
        if self.expected_device_key_fingerprint is not None:
            _require_hash(self.expected_device_key_fingerprint, "expected_device_key_fingerprint")
        if self.proof_verified_at.tzinfo is None:
            raise ValueError("wallet_session_proof_verified_at_timezone_required")
        if self.proof_expires_at is not None and self.proof_expires_at.tzinfo is None:
            raise ValueError("wallet_session_proof_expires_at_timezone_required")
        if self.device_binding_id <= 0:
            raise ValueError("wallet_session_device_binding_required")


@dataclass(frozen=True, slots=True)
class WalletSessionRecord:
    session_lookup_hash: str
    principal_hash: str
    principal_type: PrincipalType
    device_binding_id: int
    device_key_fingerprint: str
    session_public_key_b64: str
    session_public_key_fingerprint: str
    session_signature_algorithm: str
    auth_method: str
    verification_strength: WalletVerificationStrength
    entitlement_id: str | None
    effective_plan: str
    effective_scopes: tuple[str, ...]
    policy_hash: str
    policy_decision_hash: str
    policy_epoch: int
    crypto_epoch: int
    challenge_id: str
    challenge_hash: str
    proof_fingerprint: str
    origin: str
    status: WalletSessionStatus
    issued_at: datetime
    expires_at: datetime
    last_seen_at: datetime | None = None
    revoked_at: datetime | None = None
    frozen_at: datetime | None = None
    revocation_reason_code: str | None = None
    risk_snapshot: Mapping[str, object] = field(default_factory=dict)
    metadata: Mapping[str, object] = field(default_factory=dict)

    def safe_context(self) -> WalletSessionContext:
        return WalletSessionContext(
            session_lookup_hash=self.session_lookup_hash,
            principal_hash=self.principal_hash,
            principal_type=self.principal_type,
            device_binding_id=self.device_binding_id,
            device_key_fingerprint=self.device_key_fingerprint,
            session_public_key_b64=self.session_public_key_b64,
            session_public_key_fingerprint=self.session_public_key_fingerprint,
            auth_method=self.auth_method,
            verification_strength=self.verification_strength,
            effective_plan=self.effective_plan,
            effective_scopes=self.effective_scopes,
            entitlement_id=self.entitlement_id,
            policy_hash=self.policy_hash,
            policy_epoch=self.policy_epoch,
            crypto_epoch=self.crypto_epoch,
            origin=self.origin,
            risk_snapshot=dict(self.risk_snapshot),
            issued_at=self.issued_at,
            expires_at=self.expires_at,
            session_status=self.status,
            requires_request_signature=True,
        )


@dataclass(frozen=True, slots=True)
class WalletSessionContext:
    session_lookup_hash: str
    principal_hash: str
    principal_type: PrincipalType
    device_binding_id: int
    device_key_fingerprint: str
    session_public_key_b64: str
    session_public_key_fingerprint: str
    auth_method: str
    verification_strength: WalletVerificationStrength
    effective_plan: str
    effective_scopes: tuple[str, ...]
    entitlement_id: str | None
    policy_hash: str
    policy_epoch: int
    crypto_epoch: int
    origin: str
    risk_snapshot: dict[str, object]
    issued_at: datetime
    expires_at: datetime
    session_status: WalletSessionStatus
    requires_request_signature: bool


@dataclass(frozen=True, slots=True)
class WalletSessionCreationResult:
    session_token: str
    token_type: str
    expires_at: datetime
    principal_pseudonym: str
    device_fingerprint: str
    session_public_key_fingerprint: str
    effective_plan: str
    effective_scopes: tuple[str, ...]
    policy_mode: str
    requires_request_signature: bool
    request_signature_algorithm: str
    server_time: datetime
    warning: str
    context: WalletSessionContext

    def safe_summary(self) -> dict[str, object]:
        return {
            "token_type": self.token_type,
            "expires_at": self.expires_at.isoformat(),
            "principal_pseudonym": self.principal_pseudonym,
            "device_fingerprint": self.device_fingerprint,
            "session_public_key_fingerprint": self.session_public_key_fingerprint,
            "effective_plan": self.effective_plan,
            "effective_scopes": list(self.effective_scopes),
            "requires_request_signature": self.requires_request_signature,
            "warning": self.warning,
        }


class WalletSessionRepository(Protocol):
    async def create(self, record: WalletSessionRecord) -> WalletSessionRecord: ...
    async def get_by_lookup_hash(self, session_lookup_hash: str) -> WalletSessionRecord | None: ...
    async def list_active_for_principal(self, principal_hash: str) -> tuple[WalletSessionRecord, ...]: ...
    async def list_active_for_device(self, principal_hash: str, device_key_fingerprint: str) -> tuple[WalletSessionRecord, ...]: ...
    async def update(self, record: WalletSessionRecord) -> WalletSessionRecord: ...
    async def freeze_for_principal(self, principal_hash: str, *, now: datetime, reason_code: str) -> int: ...
    async def freeze_for_device(self, principal_hash: str, device_key_fingerprint: str, *, now: datetime, reason_code: str) -> int: ...
    async def expire_stale(self, *, now: datetime) -> int: ...


class PrincipalLookup(Protocol):
    async def get_principal(self, principal_hash: str) -> WalletPrincipalRecord: ...
    async def verify_principal_status(self, principal_hash: str) -> WalletPrincipalRecord: ...


class DeviceLookup(Protocol):
    async def assert_device_active(self, *, principal_hash: str, device_key_fingerprint: str) -> WalletDeviceRecord: ...


class WalletChallengeConsumer(Protocol):
    async def consume_for_session(self, *, challenge_id: str, challenge_hash: str, origin: str) -> None: ...


class WalletSessionPolicyEngine(Protocol):
    async def decide_session_create(self, context: Mapping[str, object]) -> PolicyDecision: ...


class WalletSessionEntitlementService(Protocol):
    async def get_entitlement_for_principal(self, principal_hash: str) -> EntitlementSnapshot: ...


class WalletSessionRevocationChecker(Protocol):
    def is_revoked(self, *, target_type: str, target_hash: str) -> bool: ...


class InMemoryWalletSessionRepository:
    """Thread-safe repository used by tests and local orchestration."""

    def __init__(self) -> None:
        self._records: dict[str, WalletSessionRecord] = {}
        self._lock = threading.RLock()

    async def create(self, record: WalletSessionRecord) -> WalletSessionRecord:
        with self._lock:
            if record.session_lookup_hash in self._records:
                raise WalletSessionError("wallet_session_repository_conflict")
            self._records[record.session_lookup_hash] = record
            return record

    async def get_by_lookup_hash(self, session_lookup_hash: str) -> WalletSessionRecord | None:
        with self._lock:
            return self._records.get(session_lookup_hash)

    async def list_active_for_principal(self, principal_hash: str) -> tuple[WalletSessionRecord, ...]:
        with self._lock:
            return tuple(
                record for record in self._records.values() if record.principal_hash == principal_hash and record.status is WalletSessionStatus.ACTIVE
            )

    async def list_active_for_device(self, principal_hash: str, device_key_fingerprint: str) -> tuple[WalletSessionRecord, ...]:
        with self._lock:
            return tuple(
                record
                for record in self._records.values()
                if record.principal_hash == principal_hash
                and record.device_key_fingerprint == device_key_fingerprint
                and record.status is WalletSessionStatus.ACTIVE
            )

    async def update(self, record: WalletSessionRecord) -> WalletSessionRecord:
        with self._lock:
            if record.session_lookup_hash not in self._records:
                raise WalletSessionStateError("wallet_session_not_found")
            self._records[record.session_lookup_hash] = record
            return record

    async def freeze_for_principal(self, principal_hash: str, *, now: datetime, reason_code: str) -> int:
        with self._lock:
            count = 0
            for key, record in tuple(self._records.items()):
                if record.principal_hash == principal_hash and record.status is WalletSessionStatus.ACTIVE:
                    self._records[key] = replace(record, status=WalletSessionStatus.FROZEN, frozen_at=now, revocation_reason_code=reason_code)
                    count += 1
            return count

    async def freeze_for_device(self, principal_hash: str, device_key_fingerprint: str, *, now: datetime, reason_code: str) -> int:
        with self._lock:
            count = 0
            for key, record in tuple(self._records.items()):
                if (
                    record.principal_hash == principal_hash
                    and record.device_key_fingerprint == device_key_fingerprint
                    and record.status is WalletSessionStatus.ACTIVE
                ):
                    self._records[key] = replace(record, status=WalletSessionStatus.FROZEN, frozen_at=now, revocation_reason_code=reason_code)
                    count += 1
            return count

    async def expire_stale(self, *, now: datetime) -> int:
        with self._lock:
            count = 0
            for key, record in tuple(self._records.items()):
                if record.status is WalletSessionStatus.ACTIVE and record.expires_at <= now:
                    self._records[key] = replace(record, status=WalletSessionStatus.EXPIRED)
                    count += 1
            return count



class SqlAlchemyWalletSessionRepository:
    """SQLAlchemy adapter for the canonical wallet_sessions table.

    The adapter stores the lookup hash and public verification material only;
    raw session tokens and private keys never enter the database model.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    async def create(self, record: WalletSessionRecord) -> WalletSessionRecord:
        principal = self.db.scalar(select(WalletPrincipal).where(WalletPrincipal.principal_hash == record.principal_hash))
        device = self.db.scalar(
            select(WalletDevice).where(
                WalletDevice.principal_hash == record.principal_hash,
                WalletDevice.device_key_fingerprint == record.device_key_fingerprint,
            )
        )
        if principal is None or device is None:
            raise WalletSessionStateError("wallet_session_principal_or_device_not_found")
        model = WalletSession(
            principal_id=principal.id,
            principal_hash=record.principal_hash,
            device_id=device.id,
            device_key_fingerprint=record.device_key_fingerprint,
            session_hash=record.session_lookup_hash,
            session_public_key_fingerprint=record.session_public_key_fingerprint,
            status=record.status.value,
            auth_method=record.auth_method,
            verification_strength=record.verification_strength.value,
            scopes_json=list(record.effective_scopes),
            policy_context_json={
                "policy_hash": record.policy_hash,
                "policy_decision_hash": record.policy_decision_hash,
                "policy_epoch": record.policy_epoch,
                "crypto_epoch": record.crypto_epoch,
                "origin": record.origin,
                "risk_snapshot": dict(record.risk_snapshot),
                "entitlement_id": record.entitlement_id,
                "effective_plan": record.effective_plan,
                "session_signature_algorithm": record.session_signature_algorithm,
                "requires_request_signature": True,
            },
            issued_at=record.issued_at,
            expires_at=record.expires_at,
            revoked_at=record.revoked_at,
            frozen_at=record.frozen_at,
            last_seen_at=record.last_seen_at,
            metadata_json={
                **dict(record.metadata),
                "session_public_key_b64": record.session_public_key_b64,
                "principal_type": record.principal_type.value,
                "challenge_id": record.challenge_id,
                "challenge_hash": record.challenge_hash,
                "proof_fingerprint": record.proof_fingerprint,
                "revocation_reason_code": record.revocation_reason_code,
            },
        )
        self.db.add(model)
        self.db.flush()
        return record

    async def get_by_lookup_hash(self, session_lookup_hash: str) -> WalletSessionRecord | None:
        model = self.db.scalar(select(WalletSession).where(WalletSession.session_hash == session_lookup_hash))
        return _record_from_model(model) if model is not None else None

    async def list_active_for_principal(self, principal_hash: str) -> tuple[WalletSessionRecord, ...]:
        models = self.db.scalars(
            select(WalletSession).where(WalletSession.principal_hash == principal_hash, WalletSession.status == WalletSessionStatus.ACTIVE.value)
        ).all()
        return tuple(_record_from_model(model) for model in models)

    async def list_active_for_device(self, principal_hash: str, device_key_fingerprint: str) -> tuple[WalletSessionRecord, ...]:
        models = self.db.scalars(
            select(WalletSession).where(
                WalletSession.principal_hash == principal_hash,
                WalletSession.device_key_fingerprint == device_key_fingerprint,
                WalletSession.status == WalletSessionStatus.ACTIVE.value,
            )
        ).all()
        return tuple(_record_from_model(model) for model in models)

    async def update(self, record: WalletSessionRecord) -> WalletSessionRecord:
        model = self.db.scalar(select(WalletSession).where(WalletSession.session_hash == record.session_lookup_hash))
        if model is None:
            raise WalletSessionStateError("wallet_session_not_found")
        _apply_record_to_model(record, model)
        self.db.flush()
        return record

    async def freeze_for_principal(self, principal_hash: str, *, now: datetime, reason_code: str) -> int:
        models = self.db.scalars(
            select(WalletSession).where(WalletSession.principal_hash == principal_hash, WalletSession.status == WalletSessionStatus.ACTIVE.value)
        ).all()
        for model in models:
            model.status = WalletSessionStatus.FROZEN.value
            model.frozen_at = now
            model.metadata_json = {**(model.metadata_json or {}), "revocation_reason_code": reason_code}
        self.db.flush()
        return len(models)

    async def freeze_for_device(self, principal_hash: str, device_key_fingerprint: str, *, now: datetime, reason_code: str) -> int:
        models = self.db.scalars(
            select(WalletSession).where(
                WalletSession.principal_hash == principal_hash,
                WalletSession.device_key_fingerprint == device_key_fingerprint,
                WalletSession.status == WalletSessionStatus.ACTIVE.value,
            )
        ).all()
        for model in models:
            model.status = WalletSessionStatus.FROZEN.value
            model.frozen_at = now
            model.metadata_json = {**(model.metadata_json or {}), "revocation_reason_code": reason_code}
        self.db.flush()
        return len(models)

    async def expire_stale(self, *, now: datetime) -> int:
        models = self.db.scalars(
            select(WalletSession).where(WalletSession.status == WalletSessionStatus.ACTIVE.value, WalletSession.expires_at <= now)
        ).all()
        for model in models:
            model.status = WalletSessionStatus.EXPIRED.value
        self.db.flush()
        return len(models)

class WalletSessionService:
    def __init__(
        self,
        *,
        repository: WalletSessionRepository | None = None,
        principal_lookup: PrincipalLookup,
        device_lookup: DeviceLookup,
        challenge_consumer: WalletChallengeConsumer,
        policy_engine: WalletSessionPolicyEngine,
        entitlement_service: WalletSessionEntitlementService | None = None,
        revocation_checker: WalletSessionRevocationChecker | None = None,
        audit_chain: AuditEmitter | None = None,
        server_pepper: str | bytes,
        clock: Clock | None = None,
        default_ttl_seconds: int = DEFAULT_WALLET_SESSION_TTL_SECONDS,
        max_ttl_seconds: int = MAX_WALLET_SESSION_TTL_SECONDS,
        max_active_sessions_per_device: int = DEFAULT_MAX_ACTIVE_SESSIONS_PER_DEVICE,
        max_active_sessions_per_principal: int = DEFAULT_MAX_ACTIVE_SESSIONS_PER_PRINCIPAL,
    ) -> None:
        if not server_pepper:
            raise ValueError("wallet_session_server_pepper_required")
        self.repository = repository or InMemoryWalletSessionRepository()
        self.principal_lookup = principal_lookup
        self.device_lookup = device_lookup
        self.challenge_consumer = challenge_consumer
        self.policy_engine = policy_engine
        self.entitlement_service = entitlement_service
        self.revocation_checker = revocation_checker
        self.audit_chain = audit_chain
        self.server_pepper = server_pepper
        self.clock = clock or (lambda: datetime.now(UTC))
        self.default_ttl_seconds = default_ttl_seconds
        self.max_ttl_seconds = max_ttl_seconds
        self.max_active_sessions_per_device = max_active_sessions_per_device
        self.max_active_sessions_per_principal = max_active_sessions_per_principal

    async def create_session(
        self,
        *,
        auth_context: VerifiedWalletAuthenticationContext,
        session_public_key: str | bytes,
        session_key_algorithm: str = "ed25519",
        requested_ttl_seconds: int | None = None,
        client_supplied_token: str | None = None,
    ) -> WalletSessionCreationResult:
        now = self._now()
        if client_supplied_token is not None:
            self._emit("wallet_session_creation_denied", reason_code=WalletSessionReasonCode.TOKEN_FIXATION_REJECTED.value, principal_hash=auth_context.principal_hash)
            raise WalletSessionKeyBindingError(WalletSessionReasonCode.TOKEN_FIXATION_REJECTED)
        normalized_session_key = self._validate_session_public_key(
            session_public_key, algorithm=session_key_algorithm, expected_fingerprint=auth_context.expected_session_public_key_fingerprint
        )
        await self.assert_session_can_be_created(auth_context=auth_context, session_key=normalized_session_key, now=now)
        principal = await self.principal_lookup.verify_principal_status(auth_context.principal_hash)
        device = await self.device_lookup.assert_device_active(
            principal_hash=auth_context.principal_hash, device_key_fingerprint=auth_context.device_key_fingerprint
        )
        entitlement = await self._resolve_entitlement(auth_context)
        await self._enforce_session_limits(auth_context.principal_hash, auth_context.device_key_fingerprint)
        policy_decision = await self.policy_engine.decide_session_create(
            self._policy_input(auth_context=auth_context, device=device, entitlement=entitlement, active_principal=principal)
        )
        if not policy_decision.allowed:
            event = "wallet_session_creation_step_up_required" if policy_decision.decision == "step_up_required" else "wallet_session_creation_denied"
            self._emit(event, principal_hash=auth_context.principal_hash, device_key_fingerprint=auth_context.device_key_fingerprint, reason_code=policy_decision.reason_code)
            if policy_decision.decision == "step_up_required":
                raise WalletSessionPolicyError(WalletSessionReasonCode.STEP_UP_REQUIRED)
            raise WalletSessionPolicyError(WalletSessionReasonCode.POLICY_DENIED)

        await self.challenge_consumer.consume_for_session(
            challenge_id=auth_context.challenge_id, challenge_hash=auth_context.challenge_hash, origin=auth_context.origin
        )
        token = _generate_session_token()
        lookup_hash = self._hash_session_token(token)
        expires_at = self._compute_expiry(auth_context=auth_context, entitlement=entitlement, requested_ttl_seconds=requested_ttl_seconds, now=now)
        status = WalletSessionStatus.RECOVERY_ONLY if auth_context.recovery_only_requested else WalletSessionStatus.ACTIVE
        record = WalletSessionRecord(
            session_lookup_hash=lookup_hash,
            principal_hash=auth_context.principal_hash,
            principal_type=auth_context.principal_type,
            device_binding_id=auth_context.device_binding_id,
            device_key_fingerprint=auth_context.device_key_fingerprint,
            session_public_key_b64=normalized_session_key.public_key_b64,
            session_public_key_fingerprint=normalized_session_key.fingerprint,
            session_signature_algorithm=normalized_session_key.algorithm,
            auth_method=auth_context.auth_method,
            verification_strength=auth_context.verification_strength,
            entitlement_id=entitlement.entitlement_id,
            effective_plan=entitlement.effective_plan,
            effective_scopes=tuple(sorted(auth_context.requested_scopes)),
            policy_hash=auth_context.policy_hash,
            policy_decision_hash=policy_decision.decision_hash,
            policy_epoch=auth_context.policy_epoch,
            crypto_epoch=auth_context.crypto_epoch,
            challenge_id=auth_context.challenge_id,
            challenge_hash=auth_context.challenge_hash,
            proof_fingerprint=auth_context.proof_fingerprint,
            origin=auth_context.origin,
            status=status,
            issued_at=now,
            expires_at=expires_at,
            risk_snapshot={"device_risk_score": auth_context.device_risk_score, "device_risk_level": device.risk_level},
            metadata={
                "token_type": "PoP",
                "requires_request_signature": True,
                "proof_type": auth_context.proof_type.value,
                "challenge_action": auth_context.challenge_action,
                "access_certificate_fingerprint": auth_context.access_certificate_fingerprint,
            },
        )
        await self.repository.create(record)
        self._emit(
            "wallet_session_created",
            principal_hash=record.principal_hash,
            device_key_fingerprint=record.device_key_fingerprint,
            session_fingerprint=_fingerprint_lookup_hash(record.session_lookup_hash),
            auth_method=record.auth_method,
            verification_strength=record.verification_strength.value,
            policy_decision_hash=record.policy_decision_hash,
            plan=record.effective_plan,
        )
        return WalletSessionCreationResult(
            session_token=token,
            token_type="PoP",
            expires_at=expires_at,
            principal_pseudonym=record.principal_hash,
            device_fingerprint=record.device_key_fingerprint,
            session_public_key_fingerprint=record.session_public_key_fingerprint,
            effective_plan=record.effective_plan,
            effective_scopes=record.effective_scopes,
            policy_mode="proof_of_possession",
            requires_request_signature=True,
            request_signature_algorithm=record.session_signature_algorithm,
            server_time=now,
            warning="The session token alone is insufficient. Protected requests require a valid Proof-of-Possession signature.",
            context=record.safe_context(),
        )

    async def get_session_context(self, *, session_token: str) -> WalletSessionContext:
        record = await self._get_record_by_token(session_token)
        return record.safe_context()

    async def validate_session_state(self, *, session_token: str) -> WalletSessionContext:
        now = self._now()
        record = await self._get_record_by_token(session_token)
        if record.expires_at <= now:
            expired = replace(record, status=WalletSessionStatus.EXPIRED)
            await self.repository.update(expired)
            raise WalletSessionStateError(WalletSessionReasonCode.EXPIRED)
        if record.status is WalletSessionStatus.REVOKED:
            raise WalletSessionStateError(WalletSessionReasonCode.REVOKED)
        if record.status in {WalletSessionStatus.FROZEN, WalletSessionStatus.LOCKDOWN}:
            raise WalletSessionStateError(WalletSessionReasonCode.LOCKDOWN_ACTIVE)
        if self.revocation_checker and (
            self.revocation_checker.is_revoked(target_type="wallet_session", target_hash=record.session_lookup_hash)
            or self.revocation_checker.is_revoked(target_type="wallet_principal", target_hash=record.principal_hash)
            or self.revocation_checker.is_revoked(target_type="wallet_device", target_hash=record.device_key_fingerprint)
        ):
            raise WalletSessionStateError(WalletSessionReasonCode.REVOKED)
        return record.safe_context()

    async def refresh_session(self, *, session_token: str) -> WalletSessionContext:
        context = await self.validate_session_state(session_token=session_token)
        return context

    async def rotate_session(
        self,
        *,
        session_token: str,
        new_session_public_key: str | bytes,
        reason_code: str = "wallet_session_rotated",
    ) -> WalletSessionCreationResult:
        old = await self._get_record_by_token(session_token)
        normalized = self._validate_session_public_key(new_session_public_key, algorithm=old.session_signature_algorithm, expected_fingerprint=None)
        now = self._now()
        await self.repository.update(replace(old, status=WalletSessionStatus.REVOKED, revoked_at=now, revocation_reason_code=reason_code))
        token = _generate_session_token()
        lookup_hash = self._hash_session_token(token)
        new_record = replace(
            old,
            session_lookup_hash=lookup_hash,
            session_public_key_b64=normalized.public_key_b64,
            session_public_key_fingerprint=normalized.fingerprint,
            issued_at=now,
            expires_at=min(old.expires_at, now + timedelta(seconds=self.default_ttl_seconds)),
            status=WalletSessionStatus.ACTIVE,
            revoked_at=None,
            frozen_at=None,
            revocation_reason_code=None,
            metadata={**dict(old.metadata), "rotated_from_session_fingerprint": _fingerprint_lookup_hash(old.session_lookup_hash)},
        )
        await self.repository.create(new_record)
        self._emit("wallet_session_rotated", principal_hash=old.principal_hash, device_key_fingerprint=old.device_key_fingerprint, reason_code=reason_code)
        return WalletSessionCreationResult(
            session_token=token,
            token_type="PoP",
            expires_at=new_record.expires_at,
            principal_pseudonym=new_record.principal_hash,
            device_fingerprint=new_record.device_key_fingerprint,
            session_public_key_fingerprint=new_record.session_public_key_fingerprint,
            effective_plan=new_record.effective_plan,
            effective_scopes=new_record.effective_scopes,
            policy_mode="proof_of_possession",
            requires_request_signature=True,
            request_signature_algorithm=new_record.session_signature_algorithm,
            server_time=now,
            warning="The session token alone is insufficient. Protected requests require a valid Proof-of-Possession signature.",
            context=new_record.safe_context(),
        )

    async def revoke_session(self, *, session_token: str, reason_code: str) -> WalletSessionContext:
        record = await self._get_record_by_token(session_token)
        now = self._now()
        revoked = replace(record, status=WalletSessionStatus.REVOKED, revoked_at=now, revocation_reason_code=reason_code)
        await self.repository.update(revoked)
        self._emit("wallet_session_revoked", principal_hash=record.principal_hash, device_key_fingerprint=record.device_key_fingerprint, reason_code=reason_code)
        return revoked.safe_context()

    async def freeze_sessions_for_principal(self, *, principal_hash: str, reason_code: str) -> int:
        count = await self.repository.freeze_for_principal(principal_hash, now=self._now(), reason_code=reason_code)
        self._emit("wallet_sessions_frozen_for_principal", principal_hash=principal_hash, reason_code=reason_code, count=count)
        return count

    async def freeze_sessions_for_device(self, *, principal_hash: str, device_key_fingerprint: str, reason_code: str) -> int:
        count = await self.repository.freeze_for_device(principal_hash, device_key_fingerprint, now=self._now(), reason_code=reason_code)
        self._emit("wallet_sessions_frozen_for_device", principal_hash=principal_hash, device_key_fingerprint=device_key_fingerprint, reason_code=reason_code, count=count)
        return count

    async def expire_stale_sessions(self) -> int:
        count = await self.repository.expire_stale(now=self._now())
        self._emit("wallet_session_expired", reason_code=WalletSessionReasonCode.EXPIRED.value, count=count)
        return count

    async def count_active_sessions(self, *, principal_hash: str, device_key_fingerprint: str | None = None) -> int:
        if device_key_fingerprint is None:
            return len(await self.repository.list_active_for_principal(principal_hash))
        return len(await self.repository.list_active_for_device(principal_hash, device_key_fingerprint))

    async def list_active_sessions(self, *, principal_hash: str) -> tuple[WalletSessionContext, ...]:
        return tuple(record.safe_context() for record in await self.repository.list_active_for_principal(principal_hash))

    async def assert_session_can_be_created(
        self,
        *,
        auth_context: VerifiedWalletAuthenticationContext,
        session_key: NormalizedDevicePublicKey,
        now: datetime | None = None,
    ) -> None:
        checked_now = now or self._now()
        self._validate_auth_context(auth_context, checked_now)
        if not constant_time_fingerprint_equal(session_key.fingerprint, auth_context.expected_session_public_key_fingerprint):
            raise WalletSessionKeyBindingError(WalletSessionReasonCode.KEY_BINDING_MISMATCH)
        if auth_context.expected_device_key_fingerprint and not constant_time_fingerprint_equal(
            auth_context.device_key_fingerprint, auth_context.expected_device_key_fingerprint
        ):
            raise WalletSessionKeyBindingError(WalletSessionReasonCode.KEY_BINDING_MISMATCH)
        if self.revocation_checker and (
            self.revocation_checker.is_revoked(target_type="wallet_principal", target_hash=auth_context.principal_hash)
            or self.revocation_checker.is_revoked(target_type="wallet_device", target_hash=auth_context.device_key_fingerprint)
            or self.revocation_checker.is_revoked(target_type="wallet_proof", target_hash=auth_context.proof_fingerprint)
            or self.revocation_checker.is_revoked(target_type="wallet_challenge", target_hash=auth_context.challenge_hash)
        ):
            raise WalletSessionStateError(WalletSessionReasonCode.REVOKED)

    async def _get_record_by_token(self, session_token: str) -> WalletSessionRecord:
        if not session_token.startswith(SESSION_TOKEN_PREFIX):
            raise WalletSessionStateError("wallet_session_not_found")
        record = await self.repository.get_by_lookup_hash(self._hash_session_token(session_token))
        if record is None:
            raise WalletSessionStateError("wallet_session_not_found")
        return record

    async def _resolve_entitlement(self, auth_context: VerifiedWalletAuthenticationContext) -> EntitlementSnapshot:
        if self.entitlement_service is None:
            return EntitlementSnapshot(active=True, entitlement_id=None, effective_plan="unknown", allowed_scopes=auth_context.requested_scopes)
        entitlement = await self.entitlement_service.get_entitlement_for_principal(auth_context.principal_hash)
        if auth_context.entitlement_required and not entitlement.active:
            raise WalletSessionPolicyError(WalletSessionReasonCode.ENTITLEMENT_INACTIVE)
        if not entitlement.allows(auth_context.requested_scopes):
            raise WalletSessionPolicyError(WalletSessionReasonCode.SCOPE_NOT_ALLOWED)
        return entitlement

    async def _enforce_session_limits(self, principal_hash: str, device_key_fingerprint: str) -> None:
        principal_count = len(await self.repository.list_active_for_principal(principal_hash))
        device_count = len(await self.repository.list_active_for_device(principal_hash, device_key_fingerprint))
        if principal_count >= self.max_active_sessions_per_principal or device_count >= self.max_active_sessions_per_device:
            self._emit("wallet_session_limit_reached", principal_hash=principal_hash, device_key_fingerprint=device_key_fingerprint, reason_code=WalletSessionReasonCode.LIMIT_REACHED.value)
            raise WalletSessionLimitError(WalletSessionReasonCode.LIMIT_REACHED)

    def _validate_auth_context(self, auth_context: VerifiedWalletAuthenticationContext, now: datetime) -> None:
        if auth_context.principal_status is WalletPrincipalStatus.REVOKED:
            raise WalletSessionStateError(WalletSessionReasonCode.REVOKED)
        if auth_context.principal_status is WalletPrincipalStatus.SUSPENDED:
            raise WalletSessionStateError(WalletSessionReasonCode.PRINCIPAL_INACTIVE)
        if auth_context.principal_status is WalletPrincipalStatus.RECOVERY_LOCKED and not auth_context.recovery_only_requested:
            raise WalletSessionStateError(WalletSessionReasonCode.PRINCIPAL_INACTIVE)
        if auth_context.device_status is not WalletDeviceStatus.ACTIVE:
            raise WalletSessionStateError(WalletSessionReasonCode.DEVICE_INACTIVE)
        if auth_context.challenge_used:
            raise WalletSessionChallengeError(WalletSessionReasonCode.CHALLENGE_USED)
        if auth_context.origin != auth_context.challenge_origin:
            raise WalletSessionChallengeError(WalletSessionReasonCode.ORIGIN_MISMATCH)
        if auth_context.challenge_action not in {"create_session", "login", "step_up", "lnurl_auth_login", "recovery_complete"}:
            raise WalletSessionChallengeError(WalletSessionReasonCode.INVALID_AUTH_CONTEXT)
        if auth_context.proof_expires_at is not None and auth_context.proof_expires_at <= now:
            raise WalletSessionChallengeError(WalletSessionReasonCode.CHALLENGE_EXPIRED)

    def _compute_expiry(
        self,
        *,
        auth_context: VerifiedWalletAuthenticationContext,
        entitlement: EntitlementSnapshot,
        requested_ttl_seconds: int | None,
        now: datetime,
    ) -> datetime:
        ttl = min(requested_ttl_seconds or self.default_ttl_seconds, self.max_ttl_seconds)
        if auth_context.verification_strength is WalletVerificationStrength.COMPATIBILITY:
            ttl = min(ttl, COMPATIBILITY_WALLET_SESSION_TTL_SECONDS)
        if auth_context.recovery_only_requested:
            ttl = min(ttl, RECOVERY_WALLET_SESSION_TTL_SECONDS)
        if auth_context.device_risk_score >= 70:
            ttl = min(ttl, HIGH_RISK_WALLET_SESSION_TTL_SECONDS)
        expiry = now + timedelta(seconds=max(60, ttl))
        if entitlement.expires_at is not None:
            expiry = min(expiry, entitlement.expires_at)
        if auth_context.proof_expires_at is not None:
            expiry = min(expiry, auth_context.proof_expires_at)
        return expiry

    def _policy_input(
        self,
        *,
        auth_context: VerifiedWalletAuthenticationContext,
        device: WalletDeviceRecord,
        entitlement: EntitlementSnapshot,
        active_principal: WalletPrincipalRecord,
    ) -> dict[str, object]:
        return {
            "action": "wallet_session_create",
            "actor_type": auth_context.principal_type.value,
            "principal_hash": auth_context.principal_hash,
            "principal_status": active_principal.status.value,
            "auth_method": auth_context.auth_method,
            "proof_type": auth_context.proof_type.value,
            "verification_strength": auth_context.verification_strength.value,
            "proof_freshness_seconds": int((self._now() - auth_context.proof_verified_at).total_seconds()),
            "device_class": device.device_class.value,
            "device_status": device.status.value,
            "device_risk_score": auth_context.device_risk_score,
            "requested_scopes": list(auth_context.requested_scopes),
            "entitlement_plan": entitlement.effective_plan,
            "entitlement_expires_at": entitlement.expires_at.isoformat() if entitlement.expires_at else None,
            "origin": auth_context.origin,
            "challenge_action": auth_context.challenge_action,
            "recovery_only_requested": auth_context.recovery_only_requested,
            "policy_epoch": auth_context.policy_epoch,
        }

    def _validate_session_public_key(
        self,
        session_public_key: str | bytes,
        *,
        algorithm: str,
        expected_fingerprint: str | None,
    ) -> NormalizedDevicePublicKey:
        try:
            detect_forbidden_private_material(session_public_key)
            return validate_device_public_key(session_public_key, algorithm=algorithm, expected_fingerprint=expected_fingerprint)
        except DeviceKeyInvalidError as exc:
            reason = WalletSessionReasonCode.PRIVATE_KEY_REJECTED if "private" in str(exc) else WalletSessionReasonCode.KEY_BINDING_MISMATCH
            raise WalletSessionKeyBindingError(reason) from exc

    def _hash_session_token(self, token: str) -> str:
        return compute_hmac_lookup_hash(self.server_pepper, "wallet_session_lookup", token)

    def _now(self) -> datetime:
        now = self.clock()
        return now if now.tzinfo else now.replace(tzinfo=UTC)

    def _emit(self, event_name: str, **payload: object) -> None:
        if self.audit_chain is None:
            return
        safe = {key: value for key, value in payload.items() if key not in {"session_token", "raw_token", "private_key", "seed", "mnemonic", "wallet_signature"}}
        self.audit_chain(event_name, safe)



def _record_from_model(model: WalletSession) -> WalletSessionRecord:
    policy_context = dict(model.policy_context_json or {})
    metadata = dict(model.metadata_json or {})
    return WalletSessionRecord(
        session_lookup_hash=model.session_hash,
        principal_hash=model.principal_hash,
        principal_type=PrincipalType(metadata.get("principal_type", PrincipalType.BITCOIN_WALLET_PRINCIPAL.value)),
        device_binding_id=model.device_id,
        device_key_fingerprint=model.device_key_fingerprint,
        session_public_key_b64=str(metadata.get("session_public_key_b64", "")),
        session_public_key_fingerprint=model.session_public_key_fingerprint or "sha256:" + "0" * 64,
        session_signature_algorithm=str(policy_context.get("session_signature_algorithm", "ed25519")),
        auth_method=model.auth_method,
        verification_strength=WalletVerificationStrength(model.verification_strength),
        entitlement_id=policy_context.get("entitlement_id") if isinstance(policy_context.get("entitlement_id"), str) else None,
        effective_plan=str(policy_context.get("effective_plan", "unknown")),
        effective_scopes=tuple(str(scope) for scope in (model.scopes_json or [])),
        policy_hash=str(policy_context.get("policy_hash", "sha256:" + "0" * 64)),
        policy_decision_hash=str(policy_context.get("policy_decision_hash", "sha256:" + "0" * 64)),
        policy_epoch=int(policy_context.get("policy_epoch", 1)),
        crypto_epoch=int(policy_context.get("crypto_epoch", 1)),
        challenge_id=str(metadata.get("challenge_id", "")),
        challenge_hash=str(metadata.get("challenge_hash", "sha256:" + "0" * 64)),
        proof_fingerprint=str(metadata.get("proof_fingerprint", "sha256:" + "0" * 64)),
        origin=str(policy_context.get("origin", "")),
        status=WalletSessionStatus(model.status),
        issued_at=model.issued_at if model.issued_at.tzinfo else model.issued_at.replace(tzinfo=UTC),
        expires_at=model.expires_at if model.expires_at.tzinfo else model.expires_at.replace(tzinfo=UTC),
        last_seen_at=model.last_seen_at,
        revoked_at=model.revoked_at,
        frozen_at=model.frozen_at,
        revocation_reason_code=metadata.get("revocation_reason_code") if isinstance(metadata.get("revocation_reason_code"), str) else None,
        risk_snapshot=dict(policy_context.get("risk_snapshot", {})) if isinstance(policy_context.get("risk_snapshot"), dict) else {},
        metadata=metadata,
    )


def _apply_record_to_model(record: WalletSessionRecord, model: WalletSession) -> None:
    model.status = record.status.value
    model.expires_at = record.expires_at
    model.revoked_at = record.revoked_at
    model.frozen_at = record.frozen_at
    model.last_seen_at = record.last_seen_at
    model.session_public_key_fingerprint = record.session_public_key_fingerprint
    model.scopes_json = list(record.effective_scopes)
    model.policy_context_json = {
        **dict(model.policy_context_json or {}),
        "policy_hash": record.policy_hash,
        "policy_decision_hash": record.policy_decision_hash,
        "policy_epoch": record.policy_epoch,
        "crypto_epoch": record.crypto_epoch,
        "origin": record.origin,
        "risk_snapshot": dict(record.risk_snapshot),
        "entitlement_id": record.entitlement_id,
        "effective_plan": record.effective_plan,
        "session_signature_algorithm": record.session_signature_algorithm,
        "requires_request_signature": True,
    }
    model.metadata_json = {
        **dict(model.metadata_json or {}),
        **dict(record.metadata),
        "session_public_key_b64": record.session_public_key_b64,
        "principal_type": record.principal_type.value,
        "challenge_id": record.challenge_id,
        "challenge_hash": record.challenge_hash,
        "proof_fingerprint": record.proof_fingerprint,
        "revocation_reason_code": record.revocation_reason_code,
    }

def _generate_session_token() -> str:
    return SESSION_TOKEN_PREFIX + secrets.token_urlsafe(SESSION_TOKEN_ENTROPY_BYTES)


def _require_hash(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not (value.startswith("hmac-sha256:") or value.startswith("sha256:")):
        raise ValueError(f"{field_name}_must_be_safe_hash")


def _fingerprint_lookup_hash(session_lookup_hash: str) -> str:
    return sha256_prefixed(b"wallet-session-fingerprint\x00" + session_lookup_hash.encode("utf-8"))


def sessions_require_request_signature(context: WalletSessionContext) -> bool:
    """Explicit integration boundary for Prompt 18 request verification."""

    return context.requires_request_signature


__all__ = [
    "EntitlementSnapshot",
    "InMemoryWalletSessionRepository",
    "PolicyDecision",
    "SqlAlchemyWalletSessionRepository",
    "VerifiedWalletAuthenticationContext",
    "WalletSessionContext",
    "WalletSessionCreationResult",
    "WalletSessionError",
    "WalletSessionReasonCode",
    "WalletSessionRecord",
    "WalletSessionService",
    "sessions_require_request_signature",
]
