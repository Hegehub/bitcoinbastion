"""Lightning Principal lifecycle service.

Lightning Principals are privacy-preserving cryptographic actors created only
after an LNURL-auth callback proof has already been verified. This service does
not verify signatures, issue sessions, grant entitlements, issue Access
Certificates, or authorize protected API access.
"""
from __future__ import annotations

import re
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol
from urllib.parse import urlsplit

from app.domain.lnurl.principals import LightningPrincipalStatus
from app.domain.wallet_auth.principals import WalletPrincipalActorType
from app.domain.wallet_auth.proofs import WalletVerificationStrength
from app.services.access.crypto.hashing import canonical_json, hmac_sha256_prefixed, sha256_prefixed
from app.services.lnurl.auth_callback_verifier import VerifiedLNURLAuthProof
from app.services.wallet_auth.privacy_commitments import compute_hmac_lookup_hash, compute_lnurl_key_hash, reject_forbidden_wallet_secret_input

COMPRESSED_SECP256K1_RE = re.compile(r"^(02|03)[0-9a-f]{64}$")
PRIMARY_AUTH_DOMAIN = "auth.bitcoin-bastion.com"
LIGHTNING_PRINCIPAL_TYPE = WalletPrincipalActorType.LIGHTNING_WALLET_PRINCIPAL.value


class AuthDomainClass(StrEnum):
    PRIMARY = "primary"
    LEGACY = "legacy"
    MIGRATION_ALLOWED = "migration_allowed"
    MERCHANT_CUSTOM = "merchant_custom"
    ONION = "onion"
    DEVELOPMENT = "development"
    FORBIDDEN = "forbidden"


@dataclass(frozen=True, slots=True)
class AuthDomainPolicy:
    primary_domain: str = PRIMARY_AUTH_DOMAIN
    legacy_domains: frozenset[str] = frozenset()
    migration_allowed_domains: frozenset[str] = frozenset()
    merchant_custom_domains: frozenset[str] = frozenset()
    onion_domains: frozenset[str] = frozenset()
    development_domains: frozenset[str] = frozenset()

    def classify(self, domain: str) -> AuthDomainClass:
        normalized = normalize_auth_domain(domain)
        if normalized == self.primary_domain:
            return AuthDomainClass.PRIMARY
        if normalized in self.legacy_domains:
            return AuthDomainClass.LEGACY
        if normalized in self.migration_allowed_domains:
            return AuthDomainClass.MIGRATION_ALLOWED
        if normalized in self.merchant_custom_domains:
            return AuthDomainClass.MERCHANT_CUSTOM
        if normalized in self.onion_domains:
            return AuthDomainClass.ONION
        if normalized in self.development_domains:
            return AuthDomainClass.DEVELOPMENT
        return AuthDomainClass.FORBIDDEN

    def require_allowed(self, domain: str) -> str:
        normalized = normalize_auth_domain(domain)
        if self.classify(normalized) is AuthDomainClass.FORBIDDEN:
            raise LightningPrincipalDomainMismatchError("auth_domain_forbidden")
        return normalized


@dataclass(frozen=True, slots=True)
class LightningPrincipalConfig:
    lnurl_auth_server_pepper: str
    principal_server_pepper: str
    product_pseudonym_pepper: str | None = None
    domain_policy: AuthDomainPolicy = AuthDomainPolicy()
    schema_epoch: int = 1
    policy_epoch: int = 1
    crypto_epoch: int = 1

    def __post_init__(self) -> None:
        if not self.lnurl_auth_server_pepper or not self.principal_server_pepper:
            raise LightningPrincipalProofNotVerifiedError("principal_pepper_required")


@dataclass(frozen=True, slots=True)
class LightningPrincipal:
    principal_hash: str
    principal_type: str
    lnurl_key_hash: str
    auth_domain: str
    linking_key_fingerprint: str
    proof_method: str
    verification_strength: WalletVerificationStrength
    status: LightningPrincipalStatus
    schema_epoch: int
    policy_epoch: int
    crypto_epoch: int
    created_at: datetime
    updated_at: datetime
    last_verified_at: datetime | None
    last_proof_fingerprint: str | None
    last_challenge_id_hash: str | None
    device_key_fingerprint: str | None = None
    product_pseudonym: str | None = None
    revoked_at: datetime | None = None
    verification_count: int = 0
    metadata: Mapping[str, str] = None  # type: ignore[assignment]


