"""Origin-bound one-time challenge service for Bastion Proof-of-Access Auth.

Challenges prove intent to begin a future Proof-of-Possession session. They are
bound to origin, certificate fingerprint, requested scopes, and an unpredictable
server nonce. This module does not create sessions and does not accept bearer
Access Pass authentication.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.access import AccessCertificate, AccessChallenge, SubscriptionEntitlement
from app.domain.access.errors import (
    AccessCertificateExpiredError,
    AccessCertificateInactiveError,
    AccessCertificateNotFoundError,
    ChallengeAlreadyUsedError,
    ChallengeExpiredError,
    ChallengeNotFoundError,
    ChallengeOriginMismatchError,
    ChallengeRevokedError,
    InvalidOriginError,
    OriginRequiredError,
    RequestedScopeNotAllowedError,
    SubscriptionEntitlementInactiveError,
    UnknownScopeError,
    UnsafeScopeError,
)
from app.domain.access.scopes import ACCESS_SCOPES, FORBIDDEN_SCOPES
from app.services.access.crypto.hashing import hash_canonical_json_prefixed, secure_nonce_hex, sha256_prefixed

CHALLENGE_TYPE = "bastion_access_challenge"
CHALLENGE_VERSION = 1
CHALLENGE_STATUS_PENDING = "pending"
CHALLENGE_STATUS_USED = "used"
CHALLENGE_STATUS_EXPIRED = "expired"
CHALLENGE_STATUS_REVOKED = "revoked"
DEFAULT_CHALLENGE_TTL_SECONDS = 300
_ALLOWED_ORIGIN_SCHEMES = {"https", "app", "cli", "telegram"}
AuditEmitter = Callable[[str, dict[str, Any]], None]


@dataclass(frozen=True, slots=True)
class AccessChallengeResult:
    challenge_id: str
    challenge_hash: str
    challenge_payload: dict[str, Any]
    expires_at: datetime
    status: str


class AccessChallengeService:
    def __init__(
        self,
        db: Session,
        *,
        challenge_ttl_seconds: int = DEFAULT_CHALLENGE_TTL_SECONDS,
        audit_emitter: AuditEmitter | None = None,
    ) -> None:
        if challenge_ttl_seconds < 30:
            raise ValueError("challenge_ttl_seconds must be at least 30")
        self.db = db
        self.challenge_ttl_seconds = challenge_ttl_seconds
        self.audit_emitter = audit_emitter

    def create_challenge(
        self,
        *,
        certificate_fingerprint: str,
        origin: str,
        requested_scopes: list[str],
        device_key_fingerprint: str | None = None,
        introspection_only: bool = False,
    ) -> AccessChallengeResult:
        normalized_origin = self.normalize_origin(origin)
        certificate = self._get_active_certificate(certificate_fingerprint)
        if device_key_fingerprint and certificate.device_key_fingerprint and device_key_fingerprint != certificate.device_key_fingerprint:
            raise AccessCertificateInactiveError("device_key_fingerprint does not match certificate")
        entitlement = self._get_active_entitlement(certificate_fingerprint)
        scopes = self.canonicalize_requested_scopes(requested_scopes, allow_empty=introspection_only)
        self.reject_if_scope_escalation(scopes, entitlement)
        issued_at = datetime.now(UTC)
        expires_at = issued_at + timedelta(seconds=self.challenge_ttl_seconds)
        server_nonce = secure_nonce_hex(16)
        payload = self.build_challenge_payload(
            certificate_fingerprint=certificate_fingerprint,
            origin=normalized_origin,
            requested_scopes=scopes,
            server_nonce=server_nonce,
            issued_at=issued_at,
            expires_at=expires_at,
        )
        challenge_hash = payload["challenge_hash"]
        challenge = AccessChallenge(
            challenge_hash=challenge_hash,
            certificate_fingerprint=certificate_fingerprint,
            device_key_fingerprint=device_key_fingerprint or certificate.device_key_fingerprint,
            origin=normalized_origin,
            requested_scopes_json=scopes,
            requested_action=None,
            server_nonce_hash=sha256_prefixed(server_nonce),
            client_nonce_hash=None,
            challenge_payload_hash=hash_canonical_json_prefixed(payload),
            status=CHALLENGE_STATUS_PENDING,
            expires_at=expires_at,
            used_at=None,
            created_at=issued_at,
            updated_at=issued_at,
        )
        self.db.add(challenge)
        self.db.flush()
        self._emit_audit("access_challenge_created", challenge, reason="created")
        return AccessChallengeResult(challenge_hash, challenge_hash, payload, expires_at, CHALLENGE_STATUS_PENDING)

    def get_challenge(self, challenge_id: str) -> AccessChallenge | None:
        statement = select(AccessChallenge).where(AccessChallenge.challenge_hash == challenge_id)
        return self.db.execute(statement).scalar_one_or_none()

    def verify_challenge_exists(self, challenge_id: str) -> AccessChallenge:
        challenge = self.get_challenge(challenge_id)
        if challenge is None:
            raise ChallengeNotFoundError("challenge_not_found")
        return challenge

    def mark_challenge_used(self, challenge_id: str, *, origin: str | None = None) -> AccessChallenge:
        challenge = self.verify_challenge_exists(challenge_id)
        if origin is not None:
            self.reject_if_origin_mismatch(challenge, origin)
        self.reject_if_revoked(challenge)
        self.reject_if_expired(challenge)
        self.reject_if_used(challenge)
        challenge.status = CHALLENGE_STATUS_USED
        challenge.used_at = datetime.now(UTC)
        challenge.updated_at = datetime.now(UTC)
        self.db.flush()
        self._emit_audit("access_challenge_used", challenge, reason="used")
        return challenge

    def reject_if_expired(self, challenge: AccessChallenge) -> None:
        if challenge.status == CHALLENGE_STATUS_EXPIRED or _naive_utc(challenge.expires_at) <= datetime.now(UTC).replace(tzinfo=None):
            challenge.status = CHALLENGE_STATUS_EXPIRED
            self.db.flush()
            self._emit_audit("access_challenge_rejected", challenge, reason="challenge_expired")
            raise ChallengeExpiredError("challenge_expired")

    def reject_if_used(self, challenge: AccessChallenge) -> None:
        if challenge.status == CHALLENGE_STATUS_USED or challenge.used_at is not None:
            self._emit_audit("access_challenge_rejected", challenge, reason="challenge_already_used")
            raise ChallengeAlreadyUsedError("challenge_already_used")

    def reject_if_revoked(self, challenge: AccessChallenge) -> None:
        if challenge.status == CHALLENGE_STATUS_REVOKED:
            self._emit_audit("access_challenge_rejected", challenge, reason="challenge_revoked")
            raise ChallengeRevokedError("challenge_revoked")

    def reject_if_origin_mismatch(self, challenge: AccessChallenge, origin: str) -> None:
        if self.normalize_origin(origin) != challenge.origin:
            self._emit_audit("access_challenge_rejected", challenge, reason="challenge_origin_mismatch")
            raise ChallengeOriginMismatchError("challenge_origin_mismatch")

    def reject_if_scope_escalation(self, requested_scopes: Iterable[str], entitlement: SubscriptionEntitlement) -> None:
        allowed = {scope for scope in (entitlement.scopes_json or []) if isinstance(scope, str)}
        requested = set(requested_scopes)
        if not requested <= allowed:
            raise RequestedScopeNotAllowedError("requested_scope_not_allowed")

    def build_challenge_payload(
        self,
        *,
        certificate_fingerprint: str,
        origin: str,
        requested_scopes: list[str],
        server_nonce: str,
        issued_at: datetime,
        expires_at: datetime,
    ) -> dict[str, Any]:
        normalized_origin = self.normalize_origin(origin)
        scopes = self.canonicalize_requested_scopes(requested_scopes)
        material = {
            "type": CHALLENGE_TYPE,
            "version": CHALLENGE_VERSION,
            "certificate_fingerprint": certificate_fingerprint,
            "origin": normalized_origin,
            "requested_scopes": scopes,
            "server_nonce": server_nonce,
            "issued_at": _isoformat(issued_at),
            "expires_at": _isoformat(expires_at),
        }
        challenge_hash = hash_canonical_json_prefixed(material)
        return {**material, "challenge_hash": challenge_hash}

    def canonicalize_requested_scopes(self, requested_scopes: list[str], *, allow_empty: bool = False) -> list[str]:
        scopes = sorted(set(requested_scopes))
        if not scopes and not allow_empty:
            raise RequestedScopeNotAllowedError("requested_scope_not_allowed")
        unsafe = set(scopes) & set(FORBIDDEN_SCOPES)
        if unsafe:
            raise UnsafeScopeError("unsafe_scope")
        unknown = [scope for scope in scopes if scope not in ACCESS_SCOPES]
        if unknown:
            raise UnknownScopeError("unknown_scope")
        return scopes

    def normalize_origin(self, origin: str) -> str:
        if not origin or not origin.strip():
            raise OriginRequiredError("origin_required")
        raw = origin.strip()
        parsed = urlparse(raw)
        scheme = parsed.scheme.lower()
        if scheme not in _ALLOWED_ORIGIN_SCHEMES:
            raise InvalidOriginError("invalid_origin")
        if scheme == "https":
            if not parsed.netloc:
                raise InvalidOriginError("invalid_origin")
            host = parsed.hostname.lower() if parsed.hostname else ""
            port = f":{parsed.port}" if parsed.port else ""
            return f"https://{host}{port}"
        if not parsed.netloc:
            raise InvalidOriginError("invalid_origin")
        return f"{scheme}://{parsed.netloc.lower()}"

    def _get_active_certificate(self, certificate_fingerprint: str) -> AccessCertificate:
        certificate = self.db.execute(
            select(AccessCertificate).where(AccessCertificate.certificate_fingerprint == certificate_fingerprint)
        ).scalar_one_or_none()
        if certificate is None:
            raise AccessCertificateNotFoundError("access_certificate_not_found")
        if certificate.status != "active":
            raise AccessCertificateInactiveError("access_certificate_inactive")
        if _naive_utc(certificate.expires_at) <= datetime.now(UTC).replace(tzinfo=None):
            raise AccessCertificateExpiredError("access_certificate_expired")
        return certificate

    def _get_active_entitlement(self, certificate_fingerprint: str) -> SubscriptionEntitlement:
        now = datetime.now(UTC).replace(tzinfo=None)
        statement = (
            select(SubscriptionEntitlement)
            .where(
                SubscriptionEntitlement.certificate_fingerprint == certificate_fingerprint,
                SubscriptionEntitlement.status == "active",
            )
            .order_by(SubscriptionEntitlement.valid_from.desc(), SubscriptionEntitlement.id.desc())
        )
        entitlement = self.db.execute(statement).scalars().first()
        if entitlement is None or _naive_utc(entitlement.valid_until) <= now:
            raise SubscriptionEntitlementInactiveError("subscription_entitlement_inactive")
        return entitlement

    def _emit_audit(self, event_type: str, challenge: AccessChallenge, *, reason: str) -> None:
        if self.audit_emitter is None:
            return
        self.audit_emitter(
            event_type,
            {
                "certificate_fingerprint": challenge.certificate_fingerprint,
                "origin": challenge.origin,
                "requested_scopes": challenge.requested_scopes_json,
                "challenge_hash": challenge.challenge_hash,
                "status": challenge.status,
                "reason": reason,
            },
        )


def _isoformat(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)
