"""Recovery-specific LNURL-auth factor orchestration.

This module reuses the LNURL k1 registry and callback verifier.  It never
creates a session or completes recovery; a verified callback is converted into
exactly one attempt-bound Recovery Capsule factor receipt.
"""

from __future__ import annotations

import hmac
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Protocol
from urllib.parse import urlencode, urlunsplit

from app.domain.lnurl.auth import LNURLAuthAction
from app.services.access.crypto.hashing import (
    canonical_json,
    hmac_sha256_prefixed,
    sha256_prefixed,
)
from app.services.access.crypto.signatures import Ed25519SignatureSuite
from app.services.lnurl.auth_callback_verifier import (
    LNURLAuthCallbackResponse,
    LNURLAuthCallbackStatus,
    LNURLAuthCallbackVerifier,
)
from app.services.lnurl.auth_challenge_service import (
    InMemoryLNURLAuthChallengeRepository,
    LNURLAuthChallengeRecord,
    LNURLAuthChallengeStatus,
)
from app.services.lnurl.encoding import encode_lnurl
from app.services.lnurl.k1_registry import (
    LNURLK1Purpose,
    LNURLK1RegistryService,
    LNURLK1Status,
)
from app.services.wallet_auth.recovery.capsule import RecoveryCapsuleService
from app.services.wallet_auth.recovery.errors import RecoveryFactorError
from app.services.wallet_auth.recovery.models import (
    RecoveryCapsule,
    RecoveryCapsuleStatus,
    RecoveryFactorResult,
    RecoveryFactorSubmission,
    RecoveryFactorType,
    RecoveryProfile,
    RecoveryVerificationContext,
)
from app.services.wallet_auth.recovery.redaction import SAFETY_WARNING
from app.services.wallet_auth.recovery.policy import PROFILE_REQUIREMENTS

RECOVERY_INTERNAL_ACTION = "recovery_factor_verify"
RECOVERY_INTENT_TYPE = "bastion_lnurl_recovery_intent"
RECOVERY_PUBLIC_MESSAGE = (
    "If the recovery reference is valid, the requested factor flow has been started."
)
RECOVERY_PUBLIC_ERROR = "Recovery factor could not be verified."
RECOVERY_WARNING = (
    "LNURL-auth proves control of a Lightning wallet key for this recovery attempt. "
    "It does not prove control of your Bitcoin treasury wallet. "
    "It does not complete recovery by itself. "
    "Bastion will never ask for your Bitcoin seed, mnemonic or private key."
)


class LNURLRecoveryFactorStatus(StrEnum):
    PENDING = "pending"
    CHALLENGE_ISSUED = "challenge_issued"
    CALLBACK_RECEIVED = "callback_received"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVOKED = "revoked"
    CONSUMED = "consumed"


@dataclass(frozen=True, slots=True)
class LNURLRecoveryConfig:
    enabled: bool = True
    ttl_seconds: int = 300
    max_challenges_per_attempt: int = 5
    max_failed_callbacks: int = 10
    require_additional_factor: bool = True
    auth_domain: str = "auth.bitcoin-bastion.com"
    callback_path: str = "/v1/lnurl/auth/callback"
    allow_compatibility_proof: bool = False

    def __post_init__(self) -> None:
        if not self.enabled or not 30 <= self.ttl_seconds <= 300:
            raise RecoveryFactorError("lnurl_recovery_configuration_invalid")
        if not self.require_additional_factor:
            raise RecoveryFactorError("lnurl_recovery_additional_factor_required")
        if not self.auth_domain or not self.callback_path.startswith("/"):
            raise RecoveryFactorError("lnurl_recovery_domain_invalid")


@dataclass(frozen=True, slots=True)
class LNURLRecoveryIntent:
    type: str
    version: int
    domain: str
    lnurl_action: str
    bastion_action: str
    purpose: str
    recovery_attempt_hash: str
    challenge_hash: str
    principal_hint_hash: str
    device_context_hash: str | None
    policy_hash: str
    recovery_profile: str
    risk: str
    issued_at: datetime
    expires_at: datetime
    warning: str = RECOVERY_WARNING

    def canonical_payload(self) -> dict[str, object]:
        return {
            "type": self.type,
            "version": self.version,
            "domain": self.domain,
            "lnurl_action": self.lnurl_action,
            "bastion_action": self.bastion_action,
            "purpose": self.purpose,
            "recovery_attempt_hash": self.recovery_attempt_hash,
            "challenge_hash": self.challenge_hash,
            "principal_hint_hash": self.principal_hint_hash,
            "device_context_hash": self.device_context_hash,
            "policy_hash": self.policy_hash,
            "recovery_profile": self.recovery_profile,
            "risk": self.risk,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "warning": self.warning,
        }


