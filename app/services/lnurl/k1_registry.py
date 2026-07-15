"""LNURL k1 registry and single-use replay protection.

This module owns the k1 lifecycle only. A valid k1 proves an expected challenge
was referenced; it does not verify wallet signatures, authorize actions, create
principals, issue sessions, settle payments, or execute withdrawals.
"""
from __future__ import annotations

import re
import secrets
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy.orm import Session

from app.db.models.lnurl import LNURLAuthChallenge
from app.services.access.crypto.hashing import hmac_sha256_prefixed, sha256_prefixed
from app.services.lnurl.errors import (
    LNURLK1ActionMismatchError,
    LNURLK1BindingMismatchError,
    LNURLK1ConfigurationError,
    LNURLK1ConsumedError,
    LNURLK1DomainMismatchError,
    LNURLK1ExpiredError,
    LNURLK1MalformedError,
    LNURLK1PolicyMismatchError,
    LNURLK1RevokedError,
    LNURLK1UnknownError,
)
from app.services.lnurl.url_safety import hostname_matches_allowlist

K1_BYTES = 32
K1_HEX_LENGTH = 64
K1_MAX_TTL_SECONDS = 900
DEFAULT_K1_MAX_FAILURES = 3
K1_CLOCK_SKEW_SECONDS = 30
_K1_RE = re.compile(r"^[0-9a-f]{64}$")

class LNURLK1Purpose(str, Enum):
    LNURL_AUTH_REGISTER = "lnurl_auth_register"
    LNURL_AUTH_LOGIN = "lnurl_auth_login"
    LNURL_AUTH_LINK = "lnurl_auth_link"
    LNURL_AUTH_STEP_UP = "lnurl_auth_step_up"
    LNURL_WITHDRAW = "lnurl_withdraw"
    PAYREGISTER_REFUND = "payregister_refund"
    RECOVERY_FACTOR = "recovery_factor"
    BUSINESS_APPROVAL = "business_approval"
    SOVEREIGN_APPROVAL = "sovereign_approval"

class LNURLK1Status(str, Enum):
    ACTIVE = "active"
    CONSUMED = "consumed"
    EXPIRED = "expired"
    REVOKED = "revoked"
    FAILED = "failed"

class LNURLK1FailureReason(str, Enum):
    MALFORMED_K1 = "malformed_k1"
    UNKNOWN_K1 = "unknown_k1"
    EXPIRED_K1 = "expired_k1"
    REUSED_K1 = "reused_k1"
    REVOKED_K1 = "revoked_k1"
    DOMAIN_MISMATCH = "domain_mismatch"
    ACTION_MISMATCH = "action_mismatch"
    POLICY_MISMATCH = "policy_mismatch"
    PRINCIPAL_MISMATCH = "principal_mismatch"
    DEVICE_MISMATCH = "device_mismatch"
    INVALID_SIGNATURE = "invalid_signature"
    UNSUPPORTED_KEY = "unsupported_key"
    VERIFICATION_ERROR = "verification_error"

@dataclass(frozen=True, slots=True)
class LNURLK1Config:
    server_pepper: str
    auth_ttl_seconds: int = 300
    step_up_ttl_seconds: int = 180
    withdraw_ttl_seconds: int = 300
    recovery_ttl_seconds: int = 180
    critical_ttl_seconds: int = 120
    max_failures: int = DEFAULT_K1_MAX_FAILURES
    one_attempt_for_critical_actions: bool = True
    clock_skew_seconds: int = K1_CLOCK_SKEW_SECONDS
    stable_auth_domain: str | None = None
    allow_test_pepper: bool = False

    def __post_init__(self) -> None:
        if not self.server_pepper or (not self.allow_test_pepper and self.server_pepper.startswith("test-")):
            raise LNURLK1ConfigurationError()
        for ttl in (self.auth_ttl_seconds, self.step_up_ttl_seconds, self.withdraw_ttl_seconds, self.recovery_ttl_seconds, self.critical_ttl_seconds):
            if ttl <= 0 or ttl > K1_MAX_TTL_SECONDS:
                raise LNURLK1ConfigurationError("Unsafe LNURL k1 TTL configuration.")

