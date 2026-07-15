"""LNURL-auth callback verifier.

This verifier proves control of a domain-specific LNURL-auth linking key. It
never creates principals, device bindings, sessions, entitlements, Access
Certificates, or protected API authorization by itself.
"""
from __future__ import annotations

import re
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, utils

from app.domain.lnurl.auth import LNURLAuthAction
from app.domain.wallet_auth.proofs import WalletVerificationStrength
from app.services.access.crypto.hashing import canonical_json, hmac_sha256_prefixed, sha256_prefixed
from app.services.lnurl.auth_challenge_service import InMemoryLNURLAuthChallengeRepository, LNURLAuthChallengeRecord
from app.services.lnurl.errors import (
    LNURLAuthActionMismatchError,
    LNURLAuthCallbackError,
    LNURLAuthChallengeExpiredError,
    LNURLAuthChallengeUsedError,
    LNURLAuthDomainMismatchError,
    LNURLAuthInternalVerificationError,
    LNURLAuthInvalidPublicKeyError,
    LNURLAuthInvalidSignatureError,
    LNURLAuthMalformedK1Error,
    LNURLAuthMalformedSignatureError,
    LNURLAuthPolicyIntentMismatchError,
    LNURLAuthReplayDetectedError,
    LNURLAuthUnknownChallengeError,
    LNURLK1ConsumedError,
    LNURLK1ExpiredError,
    LNURLK1RevokedError,
)
from app.services.lnurl.k1_registry import LNURLK1RegistryService, LNURLK1Status
from app.services.lnurl.redaction import redact_lnurl_url

K1_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
COMPRESSED_SECP256K1_RE = re.compile(r"^(02|03)[0-9a-f]{64}$")
DER_SIGNATURE_RE = re.compile(r"^[0-9a-f]+$")
MAX_SIGNATURE_HEX_LENGTH = 160
MAX_ACTION_LENGTH = 16
LNURL_AUTH_PUBLIC_ERROR_REASON = "Authentication request could not be verified."
SECP256K1_ORDER = int("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141", 16)


class LNURLAuthCallbackStatus(StrEnum):
    OK = "OK"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class LNURLAuthCallbackConfig:
    canonical_domain: str = "auth.bitcoin-bastion.com"
    allowed_callback_hosts: frozenset[str] = frozenset({"auth.bitcoin-bastion.com"})
    principal_server_pepper: str = "test-lnurl-principal-pepper"
    allow_test_pepper: bool = True
    strict_query_params: bool = True
    max_signature_hex_length: int = MAX_SIGNATURE_HEX_LENGTH
    enforce_low_s: bool = True

    def __post_init__(self) -> None:
        if not self.canonical_domain or not self.allowed_callback_hosts:
            raise LNURLAuthInternalVerificationError("lnurl_auth_callback_config_invalid")
        if not self.principal_server_pepper or (not self.allow_test_pepper and self.principal_server_pepper.startswith("test-")):
            raise LNURLAuthInternalVerificationError("lnurl_principal_pepper_required")


@dataclass(frozen=True, slots=True)
class LNURLAuthCallbackRequest:
    k1: str
    key: str
    sig: str
    action: LNURLAuthAction | None = None


@dataclass(frozen=True, slots=True)
class LNURLAuthCallbackResponse:
    status: LNURLAuthCallbackStatus
    reason: str | None = None

    def as_lnurl_json(self) -> dict[str, str]:
        if self.status is LNURLAuthCallbackStatus.OK:
            return {"status": self.status.value}
        return {"status": self.status.value, "reason": self.reason or LNURL_AUTH_PUBLIC_ERROR_REASON}


@dataclass(frozen=True, slots=True)
class VerifiedLNURLAuthProof:
    lnurl_key_hash: str
    key_fingerprint: str
    auth_domain: str
    lnurl_action: LNURLAuthAction
    bastion_action: str
    challenge_id: str
    policy_intent_hash: str
    verification_strength: WalletVerificationStrength
    device_key_fingerprint: str | None
    verified_at: datetime


@dataclass(frozen=True, slots=True)
class LNURLAuthVerificationResult:
    verified: bool
    challenge_id: str | None
    challenge_type: str
    lnurl_action: LNURLAuthAction | None
    bastion_action: str | None
    key_fingerprint: str | None
    lnurl_key_hash: str | None
    verification_strength: WalletVerificationStrength | None
    auth_domain: str | None
    device_key_fingerprint: str | None
    policy_intent_hash: str | None
    principal_lookup_hint: str | None
    verified_at: datetime | None
    reason_code: str
    limitations: tuple[str, ...] = ()
    proof: VerifiedLNURLAuthProof | None = None
    response: LNURLAuthCallbackResponse = field(default_factory=lambda: LNURLAuthCallbackResponse(LNURLAuthCallbackStatus.ERROR, LNURL_AUTH_PUBLIC_ERROR_REASON))