@dataclass(frozen=True, slots=True)
class LNURLRecoveryChallenge:
    challenge_id: str
    registry_id: str
    recovery_attempt_hash: str
    principal_hash: str
    lnurl_principal_hash: str
    expected_lnurl_key_hash: str
    auth_domain_hash: str
    challenge_hash: str
    intent_hash: str
    policy_hash: str
    recovery_profile: RecoveryProfile
    issued_at: datetime
    expires_at: datetime
    status: LNURLRecoveryFactorStatus
    failed_callbacks: int = 0
    receipt_hash: str | None = None


@dataclass(frozen=True, slots=True)
class LNURLRecoveryChallengeResult:
    type: str
    recovery_attempt_id: str
    lnurl: str = field(repr=False)
    qr_payload: str = field(repr=False)
    expires_at: datetime
    factor_status: LNURLRecoveryFactorStatus
    remaining_factor_count: int
    warning: str = RECOVERY_WARNING
    public_message: str = RECOVERY_PUBLIC_MESSAGE


@dataclass(frozen=True, slots=True)
class LNURLRecoveryFactorReceipt:
    type: str
    version: int
    factor_type: str
    recovery_attempt_hash: str
    principal_hash: str
    lnurl_principal_hash: str
    auth_domain_hash: str
    proof_hash: str
    challenge_hash: str
    verification_strength: str
    verified_at: datetime
    expires_at: datetime
    status: LNURLRecoveryFactorStatus
    limitations: tuple[str, ...]
    policy_hash: str
    crypto_epoch: int
    issuer_signature: Mapping[str, object]
    audit_event_hash: str | None = None

    def safe_payload(self) -> dict[str, object]:
        return {
            "type": self.type,
            "version": self.version,
            "factor_type": self.factor_type,
            "recovery_attempt_hash": self.recovery_attempt_hash,
            "principal_hash": self.principal_hash,
            "lnurl_principal_hash": self.lnurl_principal_hash,
            "auth_domain_hash": self.auth_domain_hash,
            "proof_hash": self.proof_hash,
            "challenge_hash": self.challenge_hash,
            "verification_strength": self.verification_strength,
            "verified_at": self.verified_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "status": self.status.value,
            "limitations": list(self.limitations),
            "policy_hash": self.policy_hash,
            "crypto_epoch": self.crypto_epoch,
        }


class RecoveryReceiptSigner(Protocol):
    def sign(self, payload: Mapping[str, object]) -> Mapping[str, object]: ...

    def verify(self, payload: Mapping[str, object], signature: Mapping[str, object]) -> bool: ...


class Ed25519RecoveryReceiptSigner:
    """Adapter around the existing classical issuer signature suite."""

    def __init__(
        self,
        *,
        private_key: str | bytes,
        public_key: str | bytes,
        key_id: str,
        crypto_epoch: int = 1,
    ) -> None:
        self.private_key, self.public_key = private_key, public_key
        self.key_id, self.crypto_epoch = key_id, crypto_epoch

    def sign(self, payload: Mapping[str, object]) -> Mapping[str, object]:
        signature = Ed25519SignatureSuite().sign(
            dict(payload),
            "recovery_factor_receipt",
            self.key_id,
            self.private_key,
            self.crypto_epoch,
        )
        return {
            "alg": signature.alg,
            "key_id": signature.key_id,
            "crypto_epoch": signature.crypto_epoch,
            "sig": signature.signature,
            "public_key_fingerprint": signature.public_key_fingerprint,
        }

    def verify(self, payload: Mapping[str, object], signature: Mapping[str, object]) -> bool:
        if signature.get("alg") != "ed25519" or signature.get("key_id") != self.key_id:
            return False
        value = signature.get("sig")
        if not isinstance(value, str):
            return False
        return (
            Ed25519SignatureSuite()
            .verify(dict(payload), "recovery_factor_receipt", self.public_key, value)
            .valid
        )


