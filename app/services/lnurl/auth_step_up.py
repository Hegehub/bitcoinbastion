"""LNURL-auth step-up service for critical Bastion actions.

The service uses an already verified LNURL-auth ``action=auth`` proof as a fresh
proof-of-control factor, but never treats that proof as standalone
authorization. Approval also requires an active principal, active Device Binding,
active PoP session, structured human intent, Policy Engine allow decision,
revocation checks, and audit events.
"""
from __future__ import annotations

import secrets
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any, Protocol

from app.domain.lnurl.auth import BastionLNURLIntentAction, LNURLAuthAction
from app.domain.lnurl.principals import LightningPrincipalStatus
from app.domain.wallet_auth.devices import WalletDeviceClass, WalletDeviceStatus, is_root_of_trust_device_class
from app.domain.wallet_auth.proofs import WalletVerificationStrength
from app.services.access.crypto.hashing import canonical_json, hmac_sha256_prefixed, sha256_prefixed
from app.services.lnurl.auth_challenge_service import LNURLAuthChallengeResult, LNURLAuthChallengeService
from app.services.lnurl.auth_session_bridge import VerifiedLNURLAuthSessionInput
from app.services.lnurl.principal_service import LightningPrincipalService
from app.services.wallet_auth.privacy_commitments import reject_forbidden_wallet_secret_input
from app.services.wallet_auth.session_service import EntitlementSnapshot, PolicyDecision

STEP_UP_INTENT_TYPE = "bastion_lnurl_auth_step_up_intent"
STEP_UP_INTENT_VERSION = 1
STEP_UP_WARNING = "This signature does not authorize a Bitcoin transaction. It only confirms this Bastion security action."
DEFAULT_STEP_UP_TTL_SECONDS = 300
CRITICAL_STEP_UP_TTL_SECONDS = 120


class LNURLStepUpStatus(StrEnum):
    PENDING = "pending"
    CHALLENGE_ISSUED = "challenge_issued"
    PROOF_VERIFIED = "proof_verified"
    POLICY_PENDING = "policy_pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    CONSUMED = "consumed"
    REVOKED = "revoked"


class LNURLStepUpFailureReason(StrEnum):
    INVALID_ACTION = "lnurl_step_up_invalid_action"
    SESSION_REQUIRED = "lnurl_step_up_session_required"
    SESSION_MISMATCH = "lnurl_step_up_session_mismatch"
    DEVICE_MISMATCH = "lnurl_step_up_device_mismatch"
    PRINCIPAL_MISMATCH = "lnurl_step_up_principal_mismatch"
    CHALLENGE_EXPIRED = "lnurl_step_up_challenge_expired"
    CHALLENGE_USED = "lnurl_step_up_challenge_used"
    PROOF_INVALID = "lnurl_step_up_proof_invalid"
    POLICY_DENIED = "lnurl_step_up_policy_denied"
    ADDITIONAL_FACTOR_REQUIRED = "lnurl_step_up_additional_factor_required"
    QUORUM_REQUIRED = "lnurl_step_up_quorum_required"
    REVOKED = "lnurl_step_up_revoked"
    EXPIRED = "lnurl_step_up_expired"
    ALREADY_CONSUMED = "lnurl_step_up_already_consumed"
    SCOPE_TAMPERING = "lnurl_step_up_scope_tampering"
    RESOURCE_TAMPERING = "lnurl_step_up_resource_tampering"
    POLICY_TAMPERING = "lnurl_step_up_policy_tampering"
    SECRET_INPUT_REJECTED = "lnurl_step_up_secret_input_rejected"


class LNURLAuthStepUpError(ValueError):
    def __init__(self, reason_code: str) -> None:
        self.reason_code = reason_code
        super().__init__(reason_code)


class LNURLAuthStepUpInvalidActionError(LNURLAuthStepUpError): ...
class LNURLAuthStepUpSessionError(LNURLAuthStepUpError): ...
class LNURLAuthStepUpMismatchError(LNURLAuthStepUpError): ...
class LNURLAuthStepUpProofError(LNURLAuthStepUpError): ...
class LNURLAuthStepUpPolicyError(LNURLAuthStepUpError): ...
class LNURLAuthStepUpRevokedError(LNURLAuthStepUpError): ...
class LNURLAuthStepUpExpiredError(LNURLAuthStepUpError): ...
class LNURLAuthStepUpConsumedError(LNURLAuthStepUpError): ...


class LNURLStepUpCriticalAction(StrEnum):
    CREATE_API_KEY = "create_api_key"
    INCREASE_SCOPE = "increase_scope"
    EXPORT_DATA = "export_data"
    CREATE_DELEGATED_PASS = "create_delegated_pass"
    TREASURY_POLICY_CHANGE = "treasury_policy_change"
    RECOVERY_CHANGE = "recovery_change"
    RECOVERY_COMPLETE = "recovery_complete"
    DEVICE_ADD = "device_add"
    DEVICE_REVOKE = "device_revoke"
    LOCKDOWN_RELEASE = "lockdown_release"
    BUSINESS_ROLE_ASSIGNMENT = "business_role_assignment"
    ENTERPRISE_POLICY_CHANGE = "enterprise_policy_change"
    PAYREGISTER_ADMIN_ENABLE = "payregister_admin_enable"
    PAYREGISTER_DEVICE_ENROLL = "payregister_device_enroll"
    OFFLINE_PACK_ISSUE = "offline_pack_issue"
    REFUND_APPROVE = "refund_approve"
    PAYOUT_APPROVE = "payout_approve"


