"""Wallet Proof-of-Possession request verifier.

This adapter reuses the shared Access PoP canonical request core and verifies
routine API requests for wallet-auth sessions. It never accepts bearer tokens,
raw wallet proofs, Bitcoin addresses, LNURL linking keys, or unsigned session
handles as authorization.
"""

from __future__ import annotations

import base64
import re
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.wallet_auth import WalletSession, WalletSessionNonce
from app.domain.wallet_auth.sessions import WalletSessionStatus
from app.services.access.crypto.hashing import constant_time_equal, sha256_prefixed
from app.services.access.crypto.signatures import Ed25519SignatureSuite, SignatureSuite
from app.services.access.pop.canonical_request import (
    POP_PROTOCOL_VERSION,
    build_pop_canonical_request,
    canonicalize_query_string,
    compute_body_sha256_hex,
    compute_pop_request_digest,
)
from app.services.wallet_auth.device_key_validation import compute_device_key_fingerprint
from app.services.wallet_auth.privacy_commitments import compute_hmac_lookup_hash
from app.services.wallet_auth.session_service import WalletSessionContext, WalletSessionService

HEADER_AUTHORIZATION = "authorization"
HEADER_TIMESTAMP = "bastion-request-timestamp"
HEADER_NONCE = "bastion-request-nonce"
HEADER_BODY_HASH = "bastion-request-body-hash"
HEADER_SIGNATURE = "bastion-request-signature"
HEADER_PRINCIPAL = "bastion-principal"
DEFAULT_WALLET_AUTH_POP_MAX_CLOCK_SKEW_SECONDS = 90
MAX_SESSION_TOKEN_LENGTH = 256
MAX_NONCE_LENGTH = 128
MAX_SIGNATURE_LENGTH = 512
_SIGNATURE_CONTEXT = "access_session"
_B64URL_RE = re.compile(r"^[A-Za-z0-9_-]+={0,2}$")
_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
AuditEmitter = Callable[[str, dict[str, object]], None]
Clock = Callable[[], datetime]


class WalletPoPError(ValueError):
    def __init__(self, reason_code: str) -> None:
        self.reason_code = reason_code
        super().__init__(reason_code)


class MissingPoPAuthorizationError(WalletPoPError): ...
class InvalidPoPAuthorizationError(WalletPoPError): ...
class InvalidPoPSessionError(WalletPoPError): ...
class InvalidPoPTimestampError(WalletPoPError): ...
class StalePoPRequestError(WalletPoPError): ...
class InvalidPoPNonceError(WalletPoPError): ...
class PoPReplayDetectedError(WalletPoPError): ...
class InvalidPoPBodyHashError(WalletPoPError): ...
class InvalidPoPSignatureError(WalletPoPError): ...
class UnsupportedPoPSignatureSuiteError(WalletPoPError): ...
class PoPPrincipalMismatchError(WalletPoPError): ...


@dataclass(frozen=True, slots=True)
class WalletPoPHeaders:
    session_token: str
    timestamp: str
    nonce: str
    body_hash: str
    signature: str
    bastion_principal: str | None = None

    @classmethod
    def parse(cls, headers: Mapping[str, str]) -> WalletPoPHeaders:
        normalized = {key.lower(): value for key, value in headers.items()}
        auth = normalized.get(HEADER_AUTHORIZATION)
        if not auth:
            raise MissingPoPAuthorizationError("missing_pop_authorization")
        scheme, _, token = auth.partition(" ")
        if scheme != "PoP" or not token:
            raise InvalidPoPAuthorizationError("invalid_pop_authorization_scheme")
        if token.lower().startswith("bearer") or len(token) > MAX_SESSION_TOKEN_LENGTH or not token.startswith("sess_"):
            raise InvalidPoPAuthorizationError("invalid_pop_session")
        timestamp = _required_header(normalized, HEADER_TIMESTAMP)
        nonce = _required_header(normalized, HEADER_NONCE)
        body_hash = _required_header(normalized, HEADER_BODY_HASH).lower()
        signature = _required_header(normalized, HEADER_SIGNATURE)
        if not timestamp.isdecimal():
            raise InvalidPoPTimestampError("invalid_pop_timestamp")
        _validate_nonce(nonce)
        if not _SHA256_HEX_RE.fullmatch(body_hash):
            raise InvalidPoPBodyHashError("invalid_body_hash")
        if not signature or len(signature) > MAX_SIGNATURE_LENGTH or not _B64URL_RE.fullmatch(signature):
            raise InvalidPoPSignatureError("invalid_pop_signature")
        return cls(
            session_token=token,
            timestamp=timestamp,
            nonce=nonce,
            body_hash=body_hash,
            signature=signature,
            bastion_principal=normalized.get(HEADER_PRINCIPAL),
        )