class LNURLRecoveryRevocationChecker(Protocol):
    def check_recovery_targets(self, **targets: str | None) -> Mapping[str, object]: ...


class LNURLRecoveryRepository:
    """Concurrency-safe orchestration state; k1 authority remains the shared registry."""

    def __init__(self, max_challenges_per_attempt: int = 5) -> None:
        self._challenges: dict[str, LNURLRecoveryChallenge] = {}
        self._registry_index: dict[str, str] = {}
        self._receipts: dict[str, LNURLRecoveryFactorReceipt] = {}
        self.max_challenges_per_attempt = max_challenges_per_attempt
        self._lock = threading.RLock()

    def create(self, challenge: LNURLRecoveryChallenge) -> None:
        with self._lock:
            count = sum(
                item.recovery_attempt_hash == challenge.recovery_attempt_hash
                and item.issued_at >= challenge.issued_at - timedelta(hours=1)
                for item in self._challenges.values()
            )
            if count >= self.max_challenges_per_attempt:
                raise RecoveryFactorError("lnurl_recovery_rate_limited")
            self._challenges[challenge.challenge_id] = challenge
            self._registry_index[challenge.registry_id] = challenge.challenge_id

    def by_registry_id(self, registry_id: str) -> LNURLRecoveryChallenge | None:
        with self._lock:
            challenge_id = self._registry_index.get(registry_id)
            return self._challenges.get(challenge_id) if challenge_id else None

    def update(self, challenge: LNURLRecoveryChallenge) -> None:
        with self._lock:
            self._challenges[challenge.challenge_id] = challenge

    def store_receipt_once(self, receipt_hash: str, receipt: LNURLRecoveryFactorReceipt) -> bool:
        with self._lock:
            if receipt_hash in self._receipts:
                return False
            self._receipts[receipt_hash] = receipt
            return True

    def receipt(self, receipt_hash: str) -> LNURLRecoveryFactorReceipt | None:
        with self._lock:
            return self._receipts.get(receipt_hash)

    def challenges(self) -> tuple[LNURLRecoveryChallenge, ...]:
        with self._lock:
            return tuple(self._challenges.values())

    def revoke_receipts(self, recovery_attempt_hash: str) -> int:
        with self._lock:
            count = 0
            for receipt_hash, receipt in tuple(self._receipts.items()):
                if (
                    receipt.recovery_attempt_hash == recovery_attempt_hash
                    and receipt.status is LNURLRecoveryFactorStatus.VERIFIED
                ):
                    self._receipts[receipt_hash] = replace(
                        receipt, status=LNURLRecoveryFactorStatus.REVOKED
                    )
                    count += 1
            return count


class LNURLRecoveryFactorVerifier:
    factor_type = RecoveryFactorType.LNURL_AUTH_PROOF
    enabled = True

    def __init__(
        self,
        repository: LNURLRecoveryRepository,
        clock: Callable[[], datetime],
        receipt_signer: RecoveryReceiptSigner,
    ) -> None:
        self.repository, self.clock, self.receipt_signer = repository, clock, receipt_signer

    async def verify(
        self,
        capsule: RecoveryCapsule,
        submission: RecoveryFactorSubmission,
        context: RecoveryVerificationContext,
    ) -> RecoveryFactorResult:
        receipt = self.repository.receipt(submission.proof_reference_hash)
        valid = (
            receipt is not None
            and receipt.status is LNURLRecoveryFactorStatus.VERIFIED
            and receipt.recovery_attempt_hash == capsule.capsule_hash
            and receipt.principal_hash == capsule.principal_hash
            and receipt.policy_hash == capsule.policy_hash
            and receipt.expires_at > self.clock()
            and self.receipt_signer.verify(receipt.safe_payload(), receipt.issuer_signature)
            and not context.revocation_state.get("factor_revoked")
        )
        if not valid or receipt is None:
            raise RecoveryFactorError("lnurl_recovery_receipt_invalid")
        safe_receipt = receipt.safe_payload()
        safe_receipt["issuer_signature_metadata"] = dict(receipt.issuer_signature)
        return RecoveryFactorResult(
            True,
            self.factor_type,
            receipt.proof_hash,
            receipt.verification_strength,
            receipt.verified_at,
            receipt.expires_at,
            "lnurl_recovery_factor_verified",
            receipt.limitations,
            {"factor_receipt": safe_receipt},
            True,
            submission.proof_reference_hash,
        )


