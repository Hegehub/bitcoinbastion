"""Proof-of-Possession session service for Bastion Access.

This service creates short-lived, device-bound sessions only after a registered
device key signs an origin-bound challenge. It stores HMAC session hashes, never
raw session tokens, and does not accept Access Passes or Authorization: Bearer
credentials.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.access import AccessCertificate, AccessChallenge, AccessDevice, AccessSession, SubscriptionEntitlement
from app.domain.access.errors import (
    AccessCertificateExpiredError,
    AccessCertificateInactiveError,
    AccessCertificateNotFoundError,
    ChallengeAlreadyUsedError,
    DeviceInactiveError,
    DeviceNotFoundError,
    EntitlementExpiredError,
    EntitlementInactiveError,
    EntitlementMissingError,
    InvalidChallengeSignatureError,
    MissingRequiredScopeError,
    RequestedScopeNotAllowedError,
    SessionExpiredError,
    SessionFrozenError,
    SessionNotFoundError,
    SessionRevokedError,
    TargetRevokedError,
)
from app.services.access.challenge_service import (
    CHALLENGE_STATUS_PENDING,
    AccessChallengeService,
)
from app.services.access.crypto.hashing import (
    hmac_sha256_prefixed,
    safe_hash_for_log,
    secure_token_urlsafe,
    sha256_prefixed,
)
from app.services.access.crypto.signatures import Ed25519SignatureSuite, SignatureSuite

SESSION_STATUS_ACTIVE = "active"
SESSION_STATUS_EXPIRED = "expired"
SESSION_STATUS_REVOKED = "revoked"
SESSION_STATUS_FROZEN = "frozen"
DEFAULT_SESSION_TTL_SECONDS = 900
AuditEmitter = Callable[[str, dict[str, Any]], None]


class RevocationRegistry(Protocol):
    def is_revoked(self, target_type: str, target_hash: str) -> bool: ...


@dataclass(frozen=True, slots=True)
class AccessSessionCreateResult:
    session_token: str
    session_hash_fingerprint: str
    certificate_fingerprint: str
    device_key_fingerprint: str
    plan_code: str
    scopes: list[str]
    expires_at: datetime
    policy_mode: str
    requires_request_signing: bool
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AccessSessionContext:
    session_hash: str
    certificate_fingerprint: str
    pass_lookup_hash: str
    plan_code: str
    scopes: list[str]
    device_key_fingerprint: str
    entitlement_id: int | None
    expires_at: datetime
    risk_level: str
    requires_request_signing: bool
    access_integrity_score: int | None = None
    is_business_context: bool = False
    workspace_id_hash: str | None = None


class AccessSessionService:
    def __init__(
        self,
        db: Session,
        *,
        challenge_service: AccessChallengeService | None = None,
        entitlement_service: object | None = None,
        revocation_registry: RevocationRegistry | None = None,
        audit_chain: AuditEmitter | None = None,
        signature_suite: SignatureSuite | None = None,
        server_pepper: str | None = None,
        session_ttl_seconds: int | None = None,
    ) -> None:
        self.db = db
        self.challenge_service = challenge_service or AccessChallengeService(db)
        self.entitlement_service = entitlement_service
        self.revocation_registry = revocation_registry
        self.audit_chain = audit_chain
        self.signature_suite = signature_suite or Ed25519SignatureSuite()
        self.server_pepper = server_pepper or ""
        if not self.server_pepper:
            raise ValueError("server_pepper is required for session hashing")
        self.session_ttl_seconds = session_ttl_seconds or DEFAULT_SESSION_TTL_SECONDS
        if self.session_ttl_seconds < 60:
            raise ValueError("session_ttl_seconds must be at least 60")

    def create_session_from_challenge(
        self,
        *,
        certificate_fingerprint: str,
        challenge_id: str,
        origin: str,
        device_key_fingerprint: str,
        challenge_signature: str,
        client_session_public_key: str | None = None,
        requested_scopes: list[str] | None = None,
        user_agent_hash: str | None = None,
        ip_hash: str | None = None,
    ) -> AccessSessionCreateResult:
        challenge = self.challenge_service.verify_challenge_exists(challenge_id)
        self._reject_challenge_unusable(challenge, origin)
        if challenge.certificate_fingerprint != certificate_fingerprint:
            raise AccessCertificateNotFoundError("certificate_not_found")
        challenge_scopes = _json_string_list(challenge.requested_scopes_json)
        scopes = self._resolve_requested_scopes(requested_scopes, challenge_scopes)
        certificate = self._get_active_certificate(certificate_fingerprint)
        device = self._get_active_device(certificate_fingerprint, device_key_fingerprint)
        entitlement = self._get_active_entitlement(certificate)
        self._check_revocations(certificate=certificate, device=device, entitlement=entitlement)
        self._verify_challenge_signature(challenge.challenge_hash, device.device_public_key, challenge_signature)

        now = datetime.now(UTC)
        raw_session_token = secure_token_urlsafe(32)
        session_hash = hmac_sha256_prefixed(self.server_pepper, raw_session_token)
        expires_at = now + timedelta(seconds=self.session_ttl_seconds)
        session_key_fingerprint = sha256_prefixed(client_session_public_key) if client_session_public_key else None
        session = AccessSession(
            session_hash=session_hash,
            certificate_fingerprint=certificate.certificate_fingerprint,
            device_key_fingerprint=device.device_key_fingerprint,
            entitlement_id=entitlement.id,
            challenge_hash=challenge.challenge_hash,
            session_key_fingerprint=session_key_fingerprint,
            scopes_json=scopes,
            policy_context_json={
                "policy_mode": "proof_of_possession",
                "requires_request_signing": True,
                "user_agent_hash": user_agent_hash,
                "ip_hash": ip_hash,
            },
            status=SESSION_STATUS_ACTIVE,
            risk_level="low",
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
            last_seen_at=None,
        )
        self.db.add(session)
        self.challenge_service.mark_challenge_used(challenge_id, origin=origin)
        self.db.flush()
        self._emit_audit(
            "session_created",
            certificate_fingerprint=certificate.certificate_fingerprint,
            device_key_fingerprint=device.device_key_fingerprint,
            session_hash=session_hash,
            reason="created",
            origin=self.challenge_service.normalize_origin(origin),
        )
        return AccessSessionCreateResult(
            session_token=raw_session_token,
            session_hash_fingerprint=safe_hash_for_log(session_hash),
            certificate_fingerprint=certificate.certificate_fingerprint,
            device_key_fingerprint=device.device_key_fingerprint,
            plan_code=entitlement.plan_code,
            scopes=scopes,
            expires_at=expires_at,
            policy_mode="proof_of_possession",
            requires_request_signing=True,
            created_at=now,
        )

    def get_session_by_token(self, session_token: str) -> AccessSession | None:
        session_hash = hmac_sha256_prefixed(self.server_pepper, session_token)
        return self._get_session_by_hash(session_hash)

    def validate_session(
        self,
        *,
        session_token: str,
        required_scopes: list[str] | None = None,
        require_active_entitlement: bool = True,
    ) -> AccessSessionContext:
        session_hash = hmac_sha256_prefixed(self.server_pepper, session_token)
        session = self._get_session_by_hash(session_hash)
        if session is None:
            self._emit_validation_failed("session_not_found", session_hash=session_hash)
            raise SessionNotFoundError("session_not_found")
        self._reject_session_unusable(session)
        certificate = self._get_active_certificate(session.certificate_fingerprint)
        device = self._get_active_device(certificate.certificate_fingerprint, session.device_key_fingerprint)
        entitlement = self._get_active_entitlement(certificate) if require_active_entitlement else self._get_latest_entitlement(certificate)
        if entitlement is None:
            raise EntitlementMissingError("entitlement_missing")
        self._check_revocations(certificate=certificate, device=device, entitlement=entitlement, session=session)
        session_scopes = _json_string_list(session.scopes_json)
        required = set(required_scopes or [])
        if not required <= set(session_scopes):
            self._emit_validation_failed("missing_required_scope", session_hash=session.session_hash)
            raise MissingRequiredScopeError("missing_required_scope")
        session.last_seen_at = datetime.now(UTC)
        session.updated_at = datetime.now(UTC)
        self.db.flush()
        return self.build_session_context(session=session, certificate=certificate, entitlement=entitlement)

    def revoke_session(self, *, session_token: str | None = None, session_hash: str | None = None, reason: str) -> None:
        session = self._session_from_token_or_hash(session_token=session_token, session_hash=session_hash)
        session.status = SESSION_STATUS_REVOKED
        session.revoked_at = datetime.now(UTC)
        session.updated_at = datetime.now(UTC)
        self.db.flush()
        self._emit_audit("session_revoked", session=session, reason=reason)

    def freeze_session(self, *, session_token: str | None = None, session_hash: str | None = None, reason: str) -> None:
        session = self._session_from_token_or_hash(session_token=session_token, session_hash=session_hash)
        session.status = SESSION_STATUS_FROZEN
        session.frozen_at = datetime.now(UTC)
        session.updated_at = datetime.now(UTC)
        self.db.flush()
        self._emit_audit("session_frozen", session=session, reason=reason)

    def freeze_sessions_for_certificate(self, *, certificate_fingerprint: str, reason: str) -> int:
        now = datetime.now(UTC)
        sessions = list(
            self.db.execute(
                select(AccessSession).where(
                    AccessSession.certificate_fingerprint == certificate_fingerprint,
                    AccessSession.status == SESSION_STATUS_ACTIVE,
                )
            )
            .scalars()
            .all()
        )
        for session in sessions:
            session.status = SESSION_STATUS_FROZEN
            session.frozen_at = now
            session.updated_at = now
        self.db.flush()
        count = len(sessions)
        if count:
            self._emit_audit(
                "session_frozen",
                certificate_fingerprint=certificate_fingerprint,
                device_key_fingerprint=None,
                session_hash=None,
                reason=reason,
            )
        return count

    def expire_old_sessions(self) -> int:
        now = datetime.now(UTC)
        sessions = list(
            self.db.execute(
                select(AccessSession).where(
                    AccessSession.status == SESSION_STATUS_ACTIVE,
                    AccessSession.expires_at <= now.replace(tzinfo=None),
                )
            )
            .scalars()
            .all()
        )
        for session in sessions:
            session.status = SESSION_STATUS_EXPIRED
            session.updated_at = now
        self.db.flush()
        return len(sessions)

    def build_session_context(
        self,
        *,
        session: AccessSession,
        certificate: AccessCertificate,
        entitlement: SubscriptionEntitlement,
    ) -> AccessSessionContext:
        policy = session.policy_context_json or {}
        return AccessSessionContext(
            session_hash=session.session_hash,
            certificate_fingerprint=certificate.certificate_fingerprint,
            pass_lookup_hash=certificate.pass_lookup_hash,
            plan_code=entitlement.plan_code,
            scopes=_json_string_list(session.scopes_json),
            device_key_fingerprint=session.device_key_fingerprint,
            entitlement_id=entitlement.id,
            expires_at=session.expires_at,
            risk_level=session.risk_level,
            requires_request_signing=bool(policy.get("requires_request_signing", True)),
            access_integrity_score=policy.get("access_integrity_score") if isinstance(policy.get("access_integrity_score"), int) else None,
            is_business_context=entitlement.plan_code in {"business_pass", "enterprise_pass"},
            workspace_id_hash=policy.get("workspace_id_hash") if isinstance(policy.get("workspace_id_hash"), str) else None,
        )

    def _reject_challenge_unusable(self, challenge: AccessChallenge, origin: str) -> None:
        self.challenge_service.reject_if_revoked(challenge)
        self.challenge_service.reject_if_expired(challenge)
        self.challenge_service.reject_if_used(challenge)
        self.challenge_service.reject_if_origin_mismatch(challenge, origin)
        if challenge.status != CHALLENGE_STATUS_PENDING:
            raise ChallengeAlreadyUsedError("challenge_used")

    def _resolve_requested_scopes(self, requested_scopes: list[str] | None, challenge_scopes: list[str]) -> list[str]:
        if requested_scopes is None:
            return challenge_scopes
        requested = sorted(set(requested_scopes))
        if not set(requested) <= set(challenge_scopes):
            raise RequestedScopeNotAllowedError("requested_scope_not_allowed")
        return requested

    def _get_active_certificate(self, certificate_fingerprint: str) -> AccessCertificate:
        certificate = self.db.execute(
            select(AccessCertificate).where(AccessCertificate.certificate_fingerprint == certificate_fingerprint)
        ).scalar_one_or_none()
        if certificate is None:
            raise AccessCertificateNotFoundError("certificate_not_found")
        if certificate.status != "active":
            raise AccessCertificateInactiveError("certificate_inactive")
        if _naive_utc(certificate.expires_at) <= datetime.now(UTC).replace(tzinfo=None):
            raise AccessCertificateExpiredError("certificate_expired")
        return certificate

    def _get_active_device(self, certificate_fingerprint: str, device_key_fingerprint: str) -> AccessDevice:
        device = self.db.execute(
            select(AccessDevice).where(
                AccessDevice.certificate_fingerprint == certificate_fingerprint,
                AccessDevice.device_key_fingerprint == device_key_fingerprint,
            )
        ).scalar_one_or_none()
        if device is None:
            raise DeviceNotFoundError("device_not_found")
        if device.status != "active":
            raise DeviceInactiveError("device_inactive")
        return device

    def _get_active_entitlement(self, certificate: AccessCertificate) -> SubscriptionEntitlement:
        entitlement = self._get_latest_entitlement(certificate)
        if entitlement is None:
            raise EntitlementMissingError("entitlement_missing")
        now = datetime.now(UTC).replace(tzinfo=None)
        if _naive_utc(entitlement.valid_until) <= now:
            raise EntitlementExpiredError("entitlement_expired")
        if entitlement.status != "active":
            raise EntitlementInactiveError("entitlement_inactive")
        return entitlement

    def _get_latest_entitlement(self, certificate: AccessCertificate) -> SubscriptionEntitlement | None:
        return self.db.execute(
            select(SubscriptionEntitlement)
            .where(
                SubscriptionEntitlement.certificate_fingerprint == certificate.certificate_fingerprint,
                SubscriptionEntitlement.pass_lookup_hash == certificate.pass_lookup_hash,
            )
            .order_by(SubscriptionEntitlement.valid_from.desc(), SubscriptionEntitlement.id.desc())
        ).scalars().first()

    def _check_revocations(
        self,
        *,
        certificate: AccessCertificate,
        device: AccessDevice,
        entitlement: SubscriptionEntitlement,
        session: AccessSession | None = None,
    ) -> None:
        if self.revocation_registry is None:
            return
        targets = [
            ("certificate", certificate.certificate_fingerprint),
            ("pass", certificate.pass_lookup_hash),
            ("device", device.device_key_fingerprint),
            ("entitlement", str(entitlement.id)),
        ]
        if session is not None:
            targets.append(("session", session.session_hash))
        for target_type, target_hash in targets:
            if self.revocation_registry.is_revoked(target_type, target_hash):
                raise TargetRevokedError("target_revoked")

    def _verify_challenge_signature(self, challenge_hash: str, device_public_key: str, signature: str) -> None:
        result = self.signature_suite.verify(challenge_hash, "access_challenge", device_public_key, signature)
        if not result.valid:
            raise InvalidChallengeSignatureError("invalid_challenge_signature")

    def _reject_session_unusable(self, session: AccessSession) -> None:
        if session.status == SESSION_STATUS_REVOKED:
            self._emit_validation_failed("session_revoked", session_hash=session.session_hash)
            raise SessionRevokedError("session_revoked")
        if session.status == SESSION_STATUS_FROZEN:
            self._emit_validation_failed("session_frozen", session_hash=session.session_hash)
            raise SessionFrozenError("session_frozen")
        if session.status == SESSION_STATUS_EXPIRED or _naive_utc(session.expires_at) <= datetime.now(UTC).replace(tzinfo=None):
            session.status = SESSION_STATUS_EXPIRED
            self.db.flush()
            self._emit_validation_failed("session_expired", session_hash=session.session_hash)
            raise SessionExpiredError("session_expired")
        if session.status != SESSION_STATUS_ACTIVE:
            self._emit_validation_failed("session_not_found", session_hash=session.session_hash)
            raise SessionNotFoundError("session_not_found")

    def _get_session_by_hash(self, session_hash: str) -> AccessSession | None:
        return self.db.execute(select(AccessSession).where(AccessSession.session_hash == session_hash)).scalar_one_or_none()

    def _session_from_token_or_hash(self, *, session_token: str | None, session_hash: str | None) -> AccessSession:
        if session_hash is None:
            if session_token is None:
                raise SessionNotFoundError("session_not_found")
            session_hash = hmac_sha256_prefixed(self.server_pepper, session_token)
        session = self._get_session_by_hash(session_hash)
        if session is None:
            raise SessionNotFoundError("session_not_found")
        return session

    def _emit_validation_failed(self, reason: str, *, session_hash: str | None) -> None:
        self._emit_audit(
            "session_validation_failed",
            certificate_fingerprint=None,
            device_key_fingerprint=None,
            session_hash=session_hash,
            reason=reason,
        )

    def _emit_audit(
        self,
        event_type: str,
        *,
        session: AccessSession | None = None,
        certificate_fingerprint: str | None = None,
        device_key_fingerprint: str | None = None,
        session_hash: str | None = None,
        reason: str,
        origin: str | None = None,
    ) -> None:
        if self.audit_chain is None:
            return
        self.audit_chain(
            event_type,
            {
                "certificate_fingerprint": certificate_fingerprint or (session.certificate_fingerprint if session else None),
                "device_key_fingerprint": device_key_fingerprint or (session.device_key_fingerprint if session else None),
                "session_hash": session_hash or (session.session_hash if session else None),
                "reason": reason,
                "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "origin": origin,
            },
        )


def _json_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted({item for item in value if isinstance(item, str)})


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)