@dataclass(frozen=True, slots=True)
class VerifiedPoPContext:
    session_id_hash: str
    principal_hash: str
    actor_type: str
    device_binding_id: int
    device_key_fingerprint: str
    session_key_fingerprint: str
    signature_suite: str
    auth_method: str
    verification_strength: str
    scopes: tuple[str, ...]
    plan_code: str
    entitlement_id: str | None
    request_digest: str
    nonce_hash: str
    verified_at: datetime
    policy_epoch: int
    crypto_epoch: int
    requires_policy_decision: bool = True


class WalletPoPNonceRegistry(Protocol):
    async def consume_nonce_once(
        self,
        *,
        session_hash: str,
        nonce: str,
        request_digest: str,
        timestamp: datetime,
    ) -> str: ...

    async def cleanup_expired(self, *, before: datetime) -> int: ...


class InMemoryWalletPoPNonceRegistry:
    """Thread-safe test registry; production should use the SQLAlchemy registry."""

    def __init__(self, *, nonce_pepper: str | bytes = "test-wallet-pop-nonce-pepper") -> None:
        self.nonce_pepper = nonce_pepper
        self._seen: set[tuple[str, str]] = set()
        self._lock = threading.RLock()

    async def consume_nonce_once(self, *, session_hash: str, nonce: str, request_digest: str, timestamp: datetime) -> str:
        nonce_hash = _nonce_hash(self.nonce_pepper, session_hash, nonce)
        with self._lock:
            key = (session_hash, nonce_hash)
            if key in self._seen:
                raise PoPReplayDetectedError("pop_replay_detected")
            self._seen.add(key)
        return nonce_hash

    async def cleanup_expired(self, *, before: datetime) -> int:
        return 0


class SqlAlchemyWalletPoPNonceRegistry:
    """Durable session-scoped nonce registry backed by wallet_session_nonces."""

    def __init__(self, db: Session, *, nonce_pepper: str | bytes) -> None:
        self.db = db
        self.nonce_pepper = nonce_pepper

    async def consume_nonce_once(self, *, session_hash: str, nonce: str, request_digest: str, timestamp: datetime) -> str:
        nonce_hash = _nonce_hash(self.nonce_pepper, session_hash, nonce)
        session_id = self.db.scalar(select(WalletSession.id).where(WalletSession.session_hash == session_hash))
        if session_id is None:
            raise InvalidPoPSessionError("invalid_pop_session")
        self.db.add(
            WalletSessionNonce(
                session_id=session_id,
                session_hash=session_hash,
                nonce_hash=nonce_hash,
                request_digest_hash=sha256_prefixed(request_digest),
                timestamp=timestamp,
                used_at=timestamp,
            )
        )
        try:
            self.db.flush()
        except IntegrityError as exc:
            self.db.rollback()
            raise PoPReplayDetectedError("pop_replay_detected") from exc
        return nonce_hash

    async def cleanup_expired(self, *, before: datetime) -> int:
        rows = self.db.query(WalletSessionNonce).filter(WalletSessionNonce.timestamp < before).delete(synchronize_session=False)
        self.db.flush()
        return int(rows)


