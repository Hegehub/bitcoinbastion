"""LNURL-auth challenge creation service.

This service issues scannable LNURL-auth challenges only. It does not verify
callbacks, create Lightning principals, bind devices, issue sessions, grant
entitlements, or authorize protected API access.
"""
from __future__ import annotations

import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Protocol
from urllib.parse import urlencode, urlsplit, urlunsplit

from app.domain.lnurl.auth import LNURLAuthAction
from app.domain.wallet_auth.actions import WalletAuthAction
from app.domain.wallet_auth.risks import WalletRiskLevel
from app.services.access.crypto.hashing import canonical_json, sha256_prefixed
from app.services.lnurl.encoding import decode_lnurl, encode_lnurl
from app.services.lnurl.errors import (
    LNURLAuthActionNotAllowedError,
    LNURLAuthChallengeError,
    LNURLAuthConfigurationError,
    LNURLAuthDomainError,
    LNURLAuthEncodingError,
    LNURLAuthK1RegistrationError,
    LNURLAuthPolicyPrecheckError,
)
from app.services.lnurl.k1_registry import IssuedK1, LNURLK1Purpose, LNURLK1RegistryService, LNURLK1Status
from app.services.lnurl.redaction import redact_lnurl_url, redact_lnurl_value
from app.services.lnurl.url_safety import LNURLURLPolicy, validate_lnurl_url
from app.services.wallet_auth.privacy_commitments import reject_forbidden_wallet_secret_input

LNURL_AUTH_K1_BYTES = 32
LNURL_AUTH_SIGNATURE_WARNING = "This Lightning wallet signature proves control of your wallet for Bastion access. It does not authorize a Bitcoin transaction, Lightning payment, or withdrawal."
DEFAULT_CALLBACK_PATH = "/v1/lnurl/auth/callback"
DEFAULT_AUTH_CHALLENGE_TTL_SECONDS = 300
MIN_AUTH_CHALLENGE_TTL_SECONDS = 30
MAX_AUTH_CHALLENGE_TTL_SECONDS = 600

_ACTION_INTERNAL_MAP: dict[LNURLAuthAction, str] = {
    LNURLAuthAction.REGISTER: "wallet_principal_create",
    LNURLAuthAction.LOGIN: "wallet_principal_authenticate",
    LNURLAuthAction.LINK: "lightning_principal_link",
    LNURLAuthAction.AUTH: "wallet_sensitive_action_step_up",
}
_ACTION_PURPOSE_MAP: dict[LNURLAuthAction, LNURLK1Purpose] = {
    LNURLAuthAction.REGISTER: LNURLK1Purpose.LNURL_AUTH_REGISTER,
    LNURLAuthAction.LOGIN: LNURLK1Purpose.LNURL_AUTH_LOGIN,
    LNURLAuthAction.LINK: LNURLK1Purpose.LNURL_AUTH_LINK,
    LNURLAuthAction.AUTH: LNURLK1Purpose.LNURL_AUTH_STEP_UP,
}
_DEVICE_REQUIRED_ACTIONS = frozenset({LNURLAuthAction.REGISTER, LNURLAuthAction.LINK, LNURLAuthAction.AUTH})

class LNURLAuthChallengeStatus(str, Enum):
    PENDING = "pending"
    USED = "used"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