@dataclass(frozen=True, slots=True)
class LightningPrincipalCreateResult:
    principal: LightningPrincipal
    created: bool
    verification_recorded: bool
    device_binding_required: bool
    policy_evaluation_required: bool
    audit_event_hash: str | None
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LightningPrincipalAuthenticationContext:
    principal_hash: str
    principal_type: str
    status: LightningPrincipalStatus
    verification_strength: WalletVerificationStrength
    last_verified_at: datetime | None
    auth_domain: str
    proof_method: str
    device_binding_required: bool
    entitlement_required: bool
    policy_evaluation_required: bool
    revocation_checked: bool
    audit_event_hash: str | None


@dataclass(frozen=True, slots=True)
class PrincipalStateTransitionResult:
    principal_hash: str
    previous_status: LightningPrincipalStatus
    new_status: LightningPrincipalStatus
    changed: bool
    reason_code: str


@dataclass(frozen=True, slots=True)
class PrincipalLinkRequest:
    source_principal_hash: str
    target_principal_hash: str
    link_hash: str
    requires_policy_approval: bool = True
    requires_fresh_proof: bool = True
    automatic_merge_allowed: bool = False


class LightningPrincipalError(ValueError):
    def __init__(self, reason_code: str) -> None:
        self.reason_code = reason_code
        super().__init__(reason_code)


class LightningPrincipalNotFoundError(LightningPrincipalError): ...
class LightningPrincipalRevokedError(LightningPrincipalError): ...
class LightningPrincipalSuspendedError(LightningPrincipalError): ...
class LightningPrincipalRecoveryLockedError(LightningPrincipalError): ...
class LightningPrincipalDomainMismatchError(LightningPrincipalError): ...
class LightningPrincipalAlreadyLinkedError(LightningPrincipalError): ...
class LightningPrincipalInvalidTransitionError(LightningPrincipalError): ...
class LightningPrincipalCreationConflictError(LightningPrincipalError): ...
class LightningPrincipalProofNotVerifiedError(LightningPrincipalError): ...
class LightningPrincipalEnumerationProtectedError(LightningPrincipalError): ...


class LightningPrincipalRepository(Protocol):
    def get_by_principal_hash(self, principal_hash: str) -> LightningPrincipal | None: ...
    def get_by_lnurl_key_hash_and_domain(self, *, lnurl_key_hash: str, auth_domain: str) -> LightningPrincipal | None: ...
    def find_or_create(self, *, record: LightningPrincipal) -> tuple[LightningPrincipal, bool]: ...
    def update(self, record: LightningPrincipal) -> LightningPrincipal: ...
    def list_device_bindings(self, principal_hash: str) -> tuple[str, ...]: ...


class InMemoryLightningPrincipalRepository:
    def __init__(self) -> None:
        self._records: dict[str, LightningPrincipal] = {}
        self._domain_key_index: dict[tuple[str, str], str] = {}
        self._devices: dict[str, set[str]] = {}
        self._lock = threading.Lock()

    def get_by_principal_hash(self, principal_hash: str) -> LightningPrincipal | None:
        with self._lock:
            return self._records.get(principal_hash)

    def get_by_lnurl_key_hash_and_domain(self, *, lnurl_key_hash: str, auth_domain: str) -> LightningPrincipal | None:
        with self._lock:
            principal_hash = self._domain_key_index.get((auth_domain, lnurl_key_hash))
            return self._records.get(principal_hash) if principal_hash else None

    def find_or_create(self, *, record: LightningPrincipal) -> tuple[LightningPrincipal, bool]:
        with self._lock:
            existing_hash = self._domain_key_index.get((record.auth_domain, record.lnurl_key_hash))
            if existing_hash:
                return self._records[existing_hash], False
            if record.principal_hash in self._records:
                return self._records[record.principal_hash], False
            self._records[record.principal_hash] = record
            self._domain_key_index[(record.auth_domain, record.lnurl_key_hash)] = record.principal_hash
            self._devices.setdefault(record.principal_hash, set())
            return record, True

    def update(self, record: LightningPrincipal) -> LightningPrincipal:
        with self._lock:
            if record.principal_hash not in self._records:
                raise LightningPrincipalNotFoundError("principal_not_found")
            self._records[record.principal_hash] = record
            return record

    def add_device_binding(self, *, principal_hash: str, device_key_fingerprint: str) -> None:
        with self._lock:
            self._devices.setdefault(principal_hash, set()).add(device_key_fingerprint)

    def list_device_bindings(self, principal_hash: str) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._devices.get(principal_hash, set())))


