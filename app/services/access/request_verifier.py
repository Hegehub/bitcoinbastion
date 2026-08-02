"""Per-request Proof-of-Possession verifier for Bastion Access.

Protected requests must include Bastion PoP headers and a device-key signature
over a canonical request digest. This module deliberately has no
``Authorization: Bearer`` fallback and never treats an Access Pass or session
header alone as sufficient authorization.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.access import AccessCertificate, AccessDevice, AccessRequestNonce, AccessSession, SubscriptionEntitlement
from app.services.access.crypto.hashing import (
    body_hash,
    constant_time_equal,
    hmac_sha256_prefixed,
    request_digest,
)
from app.services.access.crypto.signatures import Ed25519SignatureSuite, SignatureSuite

HEADER_SESSION = "x-bastion-session"
HEADER_TIMESTAMP = "x-bastion-timestamp"
HEADER_NONCE = "x-bastion-nonce"
HEADER_BODY_HASH = "x-bastion-body-hash"
HEADER_SIGNATURE = "x-bastion-signature"
DEFAULT_REQUEST_MAX_SKEW_SECONDS = 300
_SHA256_HEX_RE = re.compile(r"^(?:sha256:)?[0-9a-f]{64}$")
AuditEmitter = Callable[[str, dict[str, Any]], None]


class RequestVerificationError(ValueError):
    """Base request verifier error with secret-free messages."""


class MissingAccessHeaderError(RequestVerificationError):
    """Raised when a required X-Bastion header is missing."""


class InvalidSessionError(RequestVerificationError):
    """Raised when the session cannot be found or is inactive."""


class ExpiredSessionError(RequestVerificationError):
    """Raised when the session is expired."""


class RevokedSessionError(RequestVerificationError):
    """Raised when the session or related access object is revoked."""


class InvalidTimestampError(RequestVerificationError):
    """Raised when a request timestamp is malformed."""


class StaleTimestampError(RequestVerificationError):
    """Raised when a timestamp is outside the allowed skew."""


class InvalidNonceError(RequestVerificationError):
    """Raised when a nonce is empty or malformed."""


class ReusedNonceError(RequestVerificationError):
    """Raised when a nonce is replayed for a session."""


class InvalidBodyHashError(RequestVerificationError):
    """Raised when the supplied body hash is missing, malformed, or mismatched."""


class InvalidRequestSignatureError(RequestVerificationError):
    """Raised when request signature verification fails closed."""


class UnsupportedSignatureSuiteError(RequestVerificationError):
    """Raised when a configured signature suite cannot verify requests."""


class RevocationRegistry(Protocol):
    def is_revoked(self, target_type: str, target_hash: str) -> bool: ...


@dataclass(frozen=True, slots=True)
class AccessRequestHeaders:
    session_token: str
    timestamp: str
    nonce: str
    body_hash: str
    signature: str

    @classmethod
    def parse(cls, headers: Mapping[str, str]) -> AccessRequestHeaders:
        normalized = {key.lower(): value for key, value in headers.items()}
        authorization = normalized.get("authorization", "")
        canonical_session = authorization[4:].strip() if authorization.startswith("PoP ") else None
        values = {
            HEADER_SESSION: canonical_session or normalized.get(HEADER_SESSION, ""),
            HEADER_TIMESTAMP: normalized.get("bastion-request-timestamp") or normalized.get(HEADER_TIMESTAMP, ""),
            HEADER_NONCE: normalized.get("bastion-request-nonce") or normalized.get(HEADER_NONCE, ""),
            HEADER_BODY_HASH: normalized.get("bastion-request-body-hash") or normalized.get(HEADER_BODY_HASH, ""),
            HEADER_SIGNATURE: normalized.get("bastion-request-signature") or normalized.get(HEADER_SIGNATURE, ""),
        }
        for key, value in values.items():
            if not value:
                raise MissingAccessHeaderError(f"missing_{key.replace('-', '_')}")
        if not values[HEADER_NONCE].strip():
            raise InvalidNonceError("invalid_nonce")
        if not _looks_like_body_hash(values[HEADER_BODY_HASH]):
            raise InvalidBodyHashError("invalid_body_hash")
        if not values[HEADER_SIGNATURE].strip():
            raise MissingAccessHeaderError("missing_x_bastion_signature")
        return cls(
            session_token=values[HEADER_SESSION],
            timestamp=values[HEADER_TIMESTAMP],
            nonce=values[HEADER_NONCE],
            body_hash=_normalize_body_hash(values[HEADER_BODY_HASH]),
            signature=values[HEADER_SIGNATURE],
        )


@dataclass(frozen=True, slots=True)
class VerifiedAccessRequest:
    session_id: int
    session_hash: str
    certificate_id: int
    certificate_fingerprint: str
    pass_lookup_hash: str
    device_id: int
    device_key_fingerprint: str
    plan_code: str
    scopes: list[str]
    request_digest: str
    timestamp: datetime
    nonce_hash: str
    verification_level: str


class AccessRequestVerifier:
    def __init__(
        self,
        *,
        server_pepper: str,
        max_skew_seconds: int = DEFAULT_REQUEST_MAX_SKEW_SECONDS,
        signature_required: bool = True,
        signature_suite: SignatureSuite | None = None,
        revocation_registry: RevocationRegistry | None = None,
        audit_emitter: AuditEmitter | None = None,
    ) -> None:
        if not server_pepper:
            raise ValueError("server_pepper is required for session lookup")
        if max_skew_seconds < 1:
            raise ValueError("max_skew_seconds must be positive")
        self.server_pepper = server_pepper
        self.max_skew_seconds = max_skew_seconds
        self.signature_required = signature_required
        self.signature_suite = signature_suite or Ed25519SignatureSuite()
        self.revocation_registry = revocation_registry
        self.audit_emitter = audit_emitter

    def verify(
        self,
        db: Session,
        *,
        method: str,
        path: str,
        body: bytes,
        headers: Mapping[str, str],
    ) -> VerifiedAccessRequest:
        parsed = AccessRequestHeaders.parse(headers)
        timestamp = self.validate_timestamp(parsed.timestamp)
        actual_body_hash = calculate_body_hash(body)
        if not constant_time_equal(actual_body_hash, parsed.body_hash):
            self._emit_denied("invalid_body_hash", method=method, path=path, timestamp=parsed.timestamp)
            raise InvalidBodyHashError("invalid_body_hash")
        session_hash = hmac_sha256_prefixed(self.server_pepper, parsed.session_token)
        session = self._get_active_session(db, session_hash)
        certificate = self._get_active_certificate(db, session.certificate_fingerprint)
        device = self._get_active_device(db, session.device_key_fingerprint, certificate.certificate_fingerprint)
        entitlement = self._get_active_entitlement(db, certificate, session.entitlement_id)
        self._check_revocations(session=session, certificate=certificate, device=device, entitlement=entitlement)
        digest = build_request_digest(method, path, parsed.body_hash, parsed.timestamp, parsed.nonce)
        self.verify_request_signature(device=device, request_digest_hex=digest, signature=parsed.signature)
        nonce_hash = self.record_nonce_once(db, session_hash=session.session_hash, nonce=parsed.nonce, timestamp=timestamp, digest=digest)
        session.last_seen_at = datetime.now(UTC)
        session.updated_at = datetime.now(UTC)
        db.flush()
        verified = VerifiedAccessRequest(
            session_id=session.id,
            session_hash=session.session_hash,
            certificate_id=certificate.id,
            certificate_fingerprint=certificate.certificate_fingerprint,
            pass_lookup_hash=certificate.pass_lookup_hash,
            device_id=device.id,
            device_key_fingerprint=device.device_key_fingerprint,
            plan_code=entitlement.plan_code,
            scopes=_json_string_list(session.scopes_json),
            request_digest=digest,
            timestamp=timestamp,
            nonce_hash=nonce_hash,
            verification_level="proof_of_possession_request_signature",
        )
        self._emit_verified(verified, method=method, path=path)
        return verified

    def validate_timestamp(self, timestamp: str) -> datetime:
        try:
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError as exc:
            raise InvalidTimestampError("invalid_timestamp") from exc
        if parsed.tzinfo is None:
            raise InvalidTimestampError("invalid_timestamp")
        now = datetime.now(UTC)
        normalized = parsed.astimezone(UTC)
        if normalized < now - timedelta(seconds=self.max_skew_seconds):
            raise StaleTimestampError("stale_timestamp")
        if normalized > now + timedelta(seconds=self.max_skew_seconds):
            raise StaleTimestampError("stale_timestamp")
        return normalized

    def record_nonce_once(self, db: Session, *, session_hash: str, nonce: str, timestamp: datetime, digest: str) -> str:
        if not nonce.strip():
            raise InvalidNonceError("invalid_nonce")
        nonce_hash = hmac_sha256_prefixed(session_hash, nonce)
        db.add(
            AccessRequestNonce(
                session_hash=session_hash,
                nonce_hash=nonce_hash,
                timestamp=timestamp,
                request_digest=digest,
                created_at=datetime.now(UTC),
            )
        )
        try:
            db.flush()
        except IntegrityError as exc:
            db.rollback()
            raise ReusedNonceError("reused_nonce") from exc
        return nonce_hash

    def verify_request_signature(self, *, device: AccessDevice, request_digest_hex: str, signature: str) -> None:
        if not self.signature_required:
            raise InvalidRequestSignatureError("signature_required")
        if not device.device_public_key:
            raise InvalidRequestSignatureError("missing_device_key")
        try:
            result = self.signature_suite.verify(request_digest_hex, "access_session", device.device_public_key, signature)
        except Exception as exc:
            raise UnsupportedSignatureSuiteError("unsupported_signature_suite") from exc
        if not result.valid:
            raise InvalidRequestSignatureError("invalid_request_signature")

    def _get_active_session(self, db: Session, session_hash: str) -> AccessSession:
        session = db.execute(select(AccessSession).where(AccessSession.session_hash == session_hash)).scalar_one_or_none()
        if session is None:
            self._emit_denied("invalid_session")
            raise InvalidSessionError("invalid_session")
        if session.status == "expired" or _naive_utc(session.expires_at) <= datetime.now(UTC).replace(tzinfo=None):
            self._emit_denied("expired_session", session_hash=session.session_hash)
            raise ExpiredSessionError("expired_session")
        if session.status in {"revoked", "frozen"}:
            self._emit_denied("revoked_session", session_hash=session.session_hash)
            raise RevokedSessionError("revoked_session")
        if session.status != "active":
            self._emit_denied("invalid_session", session_hash=session.session_hash)
            raise InvalidSessionError("invalid_session")
        return session

    def _get_active_certificate(self, db: Session, certificate_fingerprint: str) -> AccessCertificate:
        certificate = db.execute(
            select(AccessCertificate).where(AccessCertificate.certificate_fingerprint == certificate_fingerprint)
        ).scalar_one_or_none()
        if certificate is None or certificate.status != "active" or _naive_utc(certificate.expires_at) <= datetime.now(UTC).replace(tzinfo=None):
            raise InvalidSessionError("invalid_session")
        return certificate

    def _get_active_device(self, db: Session, device_key_fingerprint: str, certificate_fingerprint: str) -> AccessDevice:
        device = db.execute(
            select(AccessDevice).where(
                AccessDevice.device_key_fingerprint == device_key_fingerprint,
                AccessDevice.certificate_fingerprint == certificate_fingerprint,
            )
        ).scalar_one_or_none()
        if device is None or device.status != "active":
            raise InvalidSessionError("invalid_session")
        return device

    def _get_active_entitlement(
        self,
        db: Session,
        certificate: AccessCertificate,
        entitlement_id: int | None,
    ) -> SubscriptionEntitlement:
        statement = select(SubscriptionEntitlement).where(
            SubscriptionEntitlement.certificate_fingerprint == certificate.certificate_fingerprint,
            SubscriptionEntitlement.pass_lookup_hash == certificate.pass_lookup_hash,
        )
        if entitlement_id is not None:
            statement = statement.where(SubscriptionEntitlement.id == entitlement_id)
        entitlement = db.execute(statement.order_by(SubscriptionEntitlement.valid_from.desc())).scalars().first()
        if entitlement is None:
            raise InvalidSessionError("invalid_session")
        if entitlement.status != "active" or _naive_utc(entitlement.valid_until) <= datetime.now(UTC).replace(tzinfo=None):
            raise InvalidSessionError("invalid_session")
        return entitlement

    def _check_revocations(
        self,
        *,
        session: AccessSession,
        certificate: AccessCertificate,
        device: AccessDevice,
        entitlement: SubscriptionEntitlement,
    ) -> None:
        if self.revocation_registry is None:
            return
        targets = [
            ("session", session.session_hash),
            ("certificate", certificate.certificate_fingerprint),
            ("pass", certificate.pass_lookup_hash),
            ("device", device.device_key_fingerprint),
            ("entitlement", str(entitlement.id)),
        ]
        for target_type, target_hash in targets:
            if self.revocation_registry.is_revoked(target_type, target_hash):
                self._emit_denied("target_revoked", session_hash=session.session_hash)
                raise RevokedSessionError("target_revoked")

    def _emit_verified(self, verified: VerifiedAccessRequest, *, method: str, path: str) -> None:
        if self.audit_emitter is None:
            return
        self.audit_emitter(
            "access_request_verified",
            {
                "session_hash": verified.session_hash,
                "certificate_fingerprint": verified.certificate_fingerprint,
                "device_key_fingerprint": verified.device_key_fingerprint,
                "reason": "verified",
                "request_path": path,
                "method": method.upper(),
                "timestamp": verified.timestamp.isoformat().replace("+00:00", "Z"),
                "request_digest": verified.request_digest,
            },
        )

    def _emit_denied(
        self,
        reason: str,
        *,
        session_hash: str | None = None,
        method: str | None = None,
        path: str | None = None,
        timestamp: str | None = None,
    ) -> None:
        if self.audit_emitter is None:
            return
        self.audit_emitter(
            "access_request_denied",
            {
                "session_hash": session_hash,
                "certificate_fingerprint": None,
                "device_key_fingerprint": None,
                "reason": reason,
                "request_path": path,
                "method": method.upper() if method else None,
                "timestamp": timestamp,
                "request_digest": None,
            },
        )


def build_request_digest(method: str, path: str, body_hash_hex: str, timestamp: str, nonce: str) -> str:
    return request_digest(method.upper(), path, _normalize_body_hash(body_hash_hex), timestamp, nonce)


def calculate_body_hash(body: bytes) -> str:
    return body_hash(body)


def _looks_like_body_hash(value: str) -> bool:
    return bool(_SHA256_HEX_RE.fullmatch(value.strip().lower()))


def _normalize_body_hash(value: str) -> str:
    lowered = value.strip().lower()
    return lowered.removeprefix("sha256:")


def _json_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted({item for item in value if isinstance(item, str)})


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)