@dataclass(frozen=True, slots=True)
class LNURLAuthChallengeConfig:
    enabled: bool = True
    public_base_url: str = "https://auth.bitcoin-bastion.com"
    callback_path: str = DEFAULT_CALLBACK_PATH
    ttl_seconds: int = DEFAULT_AUTH_CHALLENGE_TTL_SECONDS
    min_ttl_seconds: int = MIN_AUTH_CHALLENGE_TTL_SECONDS
    max_ttl_seconds: int = MAX_AUTH_CHALLENGE_TTL_SECONDS
    allowed_origins: frozenset[str] = frozenset({"https://bitcoin-bastion.com"})
    allow_onion: bool = False
    stable_domain: str = "auth.bitcoin-bastion.com"
    policy_epoch: int = 1
    crypto_epoch: int = 1

    def __post_init__(self) -> None:
        if self.enabled and not self.public_base_url:
            raise LNURLAuthConfigurationError()
        if self.ttl_seconds < self.min_ttl_seconds or self.ttl_seconds > self.max_ttl_seconds:
            raise LNURLAuthConfigurationError("LNURL-auth challenge TTL is outside safe bounds.")
        try:
            base = validate_lnurl_url(self.public_base_url.rstrip("/") + self.callback_path, policy=self.url_policy())
        except Exception as exc:
            raise LNURLAuthConfigurationError() from exc
        if base.ascii_hostname != self.stable_domain:
            raise LNURLAuthConfigurationError("LNURL-auth stable domain does not match public base URL.")

    def url_policy(self) -> LNURLURLPolicy:
        if self.allow_onion:
            return LNURLURLPolicy.onion()
        return LNURLURLPolicy.service_owned_auth(domains=[self.stable_domain], stable_domain=self.stable_domain)

@dataclass(frozen=True, slots=True)
class LNURLAuthChallengeRecord:
    challenge_id: str
    registry_id: str
    k1_fingerprint: str
    lnurl_action: LNURLAuthAction
    internal_action: str
    purpose: str
    auth_domain: str
    origin: str
    origin_hash: str
    callback_url: str = field(repr=False)
    lnurl: str = field(repr=False)
    device_key_fingerprint: str | None
    principal_hint_hash: str | None
    requested_scopes: tuple[str, ...]
    policy_hash: str
    internal_intent_hash: str
    risk_level: str
    issued_at: datetime
    expires_at: datetime
    status: LNURLAuthChallengeStatus
    policy_epoch: int
    crypto_epoch: int
    schema_version: int = 1
    idempotency_key_hash: str | None = None
    request_fingerprint: str | None = None

@dataclass(frozen=True, slots=True)
class LNURLAuthChallengeDisplay:
    domain: str
    action: str
    purpose: str
    warning: str = LNURL_AUTH_SIGNATURE_WARNING

@dataclass(frozen=True, slots=True)
class LNURLAuthChallengeResult:
    challenge_id: str
    tag: str
    action: LNURLAuthAction
    lnurl: str = field(repr=False)
    callback_url: str = field(repr=False)
    expires_at: datetime
    expires_in_seconds: int
    qr_payload: str = field(repr=False)
    display: LNURLAuthChallengeDisplay

@dataclass(frozen=True, slots=True)
class LNURLAuthChallengeStatusView:
    challenge_id: str
    status: LNURLAuthChallengeStatus
    action: LNURLAuthAction
    internal_action: str
    purpose: str
    auth_domain: str
    expires_at: datetime
    lnurl: str | None = field(default=None, repr=False)
    qr_payload: str | None = field(default=None, repr=False)

class PolicyPrecheck(Protocol):
    def check(self, *, action: str, risk_level: str, requested_scopes: tuple[str, ...], policy_hash: str) -> None: ...

class InMemoryLNURLAuthChallengeRepository:
    def __init__(self) -> None:
        self._records: dict[str, LNURLAuthChallengeRecord] = {}
        self._idempotency: dict[str, str] = {}
        self._lock = threading.Lock()

    def create(self, record: LNURLAuthChallengeRecord) -> LNURLAuthChallengeRecord:
        with self._lock:
            if record.idempotency_key_hash:
                existing_id = self._idempotency.get(record.idempotency_key_hash)
                if existing_id:
                    existing = self._records[existing_id]
                    if existing.request_fingerprint != record.request_fingerprint:
                        raise LNURLAuthChallengeError("idempotency_key_conflict")
                    return existing
                self._idempotency[record.idempotency_key_hash] = record.challenge_id
            self._records[record.challenge_id] = record
            return record

    def get(self, challenge_id: str) -> LNURLAuthChallengeRecord | None:
        with self._lock:
            return self._records.get(challenge_id)

    def get_by_idempotency(self, idempotency_key_hash: str, request_fingerprint: str) -> LNURLAuthChallengeRecord | None:
        with self._lock:
            existing_id = self._idempotency.get(idempotency_key_hash)
            if existing_id is None:
                return None
            existing = self._records[existing_id]
            if existing.request_fingerprint != request_fingerprint:
                raise LNURLAuthChallengeError("idempotency_key_conflict")
            return existing

    def update(self, record: LNURLAuthChallengeRecord) -> LNURLAuthChallengeRecord:
        with self._lock:
            self._records[record.challenge_id] = record
            return record

    def records(self) -> tuple[LNURLAuthChallengeRecord, ...]:
        with self._lock:
            return tuple(self._records.values())