class SqlAlchemyLightningPrincipalRepository:
    def __init__(self, db: Any) -> None:
        self.db = db

    def get_by_principal_hash(self, principal_hash: str) -> LightningPrincipal | None:
        from sqlalchemy import select
        from app.db.models.lnurl import LNURLPrincipal

        row = self.db.execute(select(LNURLPrincipal).where(LNURLPrincipal.principal_hash == principal_hash)).scalar_one_or_none()
        return _record_from_row(row) if row else None

    def get_by_lnurl_key_hash_and_domain(self, *, lnurl_key_hash: str, auth_domain: str) -> LightningPrincipal | None:
        from sqlalchemy import select
        from app.db.models.lnurl import LNURLPrincipal

        row = self.db.execute(
            select(LNURLPrincipal).where(LNURLPrincipal.auth_domain == auth_domain, LNURLPrincipal.lnurl_key_hash == lnurl_key_hash)
        ).scalar_one_or_none()
        return _record_from_row(row) if row else None

    def find_or_create(self, *, record: LightningPrincipal) -> tuple[LightningPrincipal, bool]:
        from sqlalchemy.exc import IntegrityError
        from app.db.models.lnurl import LNURLPrincipal

        existing = self.get_by_lnurl_key_hash_and_domain(lnurl_key_hash=record.lnurl_key_hash, auth_domain=record.auth_domain)
        if existing:
            return existing, False
        row = LNURLPrincipal(
            principal_hash=record.principal_hash,
            lnurl_key_hash=record.lnurl_key_hash,
            auth_domain=record.auth_domain,
            linking_key_fingerprint=record.linking_key_fingerprint,
            verification_strength=record.verification_strength.value,
            status=record.status.value,
            created_at=record.created_at,
            updated_at=record.updated_at,
            last_verified_at=record.last_verified_at,
            revoked_at=record.revoked_at,
            metadata_json=_metadata_for_row(record),
        )
        self.db.add(row)
        try:
            self.db.flush()
        except IntegrityError:
            self.db.rollback()
            existing = self.get_by_lnurl_key_hash_and_domain(lnurl_key_hash=record.lnurl_key_hash, auth_domain=record.auth_domain)
            if existing:
                return existing, False
            raise LightningPrincipalCreationConflictError("principal_creation_conflict")
        return record, True

    def update(self, record: LightningPrincipal) -> LightningPrincipal:
        from sqlalchemy import select
        from app.db.models.lnurl import LNURLPrincipal

        row = self.db.execute(select(LNURLPrincipal).where(LNURLPrincipal.principal_hash == record.principal_hash).with_for_update()).scalar_one_or_none()
        if row is None:
            raise LightningPrincipalNotFoundError("principal_not_found")
        row.status = record.status.value
        row.verification_strength = record.verification_strength.value
        row.last_verified_at = record.last_verified_at
        row.revoked_at = record.revoked_at
        row.updated_at = record.updated_at
        row.metadata_json = _metadata_for_row(record)
        self.db.flush()
        return record

    def list_device_bindings(self, principal_hash: str) -> tuple[str, ...]:
        return ()


class LightningPrincipalRevocationRegistry(Protocol):
    def is_revoked(self, *, target_type: str, target_hash: str) -> bool: ...
    def revoke(self, *, target_type: str, target_hash: str, reason_code: str, policy_epoch: int) -> None: ...


AuditEmitter = Callable[[str, Mapping[str, object]], None]
MetricsEmitter = Callable[[str, Mapping[str, str]], None]


_ALLOWED_TRANSITIONS: dict[LightningPrincipalStatus, frozenset[LightningPrincipalStatus]] = {
    LightningPrincipalStatus.PENDING: frozenset({LightningPrincipalStatus.ACTIVE}),
    LightningPrincipalStatus.ACTIVE: frozenset({LightningPrincipalStatus.SUSPENDED, LightningPrincipalStatus.REVOKED, LightningPrincipalStatus.RECOVERY_LOCKED}),
    LightningPrincipalStatus.SUSPENDED: frozenset({LightningPrincipalStatus.ACTIVE, LightningPrincipalStatus.REVOKED}),
    LightningPrincipalStatus.RECOVERY_LOCKED: frozenset({LightningPrincipalStatus.ACTIVE, LightningPrincipalStatus.REVOKED}),
    LightningPrincipalStatus.REVOKED: frozenset(),
}