class WalletPoPRequestVerifier:
    def __init__(
        self,
        *,
        session_service: WalletSessionService,
        nonce_registry: WalletPoPNonceRegistry,
        signature_suite: SignatureSuite | None = None,
        clock: Clock | None = None,
        max_clock_skew_seconds: int = DEFAULT_WALLET_AUTH_POP_MAX_CLOCK_SKEW_SECONDS,
        audit_emitter: AuditEmitter | None = None,
    ) -> None:
        self.session_service = session_service
        self.nonce_registry = nonce_registry
        self.signature_suite = signature_suite or Ed25519SignatureSuite()
        self.clock = clock or (lambda: datetime.now(UTC))
        self.max_clock_skew_seconds = max_clock_skew_seconds
        self.audit_emitter = audit_emitter

    async def verify_request(
        self,
        *,
        method: str,
        path: str,
        query_string: str | bytes | None,
        body: bytes,
        headers: Mapping[str, str],
        allow_recovery_only: bool = False,
    ) -> VerifiedPoPContext:
        parsed = WalletPoPHeaders.parse(headers)
        timestamp = self._validate_timestamp(parsed.timestamp)
        actual_body_hash = compute_body_sha256_hex(body)
        if not constant_time_equal(actual_body_hash, parsed.body_hash):
            self._emit_denied("pop_body_hash_mismatch")
            raise InvalidPoPBodyHashError("pop_body_hash_mismatch")
        session = await self.session_service.validate_session_state(session_token=parsed.session_token)
        self._validate_session_context(session, parsed, allow_recovery_only=allow_recovery_only)
        canonical = build_pop_canonical_request(
            method=method,
            path=path,
            query_string=query_string,
            body_hash_hex=parsed.body_hash,
            timestamp=parsed.timestamp,
            nonce=parsed.nonce,
            session_binding=session.session_lookup_hash,
        )
        digest = compute_pop_request_digest(canonical)
        self._verify_signature(session=session, request_digest=digest, signature=parsed.signature)
        nonce_hash = await self.nonce_registry.consume_nonce_once(
            session_hash=session.session_lookup_hash,
            nonce=parsed.nonce,
            request_digest=digest,
            timestamp=timestamp,
        )
        verified = VerifiedPoPContext(
            session_id_hash=session.session_lookup_hash,
            principal_hash=session.principal_hash,
            actor_type=session.principal_type.value,
            device_binding_id=session.device_binding_id,
            device_key_fingerprint=session.device_key_fingerprint,
            session_key_fingerprint=session.session_public_key_fingerprint,
            signature_suite=self.signature_suite.alg,
            auth_method=session.auth_method,
            verification_strength=session.verification_strength.value,
            scopes=session.effective_scopes,
            plan_code=session.effective_plan,
            entitlement_id=session.entitlement_id,
            request_digest=digest,
            nonce_hash=nonce_hash,
            verified_at=self._now(),
            policy_epoch=session.policy_epoch,
            crypto_epoch=session.crypto_epoch,
        )
        self._emit_verified(verified, method=method, path=path)
        return verified

    def _validate_timestamp(self, timestamp: str) -> datetime:
        try:
            parsed = datetime.fromtimestamp(int(timestamp), tz=UTC)
        except (ValueError, OverflowError) as exc:
            raise InvalidPoPTimestampError("invalid_pop_timestamp") from exc
        now = self._now()
        if abs((now - parsed).total_seconds()) > self.max_clock_skew_seconds:
            raise StalePoPRequestError("stale_pop_request")
        return parsed

    def _validate_session_context(self, session: WalletSessionContext, headers: WalletPoPHeaders, *, allow_recovery_only: bool) -> None:
        if session.session_status is WalletSessionStatus.RECOVERY_ONLY and not allow_recovery_only:
            raise InvalidPoPSessionError("invalid_pop_session")
        if headers.bastion_principal is not None and headers.bastion_principal != session.principal_hash:
            raise PoPPrincipalMismatchError("session_principal_mismatch")
        if not session.session_public_key_b64 or not session.session_public_key_fingerprint:
            raise InvalidPoPSessionError("invalid_pop_session")

    def _verify_signature(self, *, session: WalletSessionContext, request_digest: str, signature: str) -> None:
        if session.session_public_key_fingerprint != compute_device_key_fingerprint(session.session_public_key_b64):
            raise InvalidPoPSignatureError("invalid_pop_signature")
        try:
            result = self.signature_suite.verify(request_digest, _SIGNATURE_CONTEXT, session.session_public_key_b64, signature)
        except Exception as exc:
            raise UnsupportedPoPSignatureSuiteError("unsupported_signature_suite") from exc
        if not result.valid:
            raise InvalidPoPSignatureError("invalid_pop_signature")

    def _now(self) -> datetime:
        now = self.clock()
        return now if now.tzinfo else now.replace(tzinfo=UTC)

    def _emit_verified(self, verified: VerifiedPoPContext, *, method: str, path: str) -> None:
        if self.audit_emitter is None:
            return
        self.audit_emitter(
            "wallet_pop_request_verified",
            {
                "session_id_hash": verified.session_id_hash,
                "principal_hash": verified.principal_hash,
                "actor_type": verified.actor_type,
                "plan": verified.plan_code,
                "signature_suite": verified.signature_suite,
                "method": method.upper(),
                "path": path,
                "request_digest": verified.request_digest,
            },
        )

    def _emit_denied(self, reason_code: str) -> None:
        if self.audit_emitter is None:
            return
        self.audit_emitter("wallet_pop_request_denied", {"reason_code": reason_code})