@dataclass(frozen=True, slots=True)
class K1Record:
    registry_id: str
    k1_lookup_hash: str
    k1_fingerprint: str
    purpose: LNURLK1Purpose
    expected_domain: str
    lnurl_action: str | None
    internal_action: str | None
    policy_hash: str | None
    principal_hash: str | None
    device_key_fingerprint: str | None
    session_hash: str | None
    payment_request_hash: str | None
    withdraw_request_hash: str | None
    recovery_attempt_hash: str | None
    metadata_hash: str | None
    status: LNURLK1Status
    issued_at: datetime
    expires_at: datetime
    consumed_at: datetime | None = None
    revoked_at: datetime | None = None
    failure_count: int = 0
    max_failures: int = DEFAULT_K1_MAX_FAILURES
    updated_at: datetime | None = None

@dataclass(frozen=True, slots=True)
class IssuedK1:
    k1: str = field(repr=False)
    registry_id: str
    k1_fingerprint: str
    purpose: LNURLK1Purpose
    lnurl_action: str | None
    internal_action: str | None
    expected_domain: str
    expires_at: datetime

@dataclass(frozen=True, slots=True)
class K1StatusResult:
    registry_id: str | None
    status: LNURLK1Status | str
    purpose: LNURLK1Purpose | None = None
    lnurl_action: str | None = None
    internal_action: str | None = None
    expected_domain: str | None = None
    expires_at: datetime | None = None
    policy_hash: str | None = None
    principal_hash: str | None = None
    device_key_fingerprint: str | None = None
    failure_count: int = 0
    reason_code: str | None = None

@dataclass(frozen=True, slots=True)
class ConsumedK1Context:
    registry_id: str
    k1_fingerprint: str
    purpose: LNURLK1Purpose
    lnurl_action: str | None
    internal_action: str | None
    expected_domain: str
    policy_hash: str | None
    principal_hash: str | None
    device_key_fingerprint: str | None
    session_hash: str | None
    payment_request_hash: str | None
    withdraw_request_hash: str | None
    recovery_attempt_hash: str | None
    consumed_at: datetime

@dataclass(frozen=True, slots=True)
class K1FailureResult:
    registry_id: str | None
    status: LNURLK1Status | str
    failure_count: int
    terminal: bool
    reason_code: str

@dataclass(frozen=True, slots=True)
class RevokedK1Result:
    registry_id: str | None
    status: LNURLK1Status | str
    revoked: bool
    reason_code: str

class InMemoryK1Repository:
    """Thread-safe repository used by tests and single-process deployments.

    The production SQL table already stores hashed k1 values. A SQLAlchemy
    adapter can map these records onto ``lnurl_auth_challenges`` using k1_hash
    for the HMAC lookup hash and challenge_hash for the non-secret fingerprint.
    """

    def __init__(self) -> None:
        self._records: dict[str, K1Record] = {}
        self._lock = threading.Lock()

    def insert(self, record: K1Record) -> K1Record:
        with self._lock:
            if record.k1_lookup_hash in self._records:
                raise LNURLK1ConfigurationError("Duplicate k1 lookup hash.")
            self._records[record.k1_lookup_hash] = record
            return record

    def get(self, lookup_hash: str) -> K1Record | None:
        with self._lock:
            return self._records.get(lookup_hash)

    def update(self, lookup_hash: str, record: K1Record) -> K1Record:
        with self._lock:
            self._records[lookup_hash] = record
            return record

    def consume_if_active(self, lookup_hash: str, now: datetime) -> K1Record:
        with self._lock:
            record = self._records.get(lookup_hash)
            if record is None:
                raise LNURLK1UnknownError()
            if record.status is not LNURLK1Status.ACTIVE:
                raise _terminal_error(record.status)
            if record.expires_at <= now:
                expired = replace(record, status=LNURLK1Status.EXPIRED, updated_at=now)
                self._records[lookup_hash] = expired
                raise LNURLK1ExpiredError()
            consumed = replace(record, status=LNURLK1Status.CONSUMED, consumed_at=now, updated_at=now)
            self._records[lookup_hash] = consumed
            return consumed

    def records(self) -> tuple[K1Record, ...]:
        with self._lock:
            return tuple(self._records.values())