class LightningPrincipalService:
    def __init__(
        self,
        *,
        config: LightningPrincipalConfig,
        repository: LightningPrincipalRepository | None = None,
        revocation_registry: LightningPrincipalRevocationRegistry | None = None,
        audit_emitter: AuditEmitter | None = None,
        metrics_emitter: MetricsEmitter | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.config = config
        self.repository = repository or InMemoryLightningPrincipalRepository()
        self.revocation_registry = revocation_registry
        self.audit_emitter = audit_emitter
        self.metrics_emitter = metrics_emitter
        self.clock = clock or (lambda: datetime.now(UTC))

    def create_from_verified_lnurl_auth(
        self,
        *,
        proof: VerifiedLNURLAuthProof,
        normalized_linking_public_key: str,
        proof_fingerprint: str,
        policy_hash: str,
        product_id: str | None = None,
        request_context: Mapping[str, object] | None = None,
    ) -> LightningPrincipalCreateResult:
        self._validate_verified_proof(proof)
        _reject_secret_context(request_context or {})
        domain = self.config.domain_policy.require_allowed(proof.auth_domain)
        key = normalize_linking_public_key(normalized_linking_public_key)
        lnurl_key_hash = self.derive_lnurl_key_hash(normalized_linking_public_key=key, auth_domain=domain)
        principal_hash = self.derive_principal_hash(lnurl_key_hash=lnurl_key_hash, auth_domain=domain)
        linking_key_fingerprint = sha256_prefixed(bytes.fromhex(key))
        if linking_key_fingerprint != proof.key_fingerprint:
            raise LightningPrincipalProofNotVerifiedError("linking_key_proof_mismatch")
        self._check_revocations(principal_hash=principal_hash, lnurl_key_hash=lnurl_key_hash, auth_domain=domain, device_key_fingerprint=proof.device_key_fingerprint)
        now = self.clock()
        product_pseudonym = self.derive_product_pseudonym(product_id=product_id, principal_hash=principal_hash) if product_id else None
        candidate = LightningPrincipal(
            principal_hash=principal_hash,
            principal_type=LIGHTNING_PRINCIPAL_TYPE,
            lnurl_key_hash=lnurl_key_hash,
            auth_domain=domain,
            linking_key_fingerprint=linking_key_fingerprint,
            proof_method="lnurl_auth",
            verification_strength=proof.verification_strength,
            status=LightningPrincipalStatus.ACTIVE,
            schema_epoch=self.config.schema_epoch,
            policy_epoch=self.config.policy_epoch,
            crypto_epoch=self.config.crypto_epoch,
            created_at=now,
            updated_at=now,
            last_verified_at=proof.verified_at,
            last_proof_fingerprint=proof_fingerprint,
            last_challenge_id_hash=sha256_prefixed(proof.challenge_id),
            device_key_fingerprint=proof.device_key_fingerprint,
            product_pseudonym=product_pseudonym,
            verification_count=1,
            metadata={"policy_hash": policy_hash, "last_bastion_action": proof.bastion_action},
        )
        record, created = self.repository.find_or_create(record=candidate)
        if record.status is LightningPrincipalStatus.REVOKED:
            raise LightningPrincipalRevokedError("principal_revoked")
        if not created:
            record = self.record_successful_verification(record.principal_hash, proof=proof, proof_fingerprint=proof_fingerprint, policy_hash=policy_hash)
        event = "lightning_principal_created" if created else "lightning_principal_reused"
        audit_hash = self._emit_audit(event, record, proof=proof, proof_fingerprint=proof_fingerprint, policy_hash=policy_hash, reason_code="created" if created else "reused")
        self._metric("lightning_principal_created_total" if created else "lightning_principal_reused_total", result="created" if created else "reused", strength=record.verification_strength.value)
        return LightningPrincipalCreateResult(
            principal=record,
            created=created,
            verification_recorded=True,
            device_binding_required=not bool(record.device_key_fingerprint),
            policy_evaluation_required=True,
            audit_event_hash=audit_hash,
            warnings=_warnings(record),
        )

    def find_by_principal_hash(self, principal_hash: str) -> LightningPrincipal | None:
        _require_hmac(principal_hash, "principal_hash")
        return self.repository.get_by_principal_hash(principal_hash)

    def find_by_lnurl_key(self, *, normalized_linking_public_key: str, auth_domain: str) -> LightningPrincipal | None:
        domain = self.config.domain_policy.require_allowed(auth_domain)
        key = normalize_linking_public_key(normalized_linking_public_key)
        return self.repository.get_by_lnurl_key_hash_and_domain(lnurl_key_hash=self.derive_lnurl_key_hash(normalized_linking_public_key=key, auth_domain=domain), auth_domain=domain)

    def find_active_principal(self, principal_hash: str, *, device_key_fingerprint: str | None = None) -> LightningPrincipalAuthenticationContext:
        record = self._get(principal_hash)
        self._check_revocations(principal_hash=record.principal_hash, lnurl_key_hash=record.lnurl_key_hash, auth_domain=record.auth_domain, device_key_fingerprint=device_key_fingerprint)
        if record.status is LightningPrincipalStatus.SUSPENDED:
            raise LightningPrincipalSuspendedError("principal_suspended")
        if record.status is LightningPrincipalStatus.REVOKED:
            raise LightningPrincipalRevokedError("principal_revoked")
        return self.authentication_context(record, revocation_checked=True)

    def authentication_context(self, principal: LightningPrincipal, *, revocation_checked: bool) -> LightningPrincipalAuthenticationContext:
        return LightningPrincipalAuthenticationContext(
            principal_hash=principal.principal_hash,
            principal_type=principal.principal_type,
            status=principal.status,
            verification_strength=principal.verification_strength,
            last_verified_at=principal.last_verified_at,
            auth_domain=principal.auth_domain,
            proof_method=principal.proof_method,
            device_binding_required=not bool(principal.device_key_fingerprint),
            entitlement_required=True,
            policy_evaluation_required=True,
            revocation_checked=revocation_checked,
            audit_event_hash=None,
        )

    def record_successful_verification(self, principal_hash: str, *, proof: VerifiedLNURLAuthProof, proof_fingerprint: str, policy_hash: str) -> LightningPrincipal:
        self._validate_verified_proof(proof)
        record = self._get(principal_hash)
        if record.status is LightningPrincipalStatus.REVOKED:
            raise LightningPrincipalRevokedError("principal_revoked")
        if record.auth_domain != normalize_auth_domain(proof.auth_domain):
            raise LightningPrincipalDomainMismatchError("auth_domain_mismatch")
        updated = replace(
            record,
            last_verified_at=proof.verified_at,
            verification_strength=proof.verification_strength,
            last_proof_fingerprint=proof_fingerprint,
            last_challenge_id_hash=sha256_prefixed(proof.challenge_id),
            device_key_fingerprint=record.device_key_fingerprint or proof.device_key_fingerprint,
            verification_count=record.verification_count + 1,
            updated_at=self.clock(),
            metadata={**dict(record.metadata or {}), "policy_hash": policy_hash, "last_bastion_action": proof.bastion_action},
        )
        self.repository.update(updated)
        self._emit_audit("lightning_principal_verified", updated, proof=proof, proof_fingerprint=proof_fingerprint, policy_hash=policy_hash, reason_code="verified")
        self._metric("lightning_principal_verification_total", result="verified", strength=proof.verification_strength.value)
        return updated

    def activate_principal(self, principal_hash: str, *, reason_code: str) -> PrincipalStateTransitionResult:
        return self._transition(principal_hash, LightningPrincipalStatus.ACTIVE, reason_code, "lightning_principal_reactivated")

    def suspend_principal(self, principal_hash: str, *, reason_code: str) -> PrincipalStateTransitionResult:
        return self._transition(principal_hash, LightningPrincipalStatus.SUSPENDED, reason_code, "lightning_principal_suspended")

    def revoke_principal(self, principal_hash: str, *, reason_code: str) -> PrincipalStateTransitionResult:
        result = self._transition(principal_hash, LightningPrincipalStatus.REVOKED, reason_code, "lightning_principal_revoked")
        if self.revocation_registry:
            self.revocation_registry.revoke(target_type="lightning_wallet_principal", target_hash=principal_hash, reason_code=reason_code, policy_epoch=self.config.policy_epoch)
        self._metric("lightning_principal_revoked_total", result="revoked", strength="none")
        return result

    def lock_for_recovery(self, principal_hash: str, *, reason_code: str) -> PrincipalStateTransitionResult:
        return self._transition(principal_hash, LightningPrincipalStatus.RECOVERY_LOCKED, reason_code, "lightning_principal_recovery_locked")

    def restore_from_recovery_lock(self, principal_hash: str, *, reason_code: str) -> PrincipalStateTransitionResult:
        return self._transition(principal_hash, LightningPrincipalStatus.ACTIVE, reason_code, "lightning_principal_reactivated")

    def request_principal_link(self, *, source_principal_hash: str, target_principal_hash: str, policy_hash: str) -> PrincipalLinkRequest:
        if source_principal_hash == target_principal_hash:
            raise LightningPrincipalAlreadyLinkedError("principal_already_same")
        _require_hmac(source_principal_hash, "source_principal_hash")
        _require_hmac(target_principal_hash, "target_principal_hash")
        link_hash = hmac_sha256_prefixed(self.config.principal_server_pepper, canonical_json({"source": source_principal_hash, "target": target_principal_hash, "policy_hash": policy_hash}))
        self._emit_raw_audit("lightning_principal_link_requested", {"source_principal_hash": source_principal_hash, "target_principal_hash": target_principal_hash, "link_hash": link_hash, "policy_hash": policy_hash})
        return PrincipalLinkRequest(source_principal_hash, target_principal_hash, link_hash)

    def confirm_principal_link(self, *, link_request: PrincipalLinkRequest, policy_approved: bool, fresh_proofs_verified: bool) -> PrincipalLinkRequest:
        if not policy_approved or not fresh_proofs_verified:
            raise LightningPrincipalInvalidTransitionError("principal_link_requires_policy_and_fresh_proofs")
        self._emit_raw_audit("lightning_principal_link_completed", {"link_hash": link_request.link_hash, "result": "completed"})
        return link_request

    def remove_principal_link(self, *, link_hash: str, reason_code: str) -> None:
        self._emit_raw_audit("lightning_principal_link_removed", {"link_hash": link_hash, "reason_code": reason_code})

    def bind_device_to_principal(self, *, principal_hash: str, device_key_fingerprint: str, binding_method: str = "lnurl_auth_registration") -> LightningPrincipal:
        record = self._get(principal_hash)
        if not device_key_fingerprint.startswith("sha256:"):
            raise LightningPrincipalProofNotVerifiedError("invalid_device_fingerprint")
        if isinstance(self.repository, InMemoryLightningPrincipalRepository):
            self.repository.add_device_binding(principal_hash=principal_hash, device_key_fingerprint=device_key_fingerprint)
        updated = replace(record, device_key_fingerprint=device_key_fingerprint, updated_at=self.clock(), metadata={**dict(record.metadata or {}), "last_device_binding_method": binding_method})
        self.repository.update(updated)
        self._emit_audit("lightning_principal_device_bound", updated, proof=None, proof_fingerprint=None, policy_hash=None, reason_code=binding_method)
        return updated

    def derive_lnurl_key_hash(self, *, normalized_linking_public_key: str, auth_domain: str) -> str:
        return compute_lnurl_key_hash(self.config.lnurl_auth_server_pepper, normalize_linking_public_key(normalized_linking_public_key), normalize_auth_domain(auth_domain))

    def derive_principal_hash(self, *, lnurl_key_hash: str, auth_domain: str) -> str:
        _require_hmac(lnurl_key_hash, "lnurl_key_hash")
        payload = canonical_json({"principal_type": LIGHTNING_PRINCIPAL_TYPE, "auth_domain": normalize_auth_domain(auth_domain), "lnurl_key_hash": lnurl_key_hash})
        return compute_hmac_lookup_hash(self.config.principal_server_pepper, "principal:lightning_wallet_principal", payload)

    def derive_product_pseudonym(self, *, product_id: str, principal_hash: str) -> str:
        if not self.config.product_pseudonym_pepper:
            raise LightningPrincipalProofNotVerifiedError("product_pseudonym_pepper_required")
        return compute_hmac_lookup_hash(self.config.product_pseudonym_pepper, "product_lightning_principal", canonical_json({"product_id": product_id, "principal_hash": principal_hash}))

    def _transition(self, principal_hash: str, target: LightningPrincipalStatus, reason_code: str, event: str) -> PrincipalStateTransitionResult:
        record = self._get(principal_hash)
        if target not in _ALLOWED_TRANSITIONS[record.status]:
            raise LightningPrincipalInvalidTransitionError("invalid_state_transition")
        now = self.clock()
        updated = replace(record, status=target, updated_at=now, revoked_at=now if target is LightningPrincipalStatus.REVOKED else record.revoked_at, metadata={**dict(record.metadata or {}), "last_state_reason_code": reason_code})
        self.repository.update(updated)
        self._emit_audit(event, updated, proof=None, proof_fingerprint=None, policy_hash=None, reason_code=reason_code, previous_status=record.status, new_status=target)
        return PrincipalStateTransitionResult(principal_hash, record.status, target, True, reason_code)

    def _get(self, principal_hash: str) -> LightningPrincipal:
        record = self.find_by_principal_hash(principal_hash)
        if record is None:
            raise LightningPrincipalNotFoundError("principal_not_found")
        return record

    def _validate_verified_proof(self, proof: VerifiedLNURLAuthProof) -> None:
        if not isinstance(proof, VerifiedLNURLAuthProof):
            raise LightningPrincipalProofNotVerifiedError("verified_lnurl_auth_proof_required")
        if proof.verification_strength not in {WalletVerificationStrength.STANDARD, WalletVerificationStrength.HIGH_ASSURANCE, WalletVerificationStrength.SOVEREIGN}:
            raise LightningPrincipalProofNotVerifiedError("insufficient_lnurl_auth_proof")
        if proof.verified_at is None or not proof.challenge_id or not proof.lnurl_key_hash.startswith("hmac-sha256:"):
            raise LightningPrincipalProofNotVerifiedError("verified_lnurl_auth_proof_required")
        if proof.verification_strength in {WalletVerificationStrength.HIGH_ASSURANCE, WalletVerificationStrength.SOVEREIGN}:
            raise LightningPrincipalProofNotVerifiedError("lnurl_auth_alone_cannot_raise_assurance")

    def _check_revocations(self, *, principal_hash: str, lnurl_key_hash: str, auth_domain: str, device_key_fingerprint: str | None) -> None:
        if self.revocation_registry is None:
            return
        checks = [("lightning_wallet_principal", principal_hash), ("lnurl_auth_key_hash", lnurl_key_hash), ("auth_domain", sha256_prefixed(auth_domain))]
        if device_key_fingerprint:
            checks.append(("wallet_device", device_key_fingerprint))
        for target_type, target_hash in checks:
            if self.revocation_registry.is_revoked(target_type=target_type, target_hash=target_hash):
                raise LightningPrincipalRevokedError("revoked_target")

    def _emit_audit(self, event: str, record: LightningPrincipal, *, proof: VerifiedLNURLAuthProof | None, proof_fingerprint: str | None, policy_hash: str | None, reason_code: str, previous_status: LightningPrincipalStatus | None = None, new_status: LightningPrincipalStatus | None = None) -> str | None:
        payload: dict[str, object] = {
            "principal_hash": record.principal_hash,
            "lnurl_key_hash": record.lnurl_key_hash,
            "auth_domain_hash": sha256_prefixed(record.auth_domain),
            "proof_fingerprint": proof_fingerprint,
            "challenge_id_hash": sha256_prefixed(proof.challenge_id) if proof else record.last_challenge_id_hash,
            "verification_strength": record.verification_strength.value,
            "actor_type": record.principal_type,
            "policy_hash": policy_hash,
            "device_key_fingerprint": record.device_key_fingerprint,
            "timestamp": self.clock().isoformat(),
            "result": "ok",
            "reason_code": reason_code,
            "previous_status": previous_status.value if previous_status else None,
            "new_status": new_status.value if new_status else record.status.value,
        }
        audit_hash = sha256_prefixed(canonical_json(payload))
        payload["audit_event_hash"] = audit_hash
        if self.audit_emitter:
            self.audit_emitter(event, payload)
        return audit_hash

    def _emit_raw_audit(self, event: str, payload: Mapping[str, object]) -> None:
        safe = {**dict(payload), "timestamp": self.clock().isoformat()}
        if self.audit_emitter:
            self.audit_emitter(event, safe)

    def _metric(self, name: str, *, result: str, strength: str) -> None:
        if self.metrics_emitter:
            self.metrics_emitter(name, {"result": result, "verification_strength": strength, "proof_method": "lnurl_auth", "domain_class": "primary"})


def normalize_auth_domain(domain: str) -> str:
    reject_forbidden_wallet_secret_input(domain, "auth_domain")
    if "://" in domain:
        parsed = urlsplit(domain)
        if parsed.path not in ("", "/") or parsed.query or parsed.fragment or parsed.username or parsed.password:
            raise LightningPrincipalDomainMismatchError("auth_domain_must_be_host_only")
        host = parsed.hostname or ""
    else:
        parsed = urlsplit("//" + domain)
        if parsed.path not in ("", "/") or parsed.query or parsed.fragment or parsed.username or parsed.password:
            raise LightningPrincipalDomainMismatchError("auth_domain_must_be_host_only")
        host = parsed.hostname or ""
    normalized = host.rstrip(".").lower()
    if not normalized or normalized in {"localhost", "127.0.0.1", "::1"} or any(ch in normalized for ch in "/?#@"):
        raise LightningPrincipalDomainMismatchError("auth_domain_invalid")
    return normalized


def normalize_linking_public_key(key: str) -> str:
    reject_forbidden_wallet_secret_input(key, "linking_public_key")
    normalized = key.strip().lower()
    if COMPRESSED_SECP256K1_RE.fullmatch(normalized) is None:
        raise LightningPrincipalProofNotVerifiedError("compressed_lnurl_public_key_required")
    return normalized


def _require_hmac(value: str, field_name: str) -> None:
    if not value.startswith("hmac-sha256:"):
        raise LightningPrincipalEnumerationProtectedError(f"{field_name}_must_be_hmac")


def _reject_secret_context(context: Mapping[str, object]) -> None:
    for key, value in context.items():
        reject_forbidden_wallet_secret_input(str(key), "context_key")
        if isinstance(value, str):
            reject_forbidden_wallet_secret_input(value, str(key))


def _warnings(record: LightningPrincipal) -> tuple[str, ...]:
    warnings = ["policy_evaluation_required", "subscription_required", "lnurl_auth_is_not_bitcoin_treasury_ownership"]
    if not record.device_key_fingerprint:
        warnings.append("device_binding_required")
    return tuple(warnings)


def _metadata_for_row(record: LightningPrincipal) -> dict[str, object]:
    return {
        "principal_type": record.principal_type,
        "proof_method": record.proof_method,
        "schema_epoch": record.schema_epoch,
        "policy_epoch": record.policy_epoch,
        "crypto_epoch": record.crypto_epoch,
        "last_proof_fingerprint": record.last_proof_fingerprint,
        "last_challenge_id_hash": record.last_challenge_id_hash,
        "device_key_fingerprint": record.device_key_fingerprint,
        "product_pseudonym": record.product_pseudonym,
        "verification_count": record.verification_count,
        **dict(record.metadata or {}),
    }


def _record_from_row(row: Any) -> LightningPrincipal:
    metadata = row.metadata_json or {}
    return LightningPrincipal(
        principal_hash=row.principal_hash,
        principal_type=str(metadata.get("principal_type") or LIGHTNING_PRINCIPAL_TYPE),
        lnurl_key_hash=row.lnurl_key_hash,
        auth_domain=row.auth_domain,
        linking_key_fingerprint=row.linking_key_fingerprint or "sha256:unknown",
        proof_method=str(metadata.get("proof_method") or "lnurl_auth"),
        verification_strength=WalletVerificationStrength(row.verification_strength),
        status=LightningPrincipalStatus(row.status),
        schema_epoch=int(metadata.get("schema_epoch") or 1),
        policy_epoch=int(metadata.get("policy_epoch") or 1),
        crypto_epoch=int(metadata.get("crypto_epoch") or 1),
        created_at=row.created_at,
        updated_at=row.updated_at,
        last_verified_at=row.last_verified_at,
        last_proof_fingerprint=metadata.get("last_proof_fingerprint"),
        last_challenge_id_hash=metadata.get("last_challenge_id_hash"),
        device_key_fingerprint=metadata.get("device_key_fingerprint"),
        product_pseudonym=metadata.get("product_pseudonym"),
        revoked_at=row.revoked_at,
        verification_count=int(metadata.get("verification_count") or 0),
        metadata={k: str(v) for k, v in metadata.items() if isinstance(v, str)},
    )


__all__ = [
    "AuthDomainClass",
    "AuthDomainPolicy",
    "InMemoryLightningPrincipalRepository",
    "LightningPrincipal",
    "LightningPrincipalAuthenticationContext",
    "LightningPrincipalConfig",
    "LightningPrincipalCreateResult",
    "LightningPrincipalService",
    "SqlAlchemyLightningPrincipalRepository",
    "normalize_auth_domain",
    "normalize_linking_public_key",
]