_DOMAIN_ACTION_MAP: dict[LNURLStepUpCriticalAction, BastionLNURLIntentAction] = {
    LNURLStepUpCriticalAction.CREATE_API_KEY: BastionLNURLIntentAction.CREATE_API_KEY,
    LNURLStepUpCriticalAction.INCREASE_SCOPE: BastionLNURLIntentAction.INCREASE_SCOPE,
    LNURLStepUpCriticalAction.RECOVERY_COMPLETE: BastionLNURLIntentAction.RECOVERY_COMPLETE,
    LNURLStepUpCriticalAction.DEVICE_ADD: BastionLNURLIntentAction.DEVICE_ADD,
    LNURLStepUpCriticalAction.LOCKDOWN_RELEASE: BastionLNURLIntentAction.LOCKDOWN_RELEASE,
    LNURLStepUpCriticalAction.BUSINESS_ROLE_ASSIGNMENT: BastionLNURLIntentAction.BUSINESS_ROLE_CHANGE,
    LNURLStepUpCriticalAction.ENTERPRISE_POLICY_CHANGE: BastionLNURLIntentAction.ENTERPRISE_POLICY_CHANGE,
    LNURLStepUpCriticalAction.PAYREGISTER_ADMIN_ENABLE: BastionLNURLIntentAction.PAYREGISTER_ADMIN_ENABLE,
}

_SINGLE_USE_ACTIONS = frozenset(
    {
        LNURLStepUpCriticalAction.CREATE_API_KEY,
        LNURLStepUpCriticalAction.INCREASE_SCOPE,
        LNURLStepUpCriticalAction.TREASURY_POLICY_CHANGE,
        LNURLStepUpCriticalAction.RECOVERY_COMPLETE,
        LNURLStepUpCriticalAction.DEVICE_ADD,
        LNURLStepUpCriticalAction.LOCKDOWN_RELEASE,
        LNURLStepUpCriticalAction.BUSINESS_ROLE_ASSIGNMENT,
        LNURLStepUpCriticalAction.ENTERPRISE_POLICY_CHANGE,
        LNURLStepUpCriticalAction.PAYREGISTER_ADMIN_ENABLE,
        LNURLStepUpCriticalAction.OFFLINE_PACK_ISSUE,
        LNURLStepUpCriticalAction.REFUND_APPROVE,
        LNURLStepUpCriticalAction.PAYOUT_APPROVE,
    }
)

_SCOPE_VOCABULARY: dict[LNURLStepUpCriticalAction, frozenset[str]] = {
    LNURLStepUpCriticalAction.CREATE_API_KEY: frozenset({"api_key:create", "read", "metrics:read"}),
    LNURLStepUpCriticalAction.INCREASE_SCOPE: frozenset({"scope:increase", "read", "write"}),
    LNURLStepUpCriticalAction.EXPORT_DATA: frozenset({"data:export", "read"}),
    LNURLStepUpCriticalAction.CREATE_DELEGATED_PASS: frozenset({"delegated_pass:create"}),
    LNURLStepUpCriticalAction.TREASURY_POLICY_CHANGE: frozenset({"treasury:policy:write"}),
    LNURLStepUpCriticalAction.RECOVERY_CHANGE: frozenset({"recovery:change"}),
    LNURLStepUpCriticalAction.RECOVERY_COMPLETE: frozenset({"recovery:complete"}),
    LNURLStepUpCriticalAction.DEVICE_ADD: frozenset({"device:add"}),
    LNURLStepUpCriticalAction.DEVICE_REVOKE: frozenset({"device:revoke"}),
    LNURLStepUpCriticalAction.LOCKDOWN_RELEASE: frozenset({"lockdown:release"}),
    LNURLStepUpCriticalAction.BUSINESS_ROLE_ASSIGNMENT: frozenset({"business_role:assign"}),
    LNURLStepUpCriticalAction.ENTERPRISE_POLICY_CHANGE: frozenset({"enterprise_policy:write"}),
    LNURLStepUpCriticalAction.PAYREGISTER_ADMIN_ENABLE: frozenset({"payregister:admin"}),
    LNURLStepUpCriticalAction.PAYREGISTER_DEVICE_ENROLL: frozenset({"payregister_device:enroll"}),
    LNURLStepUpCriticalAction.OFFLINE_PACK_ISSUE: frozenset({"offline_pack:issue"}),
    LNURLStepUpCriticalAction.REFUND_APPROVE: frozenset({"refund:approve"}),
    LNURLStepUpCriticalAction.PAYOUT_APPROVE: frozenset({"payout:approve"}),
}


@dataclass(frozen=True, slots=True)
class ActivePoPSessionContext:
    session_reference: str = field(repr=False)
    session_fingerprint: str
    principal_hash: str
    device_key_fingerprint: str
    status: str
    expires_at: datetime
    approved_scopes: tuple[str, ...]
    auth_domain: str
    recovery_state: str = "active"
    locked_down: bool = False


@dataclass(frozen=True, slots=True)
class ActiveDeviceContext:
    device_key_fingerprint: str
    status: WalletDeviceStatus
    device_class: WalletDeviceClass
    risk_score: int = 0
    risk_level: str = "low"


@dataclass(frozen=True, slots=True)
class LNURLAuthStepUpRequest:
    principal_hash: str
    device_key_fingerprint: str
    session_reference: str = field(repr=False)
    action: LNURLStepUpCriticalAction
    requested_scopes: tuple[str, ...]
    resource_type: str
    resource_hash: str
    risk_level: str
    intent_metadata: Mapping[str, object] = field(default_factory=dict, repr=False)
    requested_ttl_seconds: int | None = None


@dataclass(frozen=True, slots=True)
class LNURLAuthStepUpIntent:
    type: str
    version: int
    domain: str
    lnurl_action: str
    internal_action: str
    purpose: str
    principal_pseudonym: str
    device_key_fingerprint: str
    session_fingerprint: str
    requested_scopes: tuple[str, ...]
    resource_type: str
    resource_hash: str
    risk_level: str
    policy_hash: str
    challenge_id: str
    k1_commitment: str
    issued_at: datetime
    expires_at: datetime
    cannot_access: tuple[str, ...]
    human_readable_warning: str
    details: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class LNURLAuthStepUpRecord:
    step_up_id: str
    status: LNURLStepUpStatus
    principal_hash: str
    device_key_fingerprint: str
    session_fingerprint: str
    session_reference_hash: str
    action: LNURLStepUpCriticalAction
    lnurl_action: LNURLAuthAction
    requested_scopes: tuple[str, ...]
    resource_type: str
    resource_hash: str
    risk_level: str
    policy_hash: str
    intent_hash: str
    challenge_id: str
    challenge_hash: str
    expected_lnurl_key_hash: str
    auth_domain: str
    issued_at: datetime
    expires_at: datetime
    metadata_hash: str
    approved_scopes: tuple[str, ...] = ()
    authorization_hash: str | None = None
    authorization_reference_hash: str | None = None
    audit_event_hash: str | None = None
    approved_at: datetime | None = None
    consumed_at: datetime | None = None
    revoked_at: datetime | None = None
    policy_decision_hash: str | None = None
    failure_reason: str | None = None