class SQLAlchemyK1Repository:
    """SQLAlchemy repository backed by the existing hash-first LNURL table.

    ``LNURLAuthChallenge.k1_hash`` stores the HMAC lookup hash and
    ``challenge_hash`` stores the non-secret k1 fingerprint. Additional prompt-21
    fields are persisted in redacted ``metadata_json`` until a later migration can
    add dedicated columns. Raw k1 is never persisted.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def insert(self, record: K1Record) -> K1Record:
        row = LNURLAuthChallenge(
            challenge_hash=record.k1_fingerprint,
            k1_hash=record.k1_lookup_hash,
            action=record.lnurl_action or record.purpose.value,
            internal_action=record.internal_action,
            auth_domain=record.expected_domain,
            principal_hash=record.principal_hash,
            device_key_fingerprint=record.device_key_fingerprint,
            policy_hash=record.policy_hash,
            status=record.status.value,
            issued_at=record.issued_at,
            expires_at=record.expires_at,
            used_at=record.consumed_at,
            metadata_json=_record_metadata(record),
        )
        self.db.add(row)
        self.db.flush()
        return record

    def get(self, lookup_hash: str) -> K1Record | None:
        row = self.db.query(LNURLAuthChallenge).filter(LNURLAuthChallenge.k1_hash == lookup_hash).one_or_none()
        return _record_from_row(row) if row is not None else None

    def update(self, lookup_hash: str, record: K1Record) -> K1Record:
        row = self.db.query(LNURLAuthChallenge).filter(LNURLAuthChallenge.k1_hash == lookup_hash).one()
        _apply_record_to_row(row, record)
        self.db.flush()
        return record

    def consume_if_active(self, lookup_hash: str, now: datetime) -> K1Record:
        query = self.db.query(LNURLAuthChallenge).filter(LNURLAuthChallenge.k1_hash == lookup_hash)
        row = query.with_for_update().one_or_none()
        if row is None:
            raise LNURLK1UnknownError()
        record = _record_from_row(row)
        if record.status is not LNURLK1Status.ACTIVE:
            raise _terminal_error(record.status)
        if record.expires_at <= now:
            expired = replace(record, status=LNURLK1Status.EXPIRED, updated_at=now)
            _apply_record_to_row(row, expired)
            self.db.flush()
            raise LNURLK1ExpiredError()
        consumed = replace(record, status=LNURLK1Status.CONSUMED, consumed_at=now, updated_at=now)
        _apply_record_to_row(row, consumed)
        self.db.flush()
        return consumed

    def records(self) -> tuple[K1Record, ...]:
        return tuple(_record_from_row(row) for row in self.db.query(LNURLAuthChallenge).all())

AuditEmitter = Callable[[str, Mapping[str, Any]], None]
MetricsEmitter = Callable[[str, Mapping[str, str]], None]

class LNURLK1RegistryService:
    def __init__(
        self,
        *,
        config: LNURLK1Config,
        repository: InMemoryK1Repository | None = None,
        clock: Callable[[], datetime] | None = None,
        random_bytes: Callable[[int], bytes] | None = None,
        audit_emitter: AuditEmitter | None = None,
        metrics_emitter: MetricsEmitter | None = None,
    ) -> None:
        self.config = config
        self.repository = repository or InMemoryK1Repository()
        self.clock = clock or (lambda: datetime.now(UTC))
        self.random_bytes = random_bytes or secrets.token_bytes
        self.audit_emitter = audit_emitter
        self.metrics_emitter = metrics_emitter

    def generate_k1(self) -> str:
        raw = self.random_bytes(K1_BYTES)
        if len(raw) != K1_BYTES:
            raise LNURLK1ConfigurationError("Random source returned an invalid k1 length.")
        return raw.hex()

    def issue_k1(
        self,
        purpose: LNURLK1Purpose | str,
        expected_domain: str,
        *,
        lnurl_action: str | None = None,
        internal_action: str | None = None,
        policy_hash: str | None = None,
        principal_hash: str | None = None,
        device_key_fingerprint: str | None = None,
        session_hash: str | None = None,
        payment_request_hash: str | None = None,
        withdraw_request_hash: str | None = None,
        recovery_attempt_hash: str | None = None,
        metadata_hash: str | None = None,
        ttl_seconds: int | None = None,
        max_failures: int | None = None,
    ) -> IssuedK1:
        purpose_enum = purpose if isinstance(purpose, LNURLK1Purpose) else LNURLK1Purpose(str(purpose))
        domain = _normalize_expected_domain(expected_domain)
        _validate_policy_requirements(purpose_enum, policy_hash)
        ttl = ttl_seconds or self._ttl_for_purpose(purpose_enum)
        _validate_ttl(ttl)
        now = self.clock()
        k1 = self.generate_k1()
        lookup_hash = self._lookup_hash(k1)
        fingerprint = self._fingerprint(k1)
        record = K1Record(
            registry_id=sha256_prefixed(f"registry:{fingerprint}:{now.isoformat()}"),
            k1_lookup_hash=lookup_hash,
            k1_fingerprint=fingerprint,
            purpose=purpose_enum,
            expected_domain=domain,
            lnurl_action=lnurl_action,
            internal_action=internal_action,
            policy_hash=policy_hash,
            principal_hash=principal_hash,
            device_key_fingerprint=device_key_fingerprint,
            session_hash=session_hash,
            payment_request_hash=payment_request_hash,
            withdraw_request_hash=withdraw_request_hash,
            recovery_attempt_hash=recovery_attempt_hash,
            metadata_hash=metadata_hash,
            status=LNURLK1Status.ACTIVE,
            issued_at=now,
            expires_at=now + timedelta(seconds=ttl),
            max_failures=max_failures or self.config.max_failures,
            updated_at=now,
        )
        self.repository.insert(record)
        self._emit("lnurl_k1_issued", record, reason_code="issued")
        return IssuedK1(k1, record.registry_id, fingerprint, purpose_enum, lnurl_action, internal_action, domain, record.expires_at)

    def get_k1_status(self, raw_k1: str) -> K1StatusResult:
        try:
            lookup = self._lookup_hash(raw_k1)
        except LNURLK1MalformedError:
            return K1StatusResult(None, "invalid", reason_code="malformed_k1")
        record = self.repository.get(lookup)
        if record is None:
            return K1StatusResult(None, "invalid", reason_code="unknown_k1")
        record = self._effective_record(record)
        return _status_result(record)

    def get_k1_status_by_registry_id(self, registry_id: str) -> K1StatusResult | None:
        record = next((r for r in self.repository.records() if r.registry_id == registry_id), None)
        if record is None:
            return None
        return _status_result(self._effective_record(record))

    def consume_k1(self, raw_k1: str, **expected: str | None) -> ConsumedK1Context:
        lookup = self._lookup_hash(raw_k1)
        pre = self.repository.get(lookup)
        if pre is None:
            self._emit_generic("lnurl_k1_replay_rejected", reason_code="unknown_k1")
            raise LNURLK1UnknownError()
        if pre.status is not LNURLK1Status.ACTIVE:
            self._emit("lnurl_k1_replay_rejected", pre, reason_code="reused_k1")
            self._metric("lnurl_k1_replay_rejected_total", pre, result="replay")
            raise _terminal_error(pre.status)
        self._check_bindings(pre, expected)
        try:
            consumed = self.repository.consume_if_active(lookup, self.clock())
        except LNURLK1ConsumedError:
            self._emit("lnurl_k1_replay_rejected", pre, reason_code="reused_k1")
            self._metric("lnurl_k1_replay_rejected_total", pre, result="replay")
            raise
        self._emit("lnurl_k1_consumed", consumed, reason_code="consumed")
        self._metric("lnurl_k1_consumed_total", consumed, result="consumed")
        return ConsumedK1Context(
            consumed.registry_id,
            consumed.k1_fingerprint,
            consumed.purpose,
            consumed.lnurl_action,
            consumed.internal_action,
            consumed.expected_domain,
            consumed.policy_hash,
            consumed.principal_hash,
            consumed.device_key_fingerprint,
            consumed.session_hash,
            consumed.payment_request_hash,
            consumed.withdraw_request_hash,
            consumed.recovery_attempt_hash,
            consumed.consumed_at or self.clock(),
        )

    def record_k1_failure(self, raw_k1: str, reason_code: str, *, terminal: bool = False) -> K1FailureResult:
        try:
            lookup = self._lookup_hash(raw_k1)
        except LNURLK1MalformedError:
            return K1FailureResult(None, "invalid", 0, True, "malformed_k1")
        record = self.repository.get(lookup)
        if record is None:
            return K1FailureResult(None, "invalid", 0, True, "unknown_k1")
        now = self.clock()
        record = self._effective_record(record)
        if record.status is not LNURLK1Status.ACTIVE:
            return K1FailureResult(record.registry_id, record.status, record.failure_count, True, reason_code)
        fail_count = record.failure_count + 1
        critical_terminal = self.config.one_attempt_for_critical_actions and record.purpose in _CRITICAL_PURPOSES
        make_terminal = terminal or critical_terminal or fail_count >= record.max_failures
        status = LNURLK1Status.FAILED if make_terminal else LNURLK1Status.ACTIVE
        updated = replace(record, failure_count=fail_count, status=status, updated_at=now)
        self.repository.update(record.k1_lookup_hash, updated)
        self._emit("lnurl_k1_failure_limit_reached" if make_terminal else "lnurl_k1_binding_mismatch", updated, reason_code=reason_code)
        return K1FailureResult(record.registry_id, status, fail_count, make_terminal, reason_code)

    def revoke_k1(self, *, raw_k1: str | None = None, registry_id: str | None = None, reason_code: str, actor_hash: str | None = None) -> RevokedK1Result:
        record = self._find_for_revocation(raw_k1=raw_k1, registry_id=registry_id)
        if record is None:
            return RevokedK1Result(None, "invalid", False, reason_code)
        if record.status in {LNURLK1Status.CONSUMED, LNURLK1Status.EXPIRED, LNURLK1Status.REVOKED, LNURLK1Status.FAILED}:
            return RevokedK1Result(record.registry_id, record.status, False, reason_code)
        revoked = replace(record, status=LNURLK1Status.REVOKED, revoked_at=self.clock(), updated_at=self.clock())
        self.repository.update(record.k1_lookup_hash, revoked)
        self._emit("lnurl_k1_revoked", revoked, reason_code=reason_code, actor_hash=actor_hash)
        return RevokedK1Result(record.registry_id, LNURLK1Status.REVOKED, True, reason_code)

    def revoke_active_k1_for_binding(self, *, reason_code: str, **bindings: str | None) -> int:
        count = 0
        for record in self.repository.records():
            if record.status is LNURLK1Status.ACTIVE and all(getattr(record, k) == v for k, v in bindings.items() if v is not None):
                self.repository.update(record.k1_lookup_hash, replace(record, status=LNURLK1Status.REVOKED, revoked_at=self.clock(), updated_at=self.clock()))
                count += 1
        return count

    def expire_stale_k1(self, now: datetime | None = None) -> int:
        effective_now = now or self.clock()
        count = 0
        for record in self.repository.records():
            if record.status is LNURLK1Status.ACTIVE and record.expires_at <= effective_now:
                expired = replace(record, status=LNURLK1Status.EXPIRED, updated_at=effective_now)
                self.repository.update(record.k1_lookup_hash, expired)
                self._emit("lnurl_k1_expired", expired, reason_code="expired_k1")
                count += 1
        return count

    def purge_terminal_k1(self, before: datetime) -> int:
        # Existing DB/audit retention owns durable deletion. In-memory repository keeps
        # records for deterministic tests and returns the purgeable count.
        return sum(1 for r in self.repository.records() if r.status is not LNURLK1Status.ACTIVE and (r.updated_at or r.issued_at) < before)

    def _lookup_hash(self, raw_k1: str) -> str:
        validate_k1_format(raw_k1)
        return hmac_sha256_prefixed(self.config.server_pepper, bytes.fromhex(raw_k1))

    def _fingerprint(self, raw_k1: str) -> str:
        validate_k1_format(raw_k1)
        return sha256_prefixed(bytes.fromhex(raw_k1))

    def _ttl_for_purpose(self, purpose: LNURLK1Purpose) -> int:
        if purpose in {LNURLK1Purpose.LNURL_AUTH_REGISTER, LNURLK1Purpose.LNURL_AUTH_LOGIN, LNURLK1Purpose.LNURL_AUTH_LINK}:
            return self.config.auth_ttl_seconds
        if purpose is LNURLK1Purpose.LNURL_AUTH_STEP_UP:
            return self.config.step_up_ttl_seconds
        if purpose in {LNURLK1Purpose.LNURL_WITHDRAW, LNURLK1Purpose.PAYREGISTER_REFUND}:
            return self.config.withdraw_ttl_seconds
        if purpose is LNURLK1Purpose.RECOVERY_FACTOR:
            return self.config.recovery_ttl_seconds
        return self.config.critical_ttl_seconds

    def _effective_record(self, record: K1Record) -> K1Record:
        if record.status is LNURLK1Status.ACTIVE and record.expires_at <= self.clock():
            expired = replace(record, status=LNURLK1Status.EXPIRED, updated_at=self.clock())
            self.repository.update(record.k1_lookup_hash, expired)
            return expired
        return record

    def _find_for_revocation(self, *, raw_k1: str | None, registry_id: str | None) -> K1Record | None:
        if raw_k1:
            return self.repository.get(self._lookup_hash(raw_k1))
        if registry_id:
            return next((r for r in self.repository.records() if r.registry_id == registry_id), None)
        return None

    def _check_bindings(self, record: K1Record, expected: Mapping[str, str | None]) -> None:
        record = self._effective_record(record)
        if record.status is not LNURLK1Status.ACTIVE:
            raise _terminal_error(record.status)
        mapping = {
            "expected_purpose": (record.purpose.value, LNURLK1ActionMismatchError),
            "expected_lnurl_action": (record.lnurl_action, LNURLK1ActionMismatchError),
            "expected_internal_action": (record.internal_action, LNURLK1ActionMismatchError),
            "expected_domain": (record.expected_domain, LNURLK1DomainMismatchError),
            "expected_policy_hash": (record.policy_hash, LNURLK1PolicyMismatchError),
            "expected_principal_hash": (record.principal_hash, LNURLK1BindingMismatchError),
            "expected_device_key_fingerprint": (record.device_key_fingerprint, LNURLK1BindingMismatchError),
            "expected_session_hash": (record.session_hash, LNURLK1BindingMismatchError),
            "expected_payment_request_hash": (record.payment_request_hash, LNURLK1BindingMismatchError),
            "expected_withdraw_request_hash": (record.withdraw_request_hash, LNURLK1BindingMismatchError),
            "expected_recovery_attempt_hash": (record.recovery_attempt_hash, LNURLK1BindingMismatchError),
        }
        for key, (actual, exc_type) in mapping.items():
            supplied = expected.get(key)
            if supplied is not None:
                normalized_supplied = _normalize_expected_domain(supplied) if key == "expected_domain" else supplied
                if actual != normalized_supplied:
                    self._emit("lnurl_k1_binding_mismatch", record, reason_code=key.removeprefix("expected_") + "_mismatch")
                    raise exc_type()

    def _emit(self, event: str, record: K1Record, *, reason_code: str, actor_hash: str | None = None) -> None:
        if self.audit_emitter:
            self.audit_emitter(event, _audit_payload(record, reason_code=reason_code, actor_hash=actor_hash))
        self._metric(event + "_total", record, result=reason_code)

    def _emit_generic(self, event: str, *, reason_code: str) -> None:
        if self.audit_emitter:
            self.audit_emitter(event, {"reason_code": reason_code, "timestamp": self.clock().isoformat()})

    def _metric(self, name: str, record: K1Record, *, result: str) -> None:
        if self.metrics_emitter:
            self.metrics_emitter(name, {"purpose": record.purpose.value, "lnurl_action": record.lnurl_action or "none", "result": result})

def generate_k1() -> str:
    return secrets.token_hex(K1_BYTES)

def validate_k1_format(raw_k1: str) -> None:
    if not isinstance(raw_k1, str) or _K1_RE.fullmatch(raw_k1) is None:
        raise LNURLK1MalformedError()

def _normalize_expected_domain(domain: str) -> str:
    if not domain or "://" in domain or "/" in domain or "@" in domain or "#" in domain:
        raise LNURLK1DomainMismatchError()
    normalized = domain.rstrip(".").lower()
    if not hostname_matches_allowlist(normalized, [normalized]):
        raise LNURLK1DomainMismatchError()
    return normalized

def _validate_ttl(ttl: int) -> None:
    if ttl <= 0 or ttl > K1_MAX_TTL_SECONDS:
        raise LNURLK1ConfigurationError("Unsafe LNURL k1 TTL.")

def _validate_policy_requirements(purpose: LNURLK1Purpose, policy_hash: str | None) -> None:
    if purpose in _CRITICAL_PURPOSES and not policy_hash:
        raise LNURLK1PolicyMismatchError()

def _terminal_error(status: LNURLK1Status) -> Exception:
    if status is LNURLK1Status.CONSUMED:
        return LNURLK1ConsumedError()
    if status is LNURLK1Status.EXPIRED:
        return LNURLK1ExpiredError()
    if status is LNURLK1Status.REVOKED:
        return LNURLK1RevokedError()
    return LNURLK1ConsumedError()

def _status_result(record: K1Record) -> K1StatusResult:
    return K1StatusResult(record.registry_id, record.status, record.purpose, record.lnurl_action, record.internal_action, record.expected_domain, record.expires_at, record.policy_hash, record.principal_hash, record.device_key_fingerprint, record.failure_count)


def _record_metadata(record: K1Record) -> dict[str, Any]:
    return {
        "registry_id": record.registry_id,
        "purpose": record.purpose.value,
        "session_hash": record.session_hash,
        "payment_request_hash": record.payment_request_hash,
        "withdraw_request_hash": record.withdraw_request_hash,
        "recovery_attempt_hash": record.recovery_attempt_hash,
        "metadata_hash": record.metadata_hash,
        "failure_count": record.failure_count,
        "max_failures": record.max_failures,
        "revoked_at": record.revoked_at.isoformat() if record.revoked_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }

def _record_from_row(row: LNURLAuthChallenge) -> K1Record:
    metadata = row.metadata_json or {}
    return K1Record(
        registry_id=str(metadata.get("registry_id") or row.challenge_hash),
        k1_lookup_hash=row.k1_hash,
        k1_fingerprint=row.challenge_hash,
        purpose=LNURLK1Purpose(str(metadata.get("purpose") or row.action)),
        expected_domain=row.auth_domain,
        lnurl_action=row.action,
        internal_action=row.internal_action,
        policy_hash=row.policy_hash,
        principal_hash=row.principal_hash,
        device_key_fingerprint=row.device_key_fingerprint,
        session_hash=metadata.get("session_hash"),
        payment_request_hash=metadata.get("payment_request_hash"),
        withdraw_request_hash=metadata.get("withdraw_request_hash"),
        recovery_attempt_hash=metadata.get("recovery_attempt_hash"),
        metadata_hash=metadata.get("metadata_hash"),
        status=LNURLK1Status(row.status),
        issued_at=row.issued_at,
        expires_at=row.expires_at,
        consumed_at=row.used_at,
        revoked_at=datetime.fromisoformat(metadata["revoked_at"]) if metadata.get("revoked_at") else None,
        failure_count=int(metadata.get("failure_count") or 0),
        max_failures=int(metadata.get("max_failures") or DEFAULT_K1_MAX_FAILURES),
        updated_at=datetime.fromisoformat(metadata["updated_at"]) if metadata.get("updated_at") else row.updated_at,
    )

def _apply_record_to_row(row: LNURLAuthChallenge, record: K1Record) -> None:
    row.challenge_hash = record.k1_fingerprint
    row.k1_hash = record.k1_lookup_hash
    row.action = record.lnurl_action or record.purpose.value
    row.internal_action = record.internal_action
    row.auth_domain = record.expected_domain
    row.principal_hash = record.principal_hash
    row.device_key_fingerprint = record.device_key_fingerprint
    row.policy_hash = record.policy_hash
    row.status = record.status.value
    row.issued_at = record.issued_at
    row.expires_at = record.expires_at
    row.used_at = record.consumed_at
    row.metadata_json = _record_metadata(record)

def _audit_payload(record: K1Record, *, reason_code: str, actor_hash: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "registry_id": record.registry_id,
        "k1_fingerprint": record.k1_fingerprint,
        "purpose": record.purpose.value,
        "lnurl_action": record.lnurl_action,
        "internal_action": record.internal_action,
        "status": record.status.value,
        "expected_domain_hash": sha256_prefixed(record.expected_domain),
        "policy_hash": record.policy_hash,
        "timestamp": (record.updated_at or record.issued_at).isoformat(),
        "reason_code": reason_code,
    }
    if actor_hash:
        payload["actor_hash"] = actor_hash
    return payload

_CRITICAL_PURPOSES = frozenset({
    LNURLK1Purpose.LNURL_AUTH_STEP_UP,
    LNURLK1Purpose.LNURL_WITHDRAW,
    LNURLK1Purpose.PAYREGISTER_REFUND,
    LNURLK1Purpose.RECOVERY_FACTOR,
    LNURLK1Purpose.BUSINESS_APPROVAL,
    LNURLK1Purpose.SOVEREIGN_APPROVAL,
})

__all__ = [
    "ConsumedK1Context", "DEFAULT_K1_MAX_FAILURES", "InMemoryK1Repository", "IssuedK1", "K1Record", "K1StatusResult", "K1FailureResult", "K1_HEX_LENGTH", "K1_BYTES", "LNURLK1Config", "LNURLK1FailureReason", "LNURLK1Purpose", "LNURLK1RegistryService", "SQLAlchemyK1Repository", "LNURLK1Status", "RevokedK1Result", "generate_k1", "validate_k1_format",
]