AuditEmitter = Callable[[str, Mapping[str, Any]], None]

class LNURLAuthChallengeService:
    def __init__(
        self,
        *,
        config: LNURLAuthChallengeConfig,
        k1_registry: LNURLK1RegistryService,
        repository: InMemoryLNURLAuthChallengeRepository | None = None,
        policy_precheck: PolicyPrecheck | None = None,
        clock: Callable[[], datetime] | None = None,
        audit_emitter: AuditEmitter | None = None,
    ) -> None:
        self.config = config
        self.k1_registry = k1_registry
        self.repository = repository or InMemoryLNURLAuthChallengeRepository()
        self.policy_precheck = policy_precheck
        self.clock = clock or (lambda: datetime.now(UTC))
        self.audit_emitter = audit_emitter

    def create_challenge(
        self,
        *,
        action: LNURLAuthAction | str,
        internal_action: WalletAuthAction | str | None = None,
        purpose: str = "primary_auth",
        origin: str,
        device_key_fingerprint: str | None = None,
        policy_hash: str,
        principal_hint_hash: str | None = None,
        requested_scopes: tuple[str, ...] | list[str] | None = None,
        risk_level: WalletRiskLevel | str = WalletRiskLevel.MEDIUM,
        expires_in_seconds: int | None = None,
        request_context: Mapping[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> LNURLAuthChallengeResult:
        action_value = _normalize_action(action)
        risk = str(risk_level.value if isinstance(risk_level, WalletRiskLevel) else risk_level)
        scopes = _normalize_scopes(requested_scopes or ())
        origin_value = _normalize_origin(origin, self.config.allowed_origins)
        internal = str(internal_action.value if isinstance(internal_action, WalletAuthAction) else (internal_action or _ACTION_INTERNAL_MAP[action_value]))
        _validate_public_inputs(purpose=purpose, device_key_fingerprint=device_key_fingerprint, principal_hint_hash=principal_hint_hash, policy_hash=policy_hash, internal_action=internal)
        if action_value in _DEVICE_REQUIRED_ACTIONS and not device_key_fingerprint:
            raise LNURLAuthActionNotAllowedError("device_fingerprint_required")
        ttl = self.config.ttl_seconds if expires_in_seconds is None else expires_in_seconds
        if ttl < self.config.min_ttl_seconds or ttl > self.config.max_ttl_seconds:
            raise LNURLAuthConfigurationError("lnurl_auth_ttl_invalid")
        context = request_context or {}
        _reject_forbidden_context(context)
        internal_intent_hash = _intent_hash(action_value, internal, purpose, origin_value, scopes, risk, policy_hash, device_key_fingerprint, principal_hint_hash, context)
        self._policy_precheck(action=internal, risk_level=risk, requested_scopes=scopes, policy_hash=policy_hash)
        idem_hash = sha256_prefixed(idempotency_key) if idempotency_key else None
        request_fp = sha256_prefixed(canonical_json({"action": action_value.value, "internal_action": internal, "purpose": purpose, "origin": origin_value, "device": device_key_fingerprint, "policy_hash": policy_hash, "scopes": scopes, "risk": risk}))
        if idem_hash:
            existing = self.repository.get_by_idempotency(idem_hash, request_fp)
            if existing and existing.status is LNURLAuthChallengeStatus.PENDING and existing.expires_at > self.clock():
                return self.build_challenge_response(existing)
        issued = self._register_k1(action_value, internal, purpose, policy_hash, principal_hint_hash, device_key_fingerprint, ttl, internal_intent_hash)
        callback_url = self.build_callback_url(k1=issued.k1, action=action_value)
        lnurl_value = self.encode_lnurl(callback_url)
        decoded = decode_lnurl(lnurl_value, policy=self.config.url_policy())
        if decoded.normalized_url != callback_url:
            raise LNURLAuthEncodingError()
        now = self.clock()
        record = LNURLAuthChallengeRecord(
            challenge_id=_challenge_id(issued.registry_id),
            registry_id=issued.registry_id,
            k1_fingerprint=issued.k1_fingerprint,
            lnurl_action=action_value,
            internal_action=internal,
            purpose=purpose,
            auth_domain=self.config.stable_domain,
            origin=origin_value,
            origin_hash=sha256_prefixed(origin_value),
            callback_url=callback_url,
            lnurl=lnurl_value,
            device_key_fingerprint=device_key_fingerprint,
            principal_hint_hash=principal_hint_hash,
            requested_scopes=scopes,
            policy_hash=policy_hash,
            internal_intent_hash=internal_intent_hash,
            risk_level=risk,
            issued_at=now,
            expires_at=issued.expires_at,
            status=LNURLAuthChallengeStatus.PENDING,
            policy_epoch=self.config.policy_epoch,
            crypto_epoch=self.config.crypto_epoch,
            idempotency_key_hash=idem_hash,
            request_fingerprint=request_fp,
        )
        stored = self.repository.create(record)
        self._audit("lnurl_auth_challenge_created", stored, reason_code="created")
        return self.build_challenge_response(stored)

    def get_challenge(self, challenge_id: str) -> LNURLAuthChallengeStatusView:
        record = self.repository.get(challenge_id)
        if record is None:
            raise LNURLAuthChallengeError("lnurl_auth_challenge_not_found")
        record = self._effective_record(record)
        active = record.status is LNURLAuthChallengeStatus.PENDING
        return LNURLAuthChallengeStatusView(record.challenge_id, record.status, record.lnurl_action, record.internal_action, record.purpose, record.auth_domain, record.expires_at, record.lnurl if active else None, record.lnurl if active else None)

    def cancel_challenge(self, challenge_id: str, *, reason: str, actor_context: Mapping[str, Any] | None = None) -> LNURLAuthChallengeStatusView:
        record = self.repository.get(challenge_id)
        if record is None:
            raise LNURLAuthChallengeError("lnurl_auth_challenge_not_found")
        if record.status is LNURLAuthChallengeStatus.CANCELLED:
            return self.get_challenge(challenge_id)
        if record.status is LNURLAuthChallengeStatus.PENDING:
            self.k1_registry.revoke_k1(registry_id=record.registry_id, reason_code=reason, actor_hash=str((actor_context or {}).get("actor_hash")) if actor_context else None)
            record = self.repository.update(replace(record, status=LNURLAuthChallengeStatus.CANCELLED))
            self._audit("lnurl_auth_challenge_cancelled", record, reason_code=reason)
        return self.get_challenge(challenge_id)

    def expire_challenge(self, challenge_id: str) -> LNURLAuthChallengeStatusView:
        record = self.repository.get(challenge_id)
        if record is None:
            raise LNURLAuthChallengeError("lnurl_auth_challenge_not_found")
        if record.status is LNURLAuthChallengeStatus.PENDING and record.expires_at <= self.clock():
            self.k1_registry.expire_stale_k1(now=self.clock())
            record = self.repository.update(replace(record, status=LNURLAuthChallengeStatus.EXPIRED))
            self._audit("lnurl_auth_challenge_expired", record, reason_code="expired")
        return self.get_challenge(record.challenge_id)

    def build_callback_url(self, *, k1: str, action: LNURLAuthAction | str) -> str:
        action_value = _normalize_action(action)
        base = validate_lnurl_url(self.config.public_base_url.rstrip("/") + self.config.callback_path, policy=self.config.url_policy())
        query = urlencode({"k1": k1, "action": action_value.value})
        callback = urlunsplit((base.scheme, base.ascii_hostname if base.port is None else f"{base.ascii_hostname}:{base.port}", base.path, query, ""))
        validate_lnurl_url(callback, policy=self.config.url_policy())
        return callback

    def encode_lnurl(self, callback_url: str) -> str:
        try:
            return encode_lnurl(callback_url, policy=self.config.url_policy()).upper()
        except Exception as exc:
            raise LNURLAuthEncodingError() from exc

    def build_challenge_response(self, record: LNURLAuthChallengeRecord) -> LNURLAuthChallengeResult:
        return LNURLAuthChallengeResult(
            challenge_id=record.challenge_id,
            tag=record.lnurl_action.value,
            action=record.lnurl_action,
            lnurl=record.lnurl,
            callback_url=record.callback_url,
            expires_at=record.expires_at,
            expires_in_seconds=max(0, int((record.expires_at - self.clock()).total_seconds())),
            qr_payload=record.lnurl,
            display=LNURLAuthChallengeDisplay(record.auth_domain, record.lnurl_action.value, record.purpose),
        )

    def _register_k1(self, action: LNURLAuthAction, internal: str, purpose: str, policy_hash: str, principal_hint_hash: str | None, device_key_fingerprint: str | None, ttl: int, internal_intent_hash: str) -> IssuedK1:
        try:
            return self.k1_registry.issue_k1(
                _ACTION_PURPOSE_MAP[action],
                self.config.stable_domain,
                lnurl_action=action.value,
                internal_action=internal,
                policy_hash=policy_hash,
                principal_hash=principal_hint_hash,
                device_key_fingerprint=device_key_fingerprint,
                metadata_hash=internal_intent_hash,
                ttl_seconds=ttl,
            )
        except Exception as exc:
            raise LNURLAuthK1RegistrationError() from exc

    def _effective_record(self, record: LNURLAuthChallengeRecord) -> LNURLAuthChallengeRecord:
        if record.status is LNURLAuthChallengeStatus.PENDING and record.expires_at <= self.clock():
            record = self.repository.update(replace(record, status=LNURLAuthChallengeStatus.EXPIRED))
            self._audit("lnurl_auth_challenge_expired", record, reason_code="expired")
        registry_status = self.k1_registry.get_k1_status_by_registry_id(record.registry_id) if hasattr(self.k1_registry, "get_k1_status_by_registry_id") else None
        if registry_status and registry_status.status is LNURLK1Status.CONSUMED and record.status is LNURLAuthChallengeStatus.PENDING:
            record = self.repository.update(replace(record, status=LNURLAuthChallengeStatus.USED))
        return record

    def _policy_precheck(self, *, action: str, risk_level: str, requested_scopes: tuple[str, ...], policy_hash: str) -> None:
        if self.policy_precheck is None:
            return
        try:
            self.policy_precheck.check(action=action, risk_level=risk_level, requested_scopes=requested_scopes, policy_hash=policy_hash)
        except Exception as exc:
            raise LNURLAuthPolicyPrecheckError() from exc

    def _audit(self, event: str, record: LNURLAuthChallengeRecord, *, reason_code: str) -> None:
        if self.audit_emitter is None:
            return
        self.audit_emitter(event, {
            "challenge_id": record.challenge_id,
            "k1_fingerprint": record.k1_fingerprint,
            "action": record.lnurl_action.value,
            "internal_action": record.internal_action,
            "auth_domain": record.auth_domain,
            "origin_hash": record.origin_hash,
            "device_key_fingerprint": record.device_key_fingerprint,
            "policy_hash": record.policy_hash,
            "risk_level": record.risk_level,
            "issued_at": record.issued_at.isoformat(),
            "expires_at": record.expires_at.isoformat(),
            "reason_code": reason_code,
        })

def _normalize_action(action: LNURLAuthAction | str) -> LNURLAuthAction:
    try:
        return action if isinstance(action, LNURLAuthAction) else LNURLAuthAction(str(action))
    except ValueError as exc:
        raise LNURLAuthActionNotAllowedError() from exc

def _normalize_origin(origin: str, allowed: frozenset[str]) -> str:
    reject_forbidden_wallet_secret_input(origin, "origin")
    parsed = urlsplit(origin)
    if not parsed.scheme or not parsed.netloc or parsed.query or parsed.fragment:
        raise LNURLAuthDomainError()
    normalized = urlunsplit((parsed.scheme.lower(), (parsed.hostname or "").lower(), parsed.path.rstrip("/") or "", "", ""))
    if allowed and normalized not in allowed:
        raise LNURLAuthDomainError()
    return normalized

def _normalize_scopes(scopes: Sequence[str]) -> tuple[str, ...]:
    normalized = tuple(sorted({scope.strip() for scope in scopes if scope and scope.strip()}))
    for scope in normalized:
        reject_forbidden_wallet_secret_input(scope, "requested_scope")
    return normalized

def _validate_public_inputs(*, purpose: str, device_key_fingerprint: str | None, principal_hint_hash: str | None, policy_hash: str, internal_action: str) -> None:
    for name, value in {"purpose": purpose, "device_key_fingerprint": device_key_fingerprint, "principal_hint_hash": principal_hint_hash, "policy_hash": policy_hash, "internal_action": internal_action}.items():
        if value:
            reject_forbidden_wallet_secret_input(value, name)
    if not policy_hash.startswith(("sha256:", "hmac-sha256:")):
        raise LNURLAuthPolicyPrecheckError("policy_hash_required")
    if device_key_fingerprint and not device_key_fingerprint.startswith("sha256:"):
        raise LNURLAuthActionNotAllowedError("invalid_device_fingerprint")

_FORBIDDEN_CHALLENGE_CONTEXT_KEYS = frozenset({"k1", "sig", "signature", "key", "linking_key", "linking_private_key", "private_key", "seed", "mnemonic", "xprv", "wallet_seed", "bitcoin_seed", "session_token", "access_pass", "recovery_material"})

def _reject_forbidden_context(context: Mapping[str, Any]) -> None:
    for key, value in context.items():
        key_text = str(key).lower()
        if any(forbidden in key_text for forbidden in _FORBIDDEN_CHALLENGE_CONTEXT_KEYS):
            raise LNURLAuthActionNotAllowedError("forbidden_lnurl_auth_challenge_input")
        if isinstance(value, str):
            reject_forbidden_wallet_secret_input(value, key_text)

def _intent_hash(action: LNURLAuthAction, internal: str, purpose: str, origin: str, scopes: tuple[str, ...], risk: str, policy_hash: str, device: str | None, principal_hint: str | None, context: Mapping[str, Any]) -> str:
    redacted_context = {str(k): "[redacted]" for k in context.keys()}
    return sha256_prefixed(canonical_json({
        "type": "bastion_lnurl_auth_intent",
        "version": 1,
        "lnurl_action": action.value,
        "internal_action": internal,
        "purpose": purpose,
        "origin": origin,
        "requested_scopes": scopes,
        "risk_level": risk,
        "policy_hash": policy_hash,
        "device_key_fingerprint": device,
        "principal_hint_hash": principal_hint,
        "context_keys": sorted(redacted_context),
    }))

def _challenge_id(registry_id: str) -> str:
    return "lac_" + sha256_prefixed(registry_id).split(":", 1)[1][:24]

def safe_auth_challenge_log_fields(record: LNURLAuthChallengeRecord) -> dict[str, str]:
    return {"challenge_id": record.challenge_id, "action": record.lnurl_action.value, "domain": record.auth_domain, "status": record.status.value, "callback_url": redact_lnurl_url(record.callback_url), "lnurl": redact_lnurl_value(record.lnurl)}

__all__ = [
    "DEFAULT_AUTH_CHALLENGE_TTL_SECONDS", "LNURL_AUTH_K1_BYTES", "LNURL_AUTH_SIGNATURE_WARNING", "InMemoryLNURLAuthChallengeRepository", "LNURLAuthChallengeConfig", "LNURLAuthChallengeDisplay", "LNURLAuthChallengeRecord", "LNURLAuthChallengeResult", "LNURLAuthChallengeService", "LNURLAuthChallengeStatus", "LNURLAuthChallengeStatusView", "safe_auth_challenge_log_fields",
]