@dataclass(frozen=True, slots=True)
class LNURLAuthStepUpChallengeResponse:
    step_up_id: str
    status: LNURLStepUpStatus
    lnurl: str = field(repr=False)
    encoded_lnurl: str = field(repr=False)
    challenge_id: str
    action: LNURLStepUpCriticalAction
    intent_summary: Mapping[str, object]
    intent_hash: str
    policy_hash: str
    expires_at: datetime
    required_additional_factors: tuple[str, ...]
    policy_decision: str
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LNURLStepUpAuthorization:
    step_up_id: str
    principal_hash: str
    device_key_fingerprint: str
    session_fingerprint: str
    action: LNURLStepUpCriticalAction
    intent_hash: str
    policy_hash: str
    approved_scopes: tuple[str, ...]
    resource_hash: str
    verification_method: str
    verification_strength: WalletVerificationStrength
    approved_at: datetime
    expires_at: datetime
    status: LNURLStepUpStatus
    audit_event_hash: str | None
    authorization_reference: str | None = field(default=None, repr=False)


@dataclass(frozen=True, slots=True)
class LNURLAuthStepUpCompleteRequest:
    step_up_id: str
    session_reference: str = field(repr=False)
    verified_callback: VerifiedLNURLAuthSessionInput
    policy_hash: str
    intent_hash: str
    resource_hash: str
    requested_scopes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LNURLAuthStepUpResult:
    step_up_id: str
    status: LNURLStepUpStatus
    authorization: LNURLStepUpAuthorization | None
    policy_decision: str
    required_additional_factors: tuple[str, ...]
    reason_code: str
    audit_event_hash: str | None
    limitations: tuple[str, ...]


class LNURLAuthStepUpRepository:
    def __init__(self) -> None:
        self._records: dict[str, LNURLAuthStepUpRecord] = {}
        self._lock = threading.Lock()

    def create(self, record: LNURLAuthStepUpRecord) -> LNURLAuthStepUpRecord:
        with self._lock:
            self._records[record.step_up_id] = record
            return record

    def get(self, step_up_id: str) -> LNURLAuthStepUpRecord | None:
        with self._lock:
            return self._records.get(step_up_id)

    def update(self, record: LNURLAuthStepUpRecord) -> LNURLAuthStepUpRecord:
        with self._lock:
            if record.step_up_id not in self._records:
                raise LNURLAuthStepUpError("lnurl_step_up_not_found")
            self._records[record.step_up_id] = record
            return record

    def transition(self, step_up_id: str, *, expected: set[LNURLStepUpStatus], target: LNURLStepUpStatus, **changes: Any) -> LNURLAuthStepUpRecord:
        with self._lock:
            record = self._records.get(step_up_id)
            if record is None:
                raise LNURLAuthStepUpError("lnurl_step_up_not_found")
            if record.status not in expected:
                if record.status is LNURLStepUpStatus.CONSUMED:
                    raise LNURLAuthStepUpConsumedError(LNURLStepUpFailureReason.ALREADY_CONSUMED.value)
                raise LNURLAuthStepUpError("lnurl_step_up_invalid_transition")
            updated = replace(record, status=target, **changes)
            self._records[step_up_id] = updated
            return updated

    def records(self) -> tuple[LNURLAuthStepUpRecord, ...]:
        with self._lock:
            return tuple(self._records.values())


class SessionResolver(Protocol):
    async def resolve(self, session_reference: str) -> ActivePoPSessionContext: ...


class DeviceResolver(Protocol):
    async def assert_active(self, *, principal_hash: str, device_key_fingerprint: str) -> ActiveDeviceContext: ...


class EntitlementResolver(Protocol):
    async def get_entitlement_for_principal(self, principal_hash: str) -> EntitlementSnapshot: ...


class StepUpPolicyEngine(Protocol):
    async def decide_lnurl_step_up(self, context: Mapping[str, object]) -> PolicyDecision: ...


class RevocationChecker(Protocol):
    def is_revoked(self, *, target_type: str, target_hash: str) -> bool: ...


AuditEmitter = Callable[[str, Mapping[str, object]], None]
MetricsEmitter = Callable[[str, Mapping[str, str]], None]
Clock = Callable[[], datetime]


@dataclass(frozen=True, slots=True)
class LNURLAuthStepUpConfig:
    auth_domain: str = "auth.bitcoin-bastion.com"
    origin: str = "https://bitcoin-bastion.com"
    default_ttl_seconds: int = DEFAULT_STEP_UP_TTL_SECONDS
    critical_ttl_seconds: int = CRITICAL_STEP_UP_TTL_SECONDS
    authorization_reference_pepper: str = "test-step-up-reference-pepper"