@dataclass(frozen=True, slots=True)
class LNURLAuthAttemptRecord:
    attempt_hash: str
    challenge_id: str | None
    result: str
    reason_code: str
    key_fingerprint: str | None
    auth_domain: str | None
    policy_intent_hash: str | None
    created_at: datetime
    completed_at: datetime


class InMemoryLNURLAuthAttemptRepository:
    def __init__(self) -> None:
        self._attempts: list[LNURLAuthAttemptRecord] = []
        self._lock = threading.Lock()

    def record(self, attempt: LNURLAuthAttemptRecord) -> None:
        with self._lock:
            self._attempts.append(attempt)

    def attempts(self) -> tuple[LNURLAuthAttemptRecord, ...]:
        with self._lock:
            return tuple(self._attempts)


class RevocationChecker(Protocol):
    def is_revoked(self, *, subject_type: str, subject_hash: str) -> bool: ...


class PolicyPrecheck(Protocol):
    def check(self, *, action: str, policy_hash: str, auth_domain: str) -> None: ...


AuditEmitter = Callable[[str, Mapping[str, Any]], None]
MetricsEmitter = Callable[[str, Mapping[str, str]], None]


class LNURLAuthCallbackVerifier:
    def __init__(
        self,
        *,
        config: LNURLAuthCallbackConfig,
        k1_registry: LNURLK1RegistryService,
        challenge_repository: InMemoryLNURLAuthChallengeRepository,
        attempt_repository: InMemoryLNURLAuthAttemptRepository | None = None,
        revocation_checker: RevocationChecker | None = None,
        policy_precheck: PolicyPrecheck | None = None,
        clock: Callable[[], datetime] | None = None,
        audit_emitter: AuditEmitter | None = None,
        metrics_emitter: MetricsEmitter | None = None,
    ) -> None:
        self.config = config
        self.k1_registry = k1_registry
        self.challenge_repository = challenge_repository
        self.attempt_repository = attempt_repository or InMemoryLNURLAuthAttemptRepository()
        self.revocation_checker = revocation_checker
        self.policy_precheck = policy_precheck
        self.clock = clock or (lambda: datetime.now(UTC))
        self.audit_emitter = audit_emitter
        self.metrics_emitter = metrics_emitter

    def verify_callback(
        self,
        *,
        k1: str,
        key: str,
        sig: str,
        action: LNURLAuthAction | str | None = None,
        callback_host: str | None = None,
        query_params: Mapping[str, str | list[str] | tuple[str, ...]] | None = None,
    ) -> LNURLAuthVerificationResult:
        started_at = self.clock()
        request: LNURLAuthCallbackRequest | None = None
        record: LNURLAuthChallengeRecord | None = None
        key_fingerprint: str | None = None
        lnurl_key_hash: str | None = None
        reason_code = "unknown_error"
        try:
            self._validate_query_params(query_params)
            request = self._validate_request(k1=k1, key=key, sig=sig, action=action)
            self._check_callback_host(callback_host)
            status = self.k1_registry.get_k1_status(request.k1)
            if status.registry_id is None:
                raise LNURLAuthUnknownChallengeError()
            if status.status is LNURLK1Status.EXPIRED:
                raise LNURLAuthChallengeExpiredError()
            if status.status is LNURLK1Status.CONSUMED:
                raise LNURLAuthChallengeUsedError()
            if status.status is not LNURLK1Status.ACTIVE:
                raise LNURLAuthUnknownChallengeError()
            record = self._challenge_by_registry_id(status.registry_id)
            if record is None:
                raise LNURLAuthUnknownChallengeError()
            self._check_challenge_bindings(record, request, callback_host)
            self._policy_precheck(record)
            key_bytes = bytes.fromhex(request.key)
            key_fingerprint = sha256_prefixed(key_bytes)
            lnurl_key_hash = hmac_sha256_prefixed(self.config.principal_server_pepper, key_bytes)
            self._revocation_check(record, lnurl_key_hash)
            self._verify_signature(k1=request.k1, key=request.key, sig=request.sig)
            consumed = self.k1_registry.consume_k1(
                request.k1,
                expected_purpose=status.purpose.value if status.purpose else None,
                expected_lnurl_action=record.lnurl_action.value,
                expected_internal_action=record.internal_action,
                expected_domain=record.auth_domain,
                expected_policy_hash=record.policy_hash,
                expected_principal_hash=record.principal_hint_hash,
                expected_device_key_fingerprint=record.device_key_fingerprint,
            )
            verified_at = consumed.consumed_at
            proof = VerifiedLNURLAuthProof(
                lnurl_key_hash=lnurl_key_hash,
                key_fingerprint=key_fingerprint,
                auth_domain=record.auth_domain,
                lnurl_action=record.lnurl_action,
                bastion_action=record.internal_action,
                challenge_id=record.challenge_id,
                policy_intent_hash=record.internal_intent_hash,
                verification_strength=WalletVerificationStrength.STANDARD,
                device_key_fingerprint=record.device_key_fingerprint,
                verified_at=verified_at,
            )
            result = LNURLAuthVerificationResult(
                verified=True,
                challenge_id=record.challenge_id,
                challenge_type="lnurl_auth",
                lnurl_action=record.lnurl_action,
                bastion_action=record.internal_action,
                key_fingerprint=key_fingerprint,
                lnurl_key_hash=lnurl_key_hash,
                verification_strength=WalletVerificationStrength.STANDARD,
                auth_domain=record.auth_domain,
                device_key_fingerprint=record.device_key_fingerprint,
                policy_intent_hash=record.internal_intent_hash,
                principal_lookup_hint=record.principal_hint_hash,
                verified_at=verified_at,
                reason_code="verified",
                limitations=("lnurl_auth_is_not_bitcoin_treasury_ownership", "policy_engine_final_authorization_required"),
                proof=proof,
                response=LNURLAuthCallbackResponse(LNURLAuthCallbackStatus.OK),
            )
            self._record_attempt(result, started_at)
            self._audit("lnurl_auth_callback_success", result)
            self._metric("lnurl_auth_callback_total", result="success", reason_group="verified", action=record.lnurl_action.value)
            return result
        except Exception as exc:
            reason_code = _reason_code(exc)
            result = self._failure_result(reason_code, record, key_fingerprint, lnurl_key_hash, started_at)
            self._record_attempt(result, started_at)
            self._audit(_audit_event_for_reason(reason_code), result)
            self._metric("lnurl_auth_callback_total", result="error", reason_group=_reason_group(reason_code), action=record.lnurl_action.value if record else "unknown")
            return result

    def _validate_request(self, *, k1: str, key: str, sig: str, action: LNURLAuthAction | str | None) -> LNURLAuthCallbackRequest:
        for name, value in {"k1": k1, "key": key, "sig": sig}.items():
            if not isinstance(value, str) or any(ord(ch) < 32 for ch in value):
                raise LNURLAuthCallbackError(f"malformed_{name}")
        k1_norm = k1.lower()
        key_norm = key.lower()
        sig_norm = sig.lower()
        if K1_HEX_RE.fullmatch(k1_norm) is None:
            raise LNURLAuthMalformedK1Error()
        if COMPRESSED_SECP256K1_RE.fullmatch(key_norm) is None:
            raise LNURLAuthInvalidPublicKeyError()
        if len(sig_norm) > self.config.max_signature_hex_length or len(sig_norm) < 16 or DER_SIGNATURE_RE.fullmatch(sig_norm) is None:
            raise LNURLAuthMalformedSignatureError()
        action_value = None
        if action is not None:
            action_text = str(action.value if isinstance(action, LNURLAuthAction) else action)
            if len(action_text) > MAX_ACTION_LENGTH:
                raise LNURLAuthActionMismatchError()
            try:
                action_value = LNURLAuthAction(action_text)
            except ValueError as exc:
                raise LNURLAuthActionMismatchError() from exc
        return LNURLAuthCallbackRequest(k1_norm, key_norm, sig_norm, action_value)

    def _validate_query_params(self, query_params: Mapping[str, str | list[str] | tuple[str, ...]] | None) -> None:
        if not self.config.strict_query_params or query_params is None:
            return
        allowed = {"k1", "key", "sig", "action"}
        for key, value in query_params.items():
            if key not in allowed:
                raise LNURLAuthCallbackError("unexpected_callback_field")
            if isinstance(value, (list, tuple)) and len(value) != 1:
                raise LNURLAuthCallbackError("duplicate_callback_field")

    def _check_callback_host(self, callback_host: str | None) -> None:
        host = (callback_host or self.config.canonical_domain).rstrip(".").lower()
        allowed = {h.rstrip(".").lower() for h in self.config.allowed_callback_hosts}
        if host not in allowed or host != self.config.canonical_domain.rstrip(".").lower():
            raise LNURLAuthDomainMismatchError()

    def _challenge_by_registry_id(self, registry_id: str) -> LNURLAuthChallengeRecord | None:
        return next((record for record in self.challenge_repository.records() if record.registry_id == registry_id), None)

    def _check_challenge_bindings(self, record: LNURLAuthChallengeRecord, request: LNURLAuthCallbackRequest, callback_host: str | None) -> None:
        if record.auth_domain != self.config.canonical_domain:
            raise LNURLAuthDomainMismatchError()
        self._check_callback_host(callback_host or record.auth_domain)
        if request.action is not None and request.action is not record.lnurl_action:
            raise LNURLAuthActionMismatchError()
        if record.expires_at <= self.clock():
            raise LNURLAuthChallengeExpiredError()
        if record.policy_epoch < 1 or record.crypto_epoch < 1 or not record.internal_intent_hash:
            raise LNURLAuthPolicyIntentMismatchError()

    def _policy_precheck(self, record: LNURLAuthChallengeRecord) -> None:
        if self.policy_precheck is None:
            return
        self.policy_precheck.check(action=record.internal_action, policy_hash=record.policy_hash, auth_domain=record.auth_domain)

    def _revocation_check(self, record: LNURLAuthChallengeRecord, lnurl_key_hash: str) -> None:
        if self.revocation_checker is None:
            return
        checks = [("lnurl_key", lnurl_key_hash), ("policy_intent", record.internal_intent_hash)]
        if record.device_key_fingerprint:
            checks.append(("device", record.device_key_fingerprint))
        for subject_type, subject_hash in checks:
            if self.revocation_checker.is_revoked(subject_type=subject_type, subject_hash=subject_hash):
                raise LNURLAuthUnknownChallengeError()

    def _verify_signature(self, *, k1: str, key: str, sig: str) -> None:
        key_bytes = bytes.fromhex(key)
        sig_bytes = bytes.fromhex(sig)
        try:
            utils.decode_dss_signature(sig_bytes)
        except ValueError as exc:
            raise LNURLAuthMalformedSignatureError() from exc
        if self.config.enforce_low_s:
            _, s_value = utils.decode_dss_signature(sig_bytes)
            if s_value > SECP256K1_ORDER // 2:
                raise LNURLAuthInvalidSignatureError()
        try:
            public_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), key_bytes)
            # LNURL-auth signs the 32-byte k1 challenge as the digest. The
            # Prehashed adapter avoids hashing the challenge a second time.
            public_key.verify(sig_bytes, bytes.fromhex(k1), ec.ECDSA(utils.Prehashed(hashes.SHA256())))
        except ValueError as exc:
            raise LNURLAuthInvalidPublicKeyError() from exc
        except InvalidSignature as exc:
            raise LNURLAuthInvalidSignatureError() from exc

    def _failure_result(
        self,
        reason_code: str,
        record: LNURLAuthChallengeRecord | None,
        key_fingerprint: str | None,
        lnurl_key_hash: str | None,
        started_at: datetime,
    ) -> LNURLAuthVerificationResult:
        return LNURLAuthVerificationResult(
            verified=False,
            challenge_id=record.challenge_id if record else None,
            challenge_type="lnurl_auth",
            lnurl_action=record.lnurl_action if record else None,
            bastion_action=record.internal_action if record else None,
            key_fingerprint=key_fingerprint,
            lnurl_key_hash=lnurl_key_hash,
            verification_strength=None,
            auth_domain=record.auth_domain if record else None,
            device_key_fingerprint=record.device_key_fingerprint if record else None,
            policy_intent_hash=record.internal_intent_hash if record else None,
            principal_lookup_hint=record.principal_hint_hash if record else None,
            verified_at=None,
            reason_code=reason_code,
            limitations=("generic_public_error",),
            response=LNURLAuthCallbackResponse(LNURLAuthCallbackStatus.ERROR, LNURL_AUTH_PUBLIC_ERROR_REASON),
        )

    def _record_attempt(self, result: LNURLAuthVerificationResult, started_at: datetime) -> None:
        completed = self.clock()
        attempt_hash = sha256_prefixed(canonical_json({
            "challenge_id": result.challenge_id,
            "result": "verified" if result.verified else "failed",
            "reason_code": result.reason_code,
            "created_at": started_at.isoformat(),
        }))
        self.attempt_repository.record(LNURLAuthAttemptRecord(
            attempt_hash=attempt_hash,
            challenge_id=result.challenge_id,
            result="verified" if result.verified else "failed",
            reason_code=result.reason_code,
            key_fingerprint=result.key_fingerprint,
            auth_domain=result.auth_domain,
            policy_intent_hash=result.policy_intent_hash,
            created_at=started_at,
            completed_at=completed,
        ))

    def _audit(self, event: str, result: LNURLAuthVerificationResult) -> None:
        if self.audit_emitter is None:
            return
        self.audit_emitter(event, {
            "challenge_id_hash": sha256_prefixed(result.challenge_id or "unknown"),
            "key_fingerprint": result.key_fingerprint,
            "auth_domain_hash": sha256_prefixed(result.auth_domain or "unknown"),
            "policy_intent_hash": result.policy_intent_hash,
            "action": result.lnurl_action.value if result.lnurl_action else None,
            "result": "verified" if result.verified else "failed",
            "reason_code": result.reason_code,
            "timestamp": self.clock().isoformat(),
        })

    def _metric(self, name: str, *, result: str, reason_group: str, action: str) -> None:
        if self.metrics_emitter is None:
            return
        self.metrics_emitter(name, {"result": result, "reason_group": reason_group, "action": action})