def build_wallet_pop_authorization_header(session_token: str) -> str:
    return f"PoP {session_token}"


def canonical_request_for_signing(
    *, method: str, path: str, query_string: str | bytes | None, body: bytes, timestamp: str, nonce: str, session_binding: str
) -> tuple[str, str, str]:
    body_hash = compute_body_sha256_hex(body)
    canonical = build_pop_canonical_request(
        method=method,
        path=path,
        query_string=query_string,
        body_hash_hex=body_hash,
        timestamp=timestamp,
        nonce=nonce,
        session_binding=session_binding,
    )
    return body_hash, canonical, compute_pop_request_digest(canonical)


def _required_header(headers: Mapping[str, str], name: str) -> str:
    value = headers.get(name)
    if value is None or value == "":
        raise MissingPoPAuthorizationError(f"missing_{name.replace('-', '_')}")
    return value


def _validate_nonce(nonce: str) -> None:
    if len(nonce) > MAX_NONCE_LENGTH or not _B64URL_RE.fullmatch(nonce):
        raise InvalidPoPNonceError("invalid_pop_nonce")
    try:
        decoded = base64.urlsafe_b64decode(nonce + "=" * (-len(nonce) % 4))
    except ValueError as exc:
        raise InvalidPoPNonceError("invalid_pop_nonce") from exc
    if not 16 <= len(decoded) <= 64:
        raise InvalidPoPNonceError("invalid_pop_nonce")


def _nonce_hash(nonce_pepper: str | bytes, session_hash: str, nonce: str) -> str:
    return compute_hmac_lookup_hash(nonce_pepper, "wallet_pop_nonce", f"{session_hash}\x00{nonce}")


__all__ = [
    "POP_PROTOCOL_VERSION",
    "InMemoryWalletPoPNonceRegistry",
    "SqlAlchemyWalletPoPNonceRegistry",
    "VerifiedPoPContext",
    "WalletPoPError",
    "WalletPoPHeaders",
    "WalletPoPRequestVerifier",
    "build_wallet_pop_authorization_header",
    "canonical_request_for_signing",
    "canonicalize_query_string",
]