class LNURLAuthStepUpService:
    def __init__(
        self,
        *,
        challenge_service: LNURLAuthChallengeService,
        principal_service: LightningPrincipalService,
        session_resolver: SessionResolver,
        device_resolver: DeviceResolver,
        entitlement_resolver: EntitlementResolver,
        policy_engine: StepUpPolicyEngine,
        repository: LNURLAuthStepUpRepository | None = None,
        revocation_checker: RevocationChecker | None = None,
        audit_emitter: AuditEmitter | None = None,
        metrics_emitter: MetricsEmitter | None = None,
        clock: Clock | None = None,
        config: LNURLAuthStepUpConfig = LNURLAuthStepUpConfig(),
    ) -> None:
        self.challenge_service = challenge_service
        self.principal_service = principal_service
        self.session_resolver = session_resolver
        self.device_resolver = device_resolver
        self.entitlement_resolver = entitlement_resolver
        self.policy_engine = policy_engine
        self.repository = repository or LNURLAuthStepUpRepository()
        self.revocation_checker = revocation_checker
        self.audit_emitter = audit_emitter
        self.metrics_emitter = metrics_emitter
        self.clock = clock or (lambda: datetime.now(UTC))
        self.config = config

    async def start_step_up(self, request: LNURLAuthStepUpRequest) -> LNURLAuthStepUpChallengeResponse:
        action = _normalize_action(request.action)
        _validate_request(request, action)
        session = await self.session_resolver.resolve(request.session_reference)
        self._validate_session(request, session)
        principal = self.principal_service.find_active_principal(request.principal_hash, device_key_fingerprint=request.device_key_fingerprint)
        if principal.status is not LightningPrincipalStatus.ACTIVE:
            if not _recovery_or_lockdown_action(action):
                raise LNURLAuthStepUpSessionError(LNURLStepUpFailureReason.SESSION_REQUIRED.value)
        device = await self.device_resolver.assert_active(principal_hash=request.principal_hash, device_key_fingerprint=request.device_key_fingerprint)
        self._validate_device(action, device, request)
        entitlement = await self.entitlement_resolver.get_entitlement_for_principal(request.principal_hash)
        self._check_revocations(principal_hash=request.principal_hash, device_key_fingerprint=request.device_key_fingerprint, session_fingerprint=session.session_fingerprint, extra=(request.resource_hash,))
        now = self.clock()
        ttl = self._ttl_for(action, request)
        expires_at = now + timedelta(seconds=ttl)
        policy_hash = self._policy_hash(request, session, entitlement, action)
        challenge = self.challenge_service.create_challenge(
            action=LNURLAuthAction.AUTH,
            internal_action=action.value,
            purpose="lnurl_auth_step_up",
            origin=self.config.origin,
            device_key_fingerprint=request.device_key_fingerprint,
            policy_hash=policy_hash,
            principal_hint_hash=request.principal_hash,
            requested_scopes=request.requested_scopes,
            risk_level=request.risk_level,
            expires_in_seconds=min(ttl, DEFAULT_STEP_UP_TTL_SECONDS),
            request_context={"step_up_action": action.value, "resource_hash": request.resource_hash, "session_fingerprint": session.session_fingerprint},
        )
        intent = self._build_intent(request=request, action=action, session=session, policy_hash=policy_hash, challenge=challenge, issued_at=now, expires_at=expires_at)
        intent_hash = _hash_intent(intent)
        step_up_id = _step_up_id(intent_hash)
        record = LNURLAuthStepUpRecord(
            step_up_id=step_up_id,
            status=LNURLStepUpStatus.CHALLENGE_ISSUED,
            principal_hash=request.principal_hash,
            device_key_fingerprint=request.device_key_fingerprint,
            session_fingerprint=session.session_fingerprint,
            session_reference_hash=sha256_prefixed(request.session_reference),
            action=action,
            lnurl_action=LNURLAuthAction.AUTH,
            requested_scopes=request.requested_scopes,
            resource_type=request.resource_type,
            resource_hash=request.resource_hash,
            risk_level=request.risk_level,
            policy_hash=policy_hash,
            intent_hash=intent_hash,
            challenge_id=challenge.challenge_id,
            challenge_hash=sha256_prefixed(challenge.challenge_id),
            expected_lnurl_key_hash=_expected_lnurl_key_hash(self.principal_service.find_by_principal_hash(request.principal_hash)),
            auth_domain=principal.auth_domain,
            issued_at=now,
            expires_at=expires_at,
            metadata_hash=sha256_prefixed(canonical_json(dict(request.intent_metadata))),
        )
        self.repository.create(record)
        audit_hash = self._audit("lnurl_step_up_challenge_created", record, reason_code="challenge_issued")
        self.repository.update(replace(record, audit_event_hash=audit_hash))
        self._metric("lnurl_step_up_requests_total", action=action.value, decision="challenge_issued", risk_level=request.risk_level, reason_code="ok")
        return LNURLAuthStepUpChallengeResponse(
            step_up_id=step_up_id,
            status=LNURLStepUpStatus.CHALLENGE_ISSUED,
            lnurl=challenge.lnurl,
            encoded_lnurl=challenge.qr_payload,
            challenge_id=challenge.challenge_id,
            action=action,
            intent_summary=_intent_summary(intent),
            intent_hash=intent_hash,
            policy_hash=policy_hash,
            expires_at=expires_at,
            required_additional_factors=(),
            policy_decision="challenge_issued",
            limitations=("lnurl_auth_step_up_is_not_standalone_authorization",),
        )

    async def complete_step_up(self, request: LNURLAuthStepUpCompleteRequest) -> LNURLAuthStepUpResult:
        record = self._get(request.step_up_id)
        if record.status is LNURLStepUpStatus.APPROVED:
            return self._approved_result(record, authorization_reference=None, reason_code="idempotent_approved")
        if record.status in {LNURLStepUpStatus.CONSUMED, LNURLStepUpStatus.REVOKED}:
            raise LNURLAuthStepUpConsumedError(LNURLStepUpFailureReason.ALREADY_CONSUMED.value)
        now = self.clock()
        if record.expires_at <= now:
            expired = self.repository.transition(record.step_up_id, expected={record.status}, target=LNURLStepUpStatus.EXPIRED, failure_reason=LNURLStepUpFailureReason.EXPIRED.value)
            self._audit("lnurl_step_up_expired", expired, reason_code=LNURLStepUpFailureReason.EXPIRED.value)
            raise LNURLAuthStepUpExpiredError(LNURLStepUpFailureReason.EXPIRED.value)
        self._validate_completion(record, request)
        session = await self.session_resolver.resolve(request.session_reference)
        self._validate_session_binding(record, session)
        self._check_revocations(principal_hash=record.principal_hash, device_key_fingerprint=record.device_key_fingerprint, session_fingerprint=record.session_fingerprint, extra=(record.challenge_hash, record.resource_hash))
        proofed = self.repository.transition(record.step_up_id, expected={LNURLStepUpStatus.CHALLENGE_ISSUED, LNURLStepUpStatus.PROOF_VERIFIED}, target=LNURLStepUpStatus.PROOF_VERIFIED)
        self._audit("lnurl_step_up_proof_verified", proofed, reason_code="proof_verified")
        entitlement = await self.entitlement_resolver.get_entitlement_for_principal(record.principal_hash)
        policy_context = self._policy_context(record=proofed, proof=request.verified_callback, session=session, entitlement=entitlement)
        decision = await self.policy_engine.decide_lnurl_step_up(policy_context)
        if not decision.allowed:
            denied = self.repository.transition(record.step_up_id, expected={LNURLStepUpStatus.PROOF_VERIFIED}, target=LNURLStepUpStatus.DENIED, policy_decision_hash=decision.decision_hash, failure_reason=decision.reason_code)
            event = "lnurl_step_up_policy_denied"
            self._audit(event, denied, reason_code=decision.reason_code)
            factors = _required_factors(decision.decision)
            self._metric("lnurl_step_up_denied_total", action=record.action.value, decision=decision.decision, risk_level=record.risk_level, reason_code=decision.reason_code)
            return LNURLAuthStepUpResult(denied.step_up_id, denied.status, None, decision.decision, factors, decision.reason_code, denied.audit_event_hash, (decision.reason_code,))
        ref = _authorization_reference()
        auth_hash = hmac_sha256_prefixed(self.config.authorization_reference_pepper, ref)
        approved_at = self.clock()
        approved = self.repository.transition(
            record.step_up_id,
            expected={LNURLStepUpStatus.PROOF_VERIFIED},
            target=LNURLStepUpStatus.APPROVED,
            approved_scopes=tuple(sorted(set(record.requested_scopes).intersection(set(entitlement.allowed_scopes if "*" not in entitlement.allowed_scopes else record.requested_scopes)))) or record.requested_scopes,
            authorization_hash=auth_hash,
            authorization_reference_hash=sha256_prefixed(ref),
            approved_at=approved_at,
            policy_decision_hash=decision.decision_hash,
        )
        audit_hash = self._audit("lnurl_step_up_approved", approved, reason_code="approved")
        approved = self.repository.update(replace(approved, audit_event_hash=audit_hash))
        self._metric("lnurl_step_up_approved_total", action=record.action.value, decision=decision.decision, risk_level=record.risk_level, reason_code="approved")
        return self._approved_result(approved, authorization_reference=ref, reason_code="approved")

    def consume_authorization(self, *, authorization_reference: str, step_up_id: str, session_fingerprint: str, action: LNURLStepUpCriticalAction | str, resource_hash: str, scopes: Sequence[str]) -> LNURLStepUpAuthorization:
        record = self._get(step_up_id)
        if record.status is not LNURLStepUpStatus.APPROVED:
            if record.status is LNURLStepUpStatus.CONSUMED:
                raise LNURLAuthStepUpConsumedError(LNURLStepUpFailureReason.ALREADY_CONSUMED.value)
            raise LNURLAuthStepUpError("lnurl_step_up_not_approved")
        if record.expires_at <= self.clock():
            self.repository.transition(step_up_id, expected={LNURLStepUpStatus.APPROVED}, target=LNURLStepUpStatus.EXPIRED, failure_reason=LNURLStepUpFailureReason.EXPIRED.value)
            raise LNURLAuthStepUpExpiredError(LNURLStepUpFailureReason.EXPIRED.value)
        if hmac_sha256_prefixed(self.config.authorization_reference_pepper, authorization_reference) != record.authorization_hash:
            raise LNURLAuthStepUpConsumedError(LNURLStepUpFailureReason.ALREADY_CONSUMED.value)
        if record.session_fingerprint != session_fingerprint:
            raise LNURLAuthStepUpMismatchError(LNURLStepUpFailureReason.SESSION_MISMATCH.value)
        if record.action is not _normalize_action(action):
            raise LNURLAuthStepUpMismatchError(LNURLStepUpFailureReason.INVALID_ACTION.value)
        if record.resource_hash != resource_hash:
            raise LNURLAuthStepUpMismatchError(LNURLStepUpFailureReason.RESOURCE_TAMPERING.value)
        if not set(scopes).issubset(set(record.approved_scopes)):
            raise LNURLAuthStepUpMismatchError(LNURLStepUpFailureReason.SCOPE_TAMPERING.value)
        consumed = self.repository.transition(step_up_id, expected={LNURLStepUpStatus.APPROVED}, target=LNURLStepUpStatus.CONSUMED, consumed_at=self.clock())
        self._audit("lnurl_step_up_consumed", consumed, reason_code="consumed")
        return _authorization(consumed, authorization_reference=None)

    def revoke_step_up(self, *, step_up_id: str, reason_code: str) -> LNURLAuthStepUpRecord:
        record = self._get(step_up_id)
        if record.status in {LNURLStepUpStatus.CONSUMED, LNURLStepUpStatus.REVOKED}:
            return record
        revoked = self.repository.transition(step_up_id, expected={record.status}, target=LNURLStepUpStatus.REVOKED, revoked_at=self.clock(), failure_reason=reason_code)
        self._audit("lnurl_step_up_revoked", revoked, reason_code=reason_code)
        return revoked

    def expire_stale(self) -> int:
        now = self.clock()
        count = 0
        for record in self.repository.records():
            if record.status in {LNURLStepUpStatus.CHALLENGE_ISSUED, LNURLStepUpStatus.PROOF_VERIFIED, LNURLStepUpStatus.APPROVED} and record.expires_at <= now:
                expired = self.repository.transition(record.step_up_id, expected={record.status}, target=LNURLStepUpStatus.EXPIRED, failure_reason=LNURLStepUpFailureReason.EXPIRED.value)
                self._audit("lnurl_step_up_expired", expired, reason_code=LNURLStepUpFailureReason.EXPIRED.value)
                count += 1
        return count

    def _validate_session(self, request: LNURLAuthStepUpRequest, session: ActivePoPSessionContext) -> None:
        if session.status != "active" or session.expires_at <= self.clock() or session.locked_down:
            raise LNURLAuthStepUpSessionError(LNURLStepUpFailureReason.SESSION_REQUIRED.value)
        if session.principal_hash != request.principal_hash:
            raise LNURLAuthStepUpMismatchError(LNURLStepUpFailureReason.PRINCIPAL_MISMATCH.value)
        if session.device_key_fingerprint != request.device_key_fingerprint:
            raise LNURLAuthStepUpMismatchError(LNURLStepUpFailureReason.DEVICE_MISMATCH.value)

    def _validate_session_binding(self, record: LNURLAuthStepUpRecord, session: ActivePoPSessionContext) -> None:
        if session.status != "active" or session.expires_at <= self.clock() or session.locked_down:
            raise LNURLAuthStepUpSessionError(LNURLStepUpFailureReason.SESSION_REQUIRED.value)
        if session.session_fingerprint != record.session_fingerprint:
            raise LNURLAuthStepUpMismatchError(LNURLStepUpFailureReason.SESSION_MISMATCH.value)
        if session.principal_hash != record.principal_hash:
            raise LNURLAuthStepUpMismatchError(LNURLStepUpFailureReason.PRINCIPAL_MISMATCH.value)
        if session.device_key_fingerprint != record.device_key_fingerprint:
            raise LNURLAuthStepUpMismatchError(LNURLStepUpFailureReason.DEVICE_MISMATCH.value)

    def _validate_device(self, action: LNURLStepUpCriticalAction, device: ActiveDeviceContext, request: LNURLAuthStepUpRequest) -> None:
        if device.status is not WalletDeviceStatus.ACTIVE:
            raise LNURLAuthStepUpMismatchError(LNURLStepUpFailureReason.DEVICE_MISMATCH.value)
        if device.device_key_fingerprint != request.device_key_fingerprint:
            raise LNURLAuthStepUpMismatchError(LNURLStepUpFailureReason.DEVICE_MISMATCH.value)
        if action in {LNURLStepUpCriticalAction.PAYOUT_APPROVE, LNURLStepUpCriticalAction.TREASURY_POLICY_CHANGE, LNURLStepUpCriticalAction.ENTERPRISE_POLICY_CHANGE} and not is_root_of_trust_device_class(device.device_class):
            raise LNURLAuthStepUpPolicyError(LNURLStepUpFailureReason.ADDITIONAL_FACTOR_REQUIRED.value)

    def _validate_completion(self, record: LNURLAuthStepUpRecord, request: LNURLAuthStepUpCompleteRequest) -> None:
        proof = request.verified_callback
        if not proof.verified or not proof.consumed or proof.replay_status not in {"consumed", "fresh", "ok"}:
            raise LNURLAuthStepUpProofError(LNURLStepUpFailureReason.PROOF_INVALID.value)
        if proof.action is not LNURLAuthAction.AUTH:
            raise LNURLAuthStepUpProofError(LNURLStepUpFailureReason.PROOF_INVALID.value)
        if proof.challenge_id != record.challenge_id or proof.auth_domain != record.auth_domain:
            raise LNURLAuthStepUpMismatchError(LNURLStepUpFailureReason.SESSION_MISMATCH.value)
        if proof.linking_key_hash != record.expected_lnurl_key_hash:
            raise LNURLAuthStepUpMismatchError(LNURLStepUpFailureReason.PRINCIPAL_MISMATCH.value)
        if proof.device_key_fingerprint and proof.device_key_fingerprint != record.device_key_fingerprint:
            raise LNURLAuthStepUpMismatchError(LNURLStepUpFailureReason.DEVICE_MISMATCH.value)
        if request.policy_hash != record.policy_hash:
            raise LNURLAuthStepUpMismatchError(LNURLStepUpFailureReason.POLICY_TAMPERING.value)
        if request.intent_hash != record.intent_hash:
            raise LNURLAuthStepUpMismatchError(LNURLStepUpFailureReason.POLICY_TAMPERING.value)
        if request.resource_hash != record.resource_hash:
            raise LNURLAuthStepUpMismatchError(LNURLStepUpFailureReason.RESOURCE_TAMPERING.value)
        if tuple(sorted(request.requested_scopes)) != tuple(sorted(record.requested_scopes)):
            raise LNURLAuthStepUpMismatchError(LNURLStepUpFailureReason.SCOPE_TAMPERING.value)
        if proof.verification_strength is not WalletVerificationStrength.STANDARD:
            raise LNURLAuthStepUpProofError(LNURLStepUpFailureReason.PROOF_INVALID.value)

    def _build_intent(self, *, request: LNURLAuthStepUpRequest, action: LNURLStepUpCriticalAction, session: ActivePoPSessionContext, policy_hash: str, challenge: LNURLAuthChallengeResult, issued_at: datetime, expires_at: datetime) -> LNURLAuthStepUpIntent:
        details = _intent_details(action, request.intent_metadata)
        return LNURLAuthStepUpIntent(
            type=STEP_UP_INTENT_TYPE,
            version=STEP_UP_INTENT_VERSION,
            domain=self.config.auth_domain,
            lnurl_action=LNURLAuthAction.AUTH.value,
            internal_action=action.value,
            purpose="critical_action_step_up",
            principal_pseudonym=request.principal_hash,
            device_key_fingerprint=request.device_key_fingerprint,
            session_fingerprint=session.session_fingerprint,
            requested_scopes=tuple(sorted(request.requested_scopes)),
            resource_type=request.resource_type,
            resource_hash=request.resource_hash,
            risk_level=request.risk_level,
            policy_hash=policy_hash,
            challenge_id=challenge.challenge_id,
            k1_commitment=sha256_prefixed(challenge.challenge_id),
            issued_at=issued_at,
            expires_at=expires_at,
            cannot_access=_cannot_access(action),
            human_readable_warning=STEP_UP_WARNING,
            details=details,
        )

    def _policy_hash(self, request: LNURLAuthStepUpRequest, session: ActivePoPSessionContext, entitlement: EntitlementSnapshot, action: LNURLStepUpCriticalAction) -> str:
        return sha256_prefixed(canonical_json({"type": STEP_UP_INTENT_TYPE, "action": action.value, "principal_hash": request.principal_hash, "device_key_fingerprint": request.device_key_fingerprint, "session_fingerprint": session.session_fingerprint, "resource_type": request.resource_type, "resource_hash": request.resource_hash, "requested_scopes": tuple(sorted(request.requested_scopes)), "risk_level": request.risk_level, "plan": entitlement.effective_plan, "metadata_hash": sha256_prefixed(canonical_json(dict(request.intent_metadata)))}))

    def _policy_context(self, *, record: LNURLAuthStepUpRecord, proof: VerifiedLNURLAuthSessionInput, session: ActivePoPSessionContext, entitlement: EntitlementSnapshot) -> Mapping[str, object]:
        return {
            "actor_type": "lightning_wallet_principal",
            "auth_method": "lnurl_auth",
            "auth_action": LNURLAuthAction.AUTH.value,
            "internal_action": record.action.value,
            "principal_hash": record.principal_hash,
            "device_key_fingerprint": record.device_key_fingerprint,
            "session_fingerprint": record.session_fingerprint,
            "verification_strength": proof.verification_strength.value,
            "wallet_proof_freshness_seconds": int((self.clock() - proof.verified_at).total_seconds()),
            "requested_scopes": record.requested_scopes,
            "resource_type": record.resource_type,
            "resource_hash": record.resource_hash,
            "subscription_plan": entitlement.effective_plan,
            "subscription_status": "active" if entitlement.active else "inactive",
            "risk_level": record.risk_level,
            "recovery_state": session.recovery_state,
            "revocation_state": "checked",
            "policy_hash": record.policy_hash,
            "intent_hash": record.intent_hash,
        }

    def _ttl_for(self, action: LNURLStepUpCriticalAction, request: LNURLAuthStepUpRequest) -> int:
        base = self.config.critical_ttl_seconds if action in {LNURLStepUpCriticalAction.PAYOUT_APPROVE, LNURLStepUpCriticalAction.REFUND_APPROVE, LNURLStepUpCriticalAction.RECOVERY_COMPLETE, LNURLStepUpCriticalAction.OFFLINE_PACK_ISSUE} else self.config.default_ttl_seconds
        if request.requested_ttl_seconds is not None:
            base = min(base, request.requested_ttl_seconds)
        return max(30, min(base, DEFAULT_STEP_UP_TTL_SECONDS))

    def _check_revocations(self, *, principal_hash: str, device_key_fingerprint: str, session_fingerprint: str, extra: Sequence[str] = ()) -> None:
        if self.revocation_checker is None:
            return
        checks = [("lightning_wallet_principal", principal_hash), ("wallet_device", device_key_fingerprint), ("wallet_session", session_fingerprint)]
        checks.extend(("lnurl_step_up_parent", value) for value in extra)
        for target_type, target_hash in checks:
            if self.revocation_checker.is_revoked(target_type=target_type, target_hash=target_hash):
                raise LNURLAuthStepUpRevokedError(LNURLStepUpFailureReason.REVOKED.value)

    def _approved_result(self, record: LNURLAuthStepUpRecord, *, authorization_reference: str | None, reason_code: str) -> LNURLAuthStepUpResult:
        return LNURLAuthStepUpResult(
            step_up_id=record.step_up_id,
            status=record.status,
            authorization=_authorization(record, authorization_reference=authorization_reference) if record.status is LNURLStepUpStatus.APPROVED else None,
            policy_decision="allow",
            required_additional_factors=(),
            reason_code=reason_code,
            audit_event_hash=record.audit_event_hash,
            limitations=("single_use" if record.action in _SINGLE_USE_ACTIONS else "action_bound",),
        )

    def _get(self, step_up_id: str) -> LNURLAuthStepUpRecord:
        record = self.repository.get(step_up_id)
        if record is None:
            raise LNURLAuthStepUpError("lnurl_step_up_not_found")
        return record

    def _audit(self, event: str, record: LNURLAuthStepUpRecord, *, reason_code: str) -> str:
        payload: dict[str, object] = {
            "step_up_id": record.step_up_id,
            "principal_hash": record.principal_hash,
            "device_key_fingerprint": record.device_key_fingerprint,
            "session_fingerprint": record.session_fingerprint,
            "action": record.action.value,
            "risk_level": record.risk_level,
            "policy_hash": record.policy_hash,
            "intent_hash": record.intent_hash,
            "resource_hash": record.resource_hash,
            "status": record.status.value,
            "reason_code": reason_code,
            "timestamp": self.clock().isoformat(),
        }
        audit_hash = sha256_prefixed(canonical_json(payload))
        payload["audit_event_hash"] = audit_hash
        if self.audit_emitter:
            self.audit_emitter(event, payload)
        return audit_hash

    def _metric(self, name: str, *, action: str, decision: str, risk_level: str, reason_code: str) -> None:
        if self.metrics_emitter:
            self.metrics_emitter(name, {"action": action, "decision": decision, "risk_level": risk_level, "verification_strength": "standard", "reason_code": reason_code})