def public_callback_error_response() -> LNURLAuthCallbackResponse:
    return LNURLAuthCallbackResponse(LNURLAuthCallbackStatus.ERROR, LNURL_AUTH_PUBLIC_ERROR_REASON)


def safe_callback_log_url(url: str) -> str:
    return redact_lnurl_url(url)


def _reason_code(exc: Exception) -> str:
    if isinstance(exc, LNURLAuthMalformedK1Error):
        return "malformed_k1"
    if isinstance(exc, LNURLAuthUnknownChallengeError):
        return "unknown_k1"
    if isinstance(exc, LNURLAuthChallengeExpiredError):
        return "expired_k1"
    if isinstance(exc, LNURLAuthChallengeUsedError | LNURLAuthReplayDetectedError | LNURLK1ConsumedError):
        return "reused_k1"
    if isinstance(exc, LNURLAuthActionMismatchError):
        return "action_mismatch"
    if isinstance(exc, LNURLAuthDomainMismatchError):
        return "domain_mismatch"
    if isinstance(exc, LNURLAuthPolicyIntentMismatchError):
        return "policy_intent_mismatch"
    if isinstance(exc, LNURLAuthInvalidPublicKeyError):
        return "invalid_public_key"
    if isinstance(exc, LNURLAuthMalformedSignatureError):
        return "malformed_signature"
    if isinstance(exc, LNURLAuthInvalidSignatureError):
        return "invalid_signature"
    if isinstance(exc, LNURLK1ExpiredError):
        return "expired_k1"
    if isinstance(exc, LNURLK1RevokedError):
        return "revoked_k1"
    return getattr(exc, "code", "internal_verification_error")