AuditEmitter = Callable[[str, Mapping[str, object]], None]
MetricEmitter = Callable[[str, Mapping[str, str]], None]


class LNURLRecoveryFactorService:
    def __init__(
        self,
        *,
        config: LNURLRecoveryConfig,
        capsule_service: RecoveryCapsuleService,
        k1_registry: LNURLK1RegistryService,
        callback_verifier: LNURLAuthCallbackVerifier,
        challenge_repository: InMemoryLNURLAuthChallengeRepository,
        receipt_signer: RecoveryReceiptSigner,
        revocation_checker: LNURLRecoveryRevocationChecker,
        repository: LNURLRecoveryRepository | None = None,
        clock: Callable[[], datetime] | None = None,
        audit_emitter: AuditEmitter | None = None,
        metric_emitter: MetricEmitter | None = None,
    ) -> None:
        self.config, self.capsules, self.k1_registry = config, capsule_service, k1_registry
        self.callback_verifier, self.challenge_repository = callback_verifier, challenge_repository
        self.receipt_signer, self.revocations = receipt_signer, revocation_checker
        self.repository = repository or LNURLRecoveryRepository(config.max_challenges_per_attempt)
        self.clock = clock or (lambda: datetime.now(UTC))
        self.audit_emitter, self.metric_emitter = audit_emitter, metric_emitter
        self.capsules.set_factor_receipt_validator(self)

    def factor_verifier(self) -> LNURLRecoveryFactorVerifier:
        return LNURLRecoveryFactorVerifier(self.repository, self.clock, self.receipt_signer)

    def validate_stored_receipt(self, receipt: dict[str, object]) -> bool:
        signature = receipt.get("issuer_signature_metadata")
        if not isinstance(signature, dict):
            return False
        payload = {
            key: value for key, value in receipt.items() if key != "issuer_signature_metadata"
        }
        return self.receipt_signer.verify(payload, signature)

    def issue_challenge(
        self,
        *,
        recovery_attempt_hash: str,
        lnurl_principal_hash: str,
        expected_lnurl_key_hash: str,
        device_context_hash: str | None = None,
    ) -> LNURLRecoveryChallengeResult:
        capsule = self.capsules.get(recovery_attempt_hash)
        self._ensure_attempt_accepts_factor(capsule)
        revocation = self.revocations.check_recovery_targets(
            recovery_attempt=recovery_attempt_hash,
            recovery_capsule=capsule.capsule_hash,
            lightning_principal=lnurl_principal_hash,
        )
        if any(bool(value) for value in revocation.values()):
            raise RecoveryFactorError("lnurl_recovery_unavailable")
        now = self.clock()
        issued = self.k1_registry.issue_k1(
            LNURLK1Purpose.RECOVERY_FACTOR,
            self.config.auth_domain,
            lnurl_action=LNURLAuthAction.AUTH.value,
            internal_action=RECOVERY_INTERNAL_ACTION,
            policy_hash=capsule.policy_hash,
            principal_hash=capsule.principal_hash,
            device_key_fingerprint=device_context_hash,
            recovery_attempt_hash=capsule.capsule_hash,
            ttl_seconds=self.config.ttl_seconds,
            max_failures=self.config.max_failed_callbacks,
        )
        intent = LNURLRecoveryIntent(
            RECOVERY_INTENT_TYPE,
            1,
            self.config.auth_domain,
            LNURLAuthAction.AUTH.value,
            RECOVERY_INTERNAL_ACTION,
            "recovery",
            capsule.capsule_hash,
            issued.k1_fingerprint,
            capsule.principal_hash,
            device_context_hash,
            capsule.policy_hash,
            capsule.recovery_profile.value,
            "critical",
            now,
            issued.expires_at,
        )
        intent_hash = sha256_prefixed(canonical_json(intent.canonical_payload()))
        challenge_id = sha256_prefixed(f"lnurl-recovery:{issued.registry_id}")
        callback_url = urlunsplit(
            (
                "https",
                self.config.auth_domain,
                self.config.callback_path,
                urlencode({"k1": issued.k1, "action": LNURLAuthAction.AUTH.value}),
                "",
            )
        )
        lnurl = encode_lnurl(callback_url).upper()
        generic = LNURLAuthChallengeRecord(
            challenge_id,
            issued.registry_id,
            issued.k1_fingerprint,
            LNURLAuthAction.AUTH,
            RECOVERY_INTERNAL_ACTION,
            "recovery",
            self.config.auth_domain,
            f"https://{self.config.auth_domain}",
            sha256_prefixed(f"https://{self.config.auth_domain}"),
            callback_url,
            lnurl,
            device_context_hash,
            capsule.principal_hash,
            (),
            capsule.policy_hash,
            intent_hash,
            "critical",
            now,
            issued.expires_at,
            LNURLAuthChallengeStatus.PENDING,
            capsule.policy_epoch,
            capsule.crypto_epoch,
        )
        self.challenge_repository.create(generic)
        challenge = LNURLRecoveryChallenge(
            challenge_id,
            issued.registry_id,
            capsule.capsule_hash,
            capsule.principal_hash,
            lnurl_principal_hash,
            expected_lnurl_key_hash,
            hmac_sha256_prefixed(self.k1_registry.config.server_pepper, self.config.auth_domain),
            issued.k1_fingerprint,
            intent_hash,
            capsule.policy_hash,
            capsule.recovery_profile,
            now,
            issued.expires_at,
            LNURLRecoveryFactorStatus.CHALLENGE_ISSUED,
        )
        try:
            self.repository.create(challenge)
        except RecoveryFactorError:
            self.k1_registry.revoke_k1(
                registry_id=issued.registry_id,
                reason_code="lnurl_recovery_rate_limited",
            )
            self._emit("lnurl_recovery_factor_rejected", challenge, "rate_limited")
            self._metric(
                "bastion_lnurl_recovery_rate_limited_total",
                challenge,
                "deny",
                "rate_limited",
            )
            raise
        self._emit("lnurl_recovery_factor_requested", challenge, "requested")
        self._emit("lnurl_recovery_challenge_created", challenge, "challenge_issued")
        self._metric(
            "bastion_lnurl_recovery_factor_requested_total",
            challenge,
            "pending",
            "requested",
        )
        remaining = max(1, capsule.required_factor_count - len(capsule.verified_factors))
        return LNURLRecoveryChallengeResult(
            "bastion_lnurl_recovery_factor",
            capsule.capsule_id,
            lnurl,
            lnurl,
            issued.expires_at,
            LNURLRecoveryFactorStatus.CHALLENGE_ISSUED,
            remaining,
        )

    async def verify_callback(
        self,
        *,
        k1: str,
        key: str,
        sig: str,
        callback_host: str,
    ) -> LNURLAuthCallbackResponse:
        status = self.k1_registry.get_k1_status(k1)
        challenge = self.repository.by_registry_id(status.registry_id or "")
        if challenge is None:
            return self._reject(None, "unknown_challenge")
        self._emit("lnurl_recovery_callback_received", challenge, "callback_received")
        if status.status is LNURLK1Status.EXPIRED:
            return self._reject(challenge, "k1_expired")
        if status.status is LNURLK1Status.CONSUMED:
            return self._reject(challenge, "k1_reused")
        if status.status is not LNURLK1Status.ACTIVE:
            return self._reject(challenge, "challenge_unavailable")
        try:
            capsule = self.capsules.get(challenge.recovery_attempt_hash)
            self._ensure_attempt_accepts_factor(capsule)
            if capsule.policy_hash != challenge.policy_hash:
                self._record_failure(k1, challenge, "policy_mismatch")
                return self._reject(challenge, "policy_mismatch")
            key_bytes = bytes.fromhex(key)
            derived_key_hash = hmac_sha256_prefixed(
                self.callback_verifier.config.principal_server_pepper, key_bytes
            )
            if not hmac.compare_digest(derived_key_hash, challenge.expected_lnurl_key_hash):
                self._record_failure(k1, challenge, "principal_mismatch")
                return self._reject(challenge, "principal_mismatch")
            revoked = self.revocations.check_recovery_targets(
                recovery_attempt=challenge.recovery_attempt_hash,
                recovery_capsule=challenge.recovery_attempt_hash,
                lightning_principal=challenge.lnurl_principal_hash,
                lnurl_auth_key=derived_key_hash,
                lnurl_k1=challenge.challenge_hash,
            )
            if any(bool(value) for value in revoked.values()):
                self._record_failure(k1, challenge, "revoked")
                return self._reject(challenge, "revoked")
            allowed, _reason = self.capsules.policy_authorizer.authorize(
                action=RECOVERY_INTERNAL_ACTION, capsule=capsule
            )
            if not allowed:
                self._record_failure(k1, challenge, "policy_denied")
                return self._reject(challenge, "policy_denied")
        except (ValueError, TypeError, RecoveryFactorError):
            self._record_failure(k1, challenge, "recovery_unavailable")
            return self._reject(challenge, "recovery_unavailable")
        result = self.callback_verifier.verify_callback(
            k1=k1,
            key=key,
            sig=sig,
            action=LNURLAuthAction.AUTH,
            callback_host=callback_host,
        )
        if not result.verified or result.proof is None or result.verified_at is None:
            self._record_failure(k1, challenge, result.reason_code)
            return self._reject(challenge, result.reason_code)
        proof_hash = sha256_prefixed(
            canonical_json(
                {
                    "challenge_hash": challenge.challenge_hash,
                    "lnurl_key_hash": result.lnurl_key_hash,
                    "intent_hash": challenge.intent_hash,
                    "verified_at": result.verified_at.isoformat(),
                }
            )
        )
        unsigned = LNURLRecoveryFactorReceipt(
            "bastion_recovery_factor_receipt",
            1,
            RecoveryFactorType.LNURL_AUTH_PROOF.value,
            challenge.recovery_attempt_hash,
            challenge.principal_hash,
            challenge.lnurl_principal_hash,
            challenge.auth_domain_hash,
            proof_hash,
            challenge.challenge_hash,
            "standard",
            result.verified_at,
            min(challenge.expires_at, capsule.expires_at),
            LNURLRecoveryFactorStatus.VERIFIED,
            (
                "not_a_bearer_credential",
                "not_bitcoin_treasury_ownership",
                "additional_recovery_factors_required",
            ),
            challenge.policy_hash,
            capsule.crypto_epoch,
            {},
        )
        signature = self.receipt_signer.sign(unsigned.safe_payload())
        receipt = replace(unsigned, issuer_signature=signature)
        receipt_hash = sha256_prefixed(
            canonical_json({**receipt.safe_payload(), "issuer_signature": dict(signature)})
        )
        if not self.repository.store_receipt_once(receipt_hash, receipt):
            return self._reject(challenge, "duplicate_callback")
        submission = RecoveryFactorSubmission(
            RecoveryFactorType.LNURL_AUTH_PROOF,
            receipt_hash,
            proof_hash,
            result.verified_at,
            {"receipt_hash": receipt_hash},
        )
        try:
            await self.capsules.submit_factor(
                capsule_hash=challenge.recovery_attempt_hash, submission=submission
            )
        except Exception:
            self.repository.update(replace(challenge, status=LNURLRecoveryFactorStatus.REJECTED))
            return self._reject(challenge, "factor_acceptance_failed")
        self.repository.update(
            replace(
                challenge,
                status=LNURLRecoveryFactorStatus.CONSUMED,
                receipt_hash=receipt_hash,
            )
        )
        self._emit("lnurl_recovery_factor_verified", challenge, "verified")
        self._emit(
            "lnurl_recovery_additional_factor_required", challenge, "additional_factor_required"
        )
        self._metric("bastion_lnurl_recovery_factor_verified_total", challenge, "allow", "verified")
        return LNURLAuthCallbackResponse(LNURLAuthCallbackStatus.OK)

    def revoke_attempt(self, recovery_attempt_hash: str) -> int:
        count = self.k1_registry.revoke_active_k1_for_binding(
            reason_code="recovery_attempt_revoked",
            recovery_attempt_hash=recovery_attempt_hash,
        )
        for record in self.repository.challenges():
            if record.recovery_attempt_hash == recovery_attempt_hash:
                self.repository.update(replace(record, status=LNURLRecoveryFactorStatus.REVOKED))
                self._emit("lnurl_recovery_factor_revoked", record, "revoked")
        return count + self.repository.revoke_receipts(recovery_attempt_hash)

    def _record_failure(self, k1: str, challenge: LNURLRecoveryChallenge, reason: str) -> None:
        failure = self.k1_registry.record_k1_failure(k1, reason)
        status = (
            LNURLRecoveryFactorStatus.REJECTED
            if failure.terminal
            else LNURLRecoveryFactorStatus.CALLBACK_RECEIVED
        )
        self.repository.update(
            replace(
                challenge,
                status=status,
                failed_callbacks=challenge.failed_callbacks + 1,
            )
        )

    def _ensure_attempt_accepts_factor(self, capsule: RecoveryCapsule) -> None:
        if capsule.status not in {
            RecoveryCapsuleStatus.AWAITING_FACTORS,
            RecoveryCapsuleStatus.FACTOR_VERIFICATION_IN_PROGRESS,
        }:
            raise RecoveryFactorError("lnurl_recovery_attempt_not_active")
        if capsule.expires_at <= self.clock():
            raise RecoveryFactorError("lnurl_recovery_attempt_expired")
        if (
            RecoveryFactorType.LNURL_AUTH_PROOF
            not in PROFILE_REQUIREMENTS[capsule.recovery_profile].allowed_factors
        ):
            raise RecoveryFactorError("lnurl_recovery_factor_not_allowed")

    def _reject(
        self, challenge: LNURLRecoveryChallenge | None, reason: str
    ) -> LNURLAuthCallbackResponse:
        if challenge is not None:
            event = {
                "k1_expired": "lnurl_recovery_k1_expired",
                "k1_reused": "lnurl_recovery_k1_reused",
                "principal_mismatch": "lnurl_recovery_principal_mismatch",
            }.get(reason, "lnurl_recovery_factor_rejected")
            self._emit(event, challenge, reason)
            metric = {
                "k1_expired": "bastion_lnurl_recovery_k1_expired_total",
                "k1_reused": "bastion_lnurl_recovery_k1_reused_total",
                "principal_mismatch": "bastion_lnurl_recovery_principal_mismatch_total",
                "policy_denied": "bastion_lnurl_recovery_policy_denied_total",
            }.get(reason, "bastion_lnurl_recovery_factor_failed_total")
            self._metric(metric, challenge, "deny", reason)
        return LNURLAuthCallbackResponse(LNURLAuthCallbackStatus.ERROR, RECOVERY_PUBLIC_ERROR)

    def _emit(self, event: str, challenge: LNURLRecoveryChallenge, reason: str) -> None:
        if self.audit_emitter:
            self.audit_emitter(
                event,
                {
                    "recovery_attempt_hash": challenge.recovery_attempt_hash,
                    "principal_hash": challenge.principal_hash,
                    "lnurl_principal_hash": challenge.lnurl_principal_hash,
                    "challenge_hash": challenge.challenge_hash,
                    "auth_domain_hash": challenge.auth_domain_hash,
                    "policy_hash": challenge.policy_hash,
                    "verification_strength": "standard",
                    "reason_code": reason,
                    "timestamp": self.clock().isoformat(),
                },
            )

    def _metric(
        self, name: str, challenge: LNURLRecoveryChallenge, decision: str, reason: str
    ) -> None:
        if self.metric_emitter:
            try:
                self.metric_emitter(
                    name,
                    {
                        "recovery_profile": challenge.recovery_profile.value,
                        "verification_strength": "standard",
                        "decision": decision,
                        "reason_code": reason,
                        "environment": "unknown",
                    },
                )
            except Exception:
                pass


__all__ = [
    "Ed25519RecoveryReceiptSigner",
    "LNURLRecoveryChallengeResult",
    "LNURLRecoveryConfig",
    "LNURLRecoveryFactorReceipt",
    "LNURLRecoveryFactorService",
    "LNURLRecoveryFactorStatus",
    "LNURLRecoveryFactorVerifier",
    "LNURLRecoveryIntent",
    "LNURLRecoveryRepository",
    "RECOVERY_PUBLIC_MESSAGE",
    "RECOVERY_WARNING",
    "SAFETY_WARNING",
]