def _normalize_action(action: LNURLStepUpCriticalAction | str) -> LNURLStepUpCriticalAction:
    try:
        return LNURLStepUpCriticalAction(action)
    except ValueError as exc:
        raise LNURLAuthStepUpInvalidActionError(LNURLStepUpFailureReason.INVALID_ACTION.value) from exc


def _validate_request(request: LNURLAuthStepUpRequest, action: LNURLStepUpCriticalAction) -> None:
    for field_name in ("principal_hash", "device_key_fingerprint", "resource_hash"):
        value = getattr(request, field_name)
        reject_forbidden_wallet_secret_input(value, field_name)
        if field_name != "device_key_fingerprint" and not (value.startswith("sha256:") or value.startswith("hmac-sha256:")):
            raise LNURLAuthStepUpMismatchError(LNURLStepUpFailureReason.PROOF_INVALID.value)
    if not request.device_key_fingerprint.startswith("sha256:"):
        raise LNURLAuthStepUpMismatchError(LNURLStepUpFailureReason.DEVICE_MISMATCH.value)
    allowed = _SCOPE_VOCABULARY[action]
    if not request.requested_scopes or not set(request.requested_scopes).issubset(allowed):
        raise LNURLAuthStepUpPolicyError(LNURLStepUpFailureReason.SCOPE_TAMPERING.value)
    if any(scope == "*" or scope.endswith(":all") or "*" in scope for scope in request.requested_scopes):
        raise LNURLAuthStepUpPolicyError(LNURLStepUpFailureReason.SCOPE_TAMPERING.value)
    for key, value in request.intent_metadata.items():
        reject_forbidden_wallet_secret_input(str(key), "intent_metadata_key")
        if isinstance(value, str):
            reject_forbidden_wallet_secret_input(value, str(key))