def _reason_group(reason_code: str) -> str:
    if "signature" in reason_code or "public_key" in reason_code:
        return "crypto"
    if "k1" in reason_code or "challenge" in reason_code:
        return "challenge"
    if "domain" in reason_code or "action" in reason_code or "policy" in reason_code:
        return "binding"
    return "internal"


def _audit_event_for_reason(reason_code: str) -> str:
    if reason_code == "unknown_k1":
        return "lnurl_auth_k1_unknown"
    if reason_code == "expired_k1":
        return "lnurl_auth_k1_expired"
    if reason_code == "reused_k1":
        return "lnurl_auth_k1_reused"
    if reason_code == "action_mismatch":
        return "lnurl_auth_action_mismatch"
    if reason_code == "domain_mismatch":
        return "lnurl_auth_domain_mismatch"
    if reason_code == "invalid_signature":
        return "lnurl_auth_signature_invalid"
    if reason_code == "policy_intent_mismatch":
        return "lnurl_auth_policy_intent_mismatch"
    return "lnurl_auth_callback_failed"


__all__ = [
    "LNURLAuthAttemptRecord",
    "LNURLAuthCallbackConfig",
    "LNURLAuthCallbackRequest",
    "LNURLAuthCallbackResponse",
    "LNURLAuthCallbackStatus",
    "LNURLAuthCallbackVerifier",
    "LNURLAuthVerificationResult",
    "VerifiedLNURLAuthProof",
    "InMemoryLNURLAuthAttemptRepository",
    "public_callback_error_response",
    "safe_callback_log_url",
]