def _expected_lnurl_key_hash(principal: object) -> str:
    value = getattr(principal, "lnurl_key_hash", None)
    if value is None:
        value = getattr(principal, "principal_hash")
    return str(value)


def _hash_intent(intent: LNURLAuthStepUpIntent) -> str:
    return sha256_prefixed(canonical_json({
        "type": intent.type,
        "version": intent.version,
        "domain": intent.domain,
        "lnurl_action": intent.lnurl_action,
        "internal_action": intent.internal_action,
        "principal_pseudonym": intent.principal_pseudonym,
        "device_key_fingerprint": intent.device_key_fingerprint,
        "session_fingerprint": intent.session_fingerprint,
        "requested_scopes": intent.requested_scopes,
        "resource_type": intent.resource_type,
        "resource_hash": intent.resource_hash,
        "risk_level": intent.risk_level,
        "policy_hash": intent.policy_hash,
        "challenge_id": intent.challenge_id,
        "k1_commitment": intent.k1_commitment,
        "cannot_access": intent.cannot_access,
        "details": dict(intent.details),
        "warning": intent.human_readable_warning,
    }))


def _step_up_id(intent_hash: str) -> str:
    return "lsu_" + intent_hash.split(":", 1)[1][:32]


def _authorization_reference() -> str:
    return "lsuar_" + secrets.token_urlsafe(32)


def _authorization(record: LNURLAuthStepUpRecord, *, authorization_reference: str | None) -> LNURLStepUpAuthorization:
    return LNURLStepUpAuthorization(
        step_up_id=record.step_up_id,
        principal_hash=record.principal_hash,
        device_key_fingerprint=record.device_key_fingerprint,
        session_fingerprint=record.session_fingerprint,
        action=record.action,
        intent_hash=record.intent_hash,
        policy_hash=record.policy_hash,
        approved_scopes=record.approved_scopes,
        resource_hash=record.resource_hash,
        verification_method="lnurl_auth",
        verification_strength=WalletVerificationStrength.STANDARD,
        approved_at=record.approved_at or datetime.now(UTC),
        expires_at=record.expires_at,
        status=record.status,
        audit_event_hash=record.audit_event_hash,
        authorization_reference=authorization_reference,
    )


def _intent_summary(intent: LNURLAuthStepUpIntent) -> Mapping[str, object]:
    return {"action": intent.internal_action, "resource_type": intent.resource_type, "resource_hash": intent.resource_hash, "requested_scopes": intent.requested_scopes, "warning": intent.human_readable_warning}


def _metadata_tuple(metadata: Mapping[str, object], key: str, default: tuple[str, ...] = ()) -> tuple[str, ...]:
    value = metadata.get(key, default)
    if isinstance(value, tuple):
        return tuple(str(item) for item in value)
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    return default


def _intent_details(action: LNURLStepUpCriticalAction, metadata: Mapping[str, object]) -> Mapping[str, object]:
    if action in {LNURLStepUpCriticalAction.PAYOUT_APPROVE, LNURLStepUpCriticalAction.REFUND_APPROVE}:
        return {"amount_msat": metadata.get("amount_msat"), "reference": metadata.get("reference_hash"), "destination_handling": "destination must match approved payout/refund service record", "maximum_authorized_amount": metadata.get("maximum_authorized_amount_msat", metadata.get("amount_msat"))}
    if action is LNURLStepUpCriticalAction.CREATE_API_KEY:
        return {"new_key_scopes": _metadata_tuple(metadata, "new_key_scopes"), "key_expiry": metadata.get("key_expiry"), "delegation_allowed": bool(metadata.get("delegation_allowed", False)), "cannot_access": _metadata_tuple(metadata, "cannot_access", ("treasury", "recovery"))}
    if action is LNURLStepUpCriticalAction.DEVICE_ADD:
        return {"new_device_class": metadata.get("new_device_class"), "new_device_fingerprint": metadata.get("new_device_fingerprint"), "requested_trust_level": metadata.get("requested_trust_level", "standard")}
    if action is LNURLStepUpCriticalAction.BUSINESS_ROLE_ASSIGNMENT:
        return {"workspace_pseudonym": metadata.get("workspace_pseudonym"), "target_role": metadata.get("target_role"), "previous_role": metadata.get("previous_role"), "resulting_permissions": _metadata_tuple(metadata, "resulting_permissions")}
    return {"metadata_hash": sha256_prefixed(canonical_json(dict(metadata)))}


def _cannot_access(action: LNURLStepUpCriticalAction) -> tuple[str, ...]:
    if action is LNURLStepUpCriticalAction.CREATE_API_KEY:
        return ("wallet_seed", "private_key", "recovery_material", "treasury_without_separate_policy")
    return ("bitcoin_transaction_signing", "wallet_private_keys", "unrelated_actions")


def _required_factors(decision: str) -> tuple[str, ...]:
    mapping = {
        "additional_factor_required": ("additional_factor_required",),
        "quorum_required": ("quorum_required",),
        "access_certificate_required": ("access_certificate_required",),
        "recovery_required": ("recovery_required",),
    }
    return mapping.get(decision, ())


def _recovery_or_lockdown_action(action: LNURLStepUpCriticalAction) -> bool:
    return action in {LNURLStepUpCriticalAction.RECOVERY_CHANGE, LNURLStepUpCriticalAction.RECOVERY_COMPLETE, LNURLStepUpCriticalAction.LOCKDOWN_RELEASE}


__all__ = [
    "ActiveDeviceContext",
    "ActivePoPSessionContext",
    "LNURLAuthStepUpChallengeResponse",
    "LNURLAuthStepUpCompleteRequest",
    "LNURLAuthStepUpConfig",
    "LNURLAuthStepUpError",
    "LNURLAuthStepUpRepository",
    "LNURLAuthStepUpRequest",
    "LNURLAuthStepUpResult",
    "LNURLAuthStepUpService",
    "LNURLStepUpAuthorization",
    "LNURLStepUpCriticalAction",
    "LNURLStepUpStatus",
]
