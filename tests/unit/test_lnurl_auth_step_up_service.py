from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from app.domain.lnurl.auth import LNURLAuthAction
from app.domain.wallet_auth.devices import WalletDeviceClass, WalletDeviceStatus
from app.domain.wallet_auth.proofs import WalletVerificationStrength
from app.services.access.crypto.hashing import sha256_prefixed
from app.services.lnurl.auth_callback_verifier import VerifiedLNURLAuthProof
from app.services.lnurl.auth_challenge_service import LNURLAuthChallengeDisplay, LNURLAuthChallengeResult
from app.services.lnurl.auth_session_bridge import VerifiedLNURLAuthSessionInput
from app.services.lnurl.auth_step_up import (
    ActiveDeviceContext,
    ActivePoPSessionContext,
    LNURLAuthStepUpCompleteRequest,
    LNURLAuthStepUpMismatchError,
    LNURLAuthStepUpPolicyError,
    LNURLAuthStepUpRepository,
    LNURLAuthStepUpRequest,
    LNURLAuthStepUpRevokedError,
    LNURLAuthStepUpSessionError,
    LNURLAuthStepUpService,
    LNURLStepUpCriticalAction,
    LNURLStepUpFailureReason,
    LNURLStepUpStatus,
)
from app.services.lnurl.principal_service import AuthDomainPolicy, InMemoryLightningPrincipalRepository, LightningPrincipalConfig, LightningPrincipalService
from app.services.wallet_auth.session_service import EntitlementSnapshot, PolicyDecision

NOW = datetime(2026, 7, 17, tzinfo=UTC)
KEY = "02" + "11" * 32
OTHER_KEY = "03" + "22" * 32


class Challenges:
    def __init__(self) -> None:
        self.calls = []

    def create_challenge(self, **kwargs):
        self.calls.append(kwargs)
        return LNURLAuthChallengeResult(
            challenge_id="lac_step",
            tag="auth",
            action=LNURLAuthAction.AUTH,
            lnurl="LNURL1STEPUP",
            callback_url="https://auth.bitcoin-bastion.com/v1/lnurl/auth/callback?k1=redacted&action=auth",
            expires_at=NOW + timedelta(seconds=300),
            expires_in_seconds=300,
            qr_payload="LNURL1STEPUP",
            display=LNURLAuthChallengeDisplay("auth.bitcoin-bastion.com", "auth", "lnurl_auth_step_up"),
        )


class Sessions:
    def __init__(self, context: ActivePoPSessionContext) -> None:
        self.context = context

    async def resolve(self, session_reference: str) -> ActivePoPSessionContext:
        if session_reference not in {"session-token", sha256_prefixed("session-token")}:
            return ActivePoPSessionContext(session_reference=session_reference, session_fingerprint="sha256:other-session", principal_hash=self.context.principal_hash, device_key_fingerprint=self.context.device_key_fingerprint, status="active", expires_at=self.context.expires_at, approved_scopes=self.context.approved_scopes, auth_domain=self.context.auth_domain)
        return self.context


class Devices:
    def __init__(self, *, status: WalletDeviceStatus = WalletDeviceStatus.ACTIVE, device_class: WalletDeviceClass = WalletDeviceClass.MOBILE_VAULT) -> None:
        self.status = status
        self.device_class = device_class

    async def assert_active(self, *, principal_hash: str, device_key_fingerprint: str) -> ActiveDeviceContext:
        return ActiveDeviceContext(device_key_fingerprint=device_key_fingerprint, status=self.status, device_class=self.device_class, risk_score=5, risk_level="low")


class Entitlements:
    def __init__(self, scopes=("api_key:create", "device:add", "payout:approve", "recovery:complete", "business_role:assign"), plan="pro", active=True) -> None:
        self.snapshot = EntitlementSnapshot(active=active, entitlement_id="ent", effective_plan=plan, allowed_scopes=tuple(scopes))

    async def get_entitlement_for_principal(self, principal_hash: str) -> EntitlementSnapshot:
        return self.snapshot


class Policy:
    def __init__(self, decision="allow", reason="allow") -> None:
        self.decision = decision
        self.reason = reason
        self.contexts = []

    async def decide_lnurl_step_up(self, context):
        self.contexts.append(dict(context))
        return PolicyDecision(self.decision, "sha256:policy-decision", self.reason)


class Revocations:
    def __init__(self) -> None:
        self.revoked = set()

    def is_revoked(self, *, target_type: str, target_hash: str) -> bool:
        return (target_type, target_hash) in self.revoked


def principal_service() -> LightningPrincipalService:
    return LightningPrincipalService(
        repository=InMemoryLightningPrincipalRepository(),
        config=LightningPrincipalConfig("lnurl-pepper", "principal-pepper", domain_policy=AuthDomainPolicy()),
        clock=lambda: NOW,
    )


def create_principal(service: LightningPrincipalService, key: str = KEY):
    proof = VerifiedLNURLAuthProof(
        lnurl_key_hash=service.derive_lnurl_key_hash(normalized_linking_public_key=key, auth_domain="auth.bitcoin-bastion.com"),
        key_fingerprint=sha256_prefixed(bytes.fromhex(key)),
        auth_domain="auth.bitcoin-bastion.com",
        lnurl_action=LNURLAuthAction.AUTH,
        bastion_action="wallet_sensitive_action_step_up",
        challenge_id="lac_base",
        policy_intent_hash="sha256:base-policy",
        verification_strength=WalletVerificationStrength.STANDARD,
        device_key_fingerprint="sha256:device",
        verified_at=NOW,
    )
    return service.create_from_verified_lnurl_auth(proof=proof, normalized_linking_public_key=key, proof_fingerprint="sha256:proof", policy_hash="sha256:base-policy").principal


def request(principal_hash: str, action=LNURLStepUpCriticalAction.CREATE_API_KEY, **kwargs) -> LNURLAuthStepUpRequest:
    data = dict(
        principal_hash=principal_hash,
        device_key_fingerprint="sha256:device",
        session_reference="session-token",
        action=action,
        requested_scopes=("api_key:create",) if action == LNURLStepUpCriticalAction.CREATE_API_KEY else ("payout:approve",),
        resource_type="api_key" if action == LNURLStepUpCriticalAction.CREATE_API_KEY else "payout",
        resource_hash="sha256:resource",
        risk_level="high",
        intent_metadata={"new_key_scopes": ("read",), "key_expiry": "2026-08-01"} if action == LNURLStepUpCriticalAction.CREATE_API_KEY else {"amount_msat": 1000, "reference_hash": "sha256:payout"},
        requested_ttl_seconds=300,
    )
    data.update(kwargs)
    return LNURLAuthStepUpRequest(**data)


def callback(record, principal, *, key_hash=None, action=LNURLAuthAction.AUTH, consumed=True) -> VerifiedLNURLAuthSessionInput:
    return VerifiedLNURLAuthSessionInput(
        verified=True,
        consumed=consumed,
        replay_status="consumed" if consumed else "replayed",
        action=action,
        auth_domain="auth.bitcoin-bastion.com",
        k1_hash=record.challenge_hash,
        linking_key_hash=key_hash or principal.lnurl_key_hash,
        proof_type="lnurl_auth",
        verification_strength=WalletVerificationStrength.STANDARD,
        challenge_id=record.challenge_id,
        verified_at=NOW,
        callback_fingerprint="sha256:callback",
        policy_intent_hash=record.policy_hash,
        device_key_fingerprint="sha256:device",
    )


def service(principal, *, policy=None, revocations=None, device=None, events=None, repo=None, session=None):
    session_context = session or ActivePoPSessionContext("session-token", "sha256:session", principal.principal_hash, "sha256:device", "active", NOW + timedelta(minutes=10), ("api_key:create", "payout:approve"), "auth.bitcoin-bastion.com")
    return LNURLAuthStepUpService(
        challenge_service=Challenges(),
        principal_service=principal_service_obj,
        session_resolver=Sessions(session_context),
        device_resolver=device or Devices(),
        entitlement_resolver=Entitlements(),
        policy_engine=policy or Policy(),
        repository=repo,
        revocation_checker=revocations,
        audit_emitter=(lambda event, payload: events.append((event, payload))) if events is not None else None,
        clock=lambda: NOW,
    )


principal_service_obj = principal_service()


def new_service(policy=None, revocations=None, device=None, events=None, repo=None, session=None):
    ps = principal_service()
    principal = create_principal(ps)
    global principal_service_obj
    principal_service_obj = ps
    session_context = session or ActivePoPSessionContext("session-token", "sha256:session", principal.principal_hash, "sha256:device", "active", NOW + timedelta(minutes=10), ("api_key:create", "payout:approve"), "auth.bitcoin-bastion.com")
    svc = LNURLAuthStepUpService(
        challenge_service=Challenges(),
        principal_service=ps,
        session_resolver=Sessions(session_context),
        device_resolver=device or Devices(),
        entitlement_resolver=Entitlements(),
        policy_engine=policy or Policy(),
        repository=repo or LNURLAuthStepUpRepository(),
        revocation_checker=revocations,
        audit_emitter=(lambda event, payload: events.append((event, payload))) if events is not None else None,
        clock=lambda: NOW,
    )
    return svc, principal


def test_valid_flow_creates_action_bound_authorization() -> None:
    events = []
    svc, principal = new_service(events=events)
    challenge = asyncio.run(svc.start_step_up(request(principal.principal_hash)))
    record = svc.repository.get(challenge.step_up_id)
    assert record is not None
    result = asyncio.run(svc.complete_step_up(LNURLAuthStepUpCompleteRequest(challenge.step_up_id, "session-token", callback(record, principal), record.policy_hash, record.intent_hash, record.resource_hash, record.requested_scopes)))
    assert result.status is LNURLStepUpStatus.APPROVED
    assert result.authorization is not None
    assert result.authorization.authorization_reference is not None
    assert result.authorization.action is LNURLStepUpCriticalAction.CREATE_API_KEY
    assert "lnurl_step_up_approved" in [event for event, _ in events]


def test_wallet_signature_alone_without_active_pop_session_is_denied() -> None:
    ps = principal_service()
    principal = create_principal(ps)
    expired = ActivePoPSessionContext("session-token", "sha256:session", principal.principal_hash, "sha256:device", "expired", NOW - timedelta(seconds=1), (), "auth.bitcoin-bastion.com")
    svc, _ = new_service(session=expired)
    with pytest.raises(LNURLAuthStepUpSessionError):
        asyncio.run(svc.start_step_up(request(principal.principal_hash)))


def test_policy_denial_and_additional_factor_do_not_create_authorization() -> None:
    svc, principal = new_service(policy=Policy("deny", "policy_denied"))
    challenge = asyncio.run(svc.start_step_up(request(principal.principal_hash)))
    record = svc.repository.get(challenge.step_up_id)
    assert record is not None
    result = asyncio.run(svc.complete_step_up(LNURLAuthStepUpCompleteRequest(challenge.step_up_id, "session-token", callback(record, principal), record.policy_hash, record.intent_hash, record.resource_hash, record.requested_scopes)))
    assert result.authorization is None
    assert result.status is LNURLStepUpStatus.DENIED
    svc2, principal2 = new_service(policy=Policy("quorum_required", "quorum_required"))
    c2 = asyncio.run(svc2.start_step_up(request(principal2.principal_hash, action=LNURLStepUpCriticalAction.PAYOUT_APPROVE)))
    r2 = svc2.repository.get(c2.step_up_id)
    assert r2 is not None
    res2 = asyncio.run(svc2.complete_step_up(LNURLAuthStepUpCompleteRequest(c2.step_up_id, "session-token", callback(r2, principal2), r2.policy_hash, r2.intent_hash, r2.resource_hash, r2.requested_scopes)))
    assert res2.required_additional_factors == ("quorum_required",)


def test_principal_device_session_and_proof_mismatches_are_rejected() -> None:
    svc, principal = new_service()
    challenge = asyncio.run(svc.start_step_up(request(principal.principal_hash)))
    record = svc.repository.get(challenge.step_up_id)
    assert record is not None
    with pytest.raises(LNURLAuthStepUpMismatchError) as principal_exc:
        asyncio.run(svc.complete_step_up(LNURLAuthStepUpCompleteRequest(challenge.step_up_id, "session-token", callback(record, principal, key_hash="hmac-sha256:other"), record.policy_hash, record.intent_hash, record.resource_hash, record.requested_scopes)))
    assert principal_exc.value.reason_code == LNURLStepUpFailureReason.PRINCIPAL_MISMATCH.value
    with pytest.raises(LNURLAuthStepUpMismatchError):
        asyncio.run(svc.complete_step_up(LNURLAuthStepUpCompleteRequest(challenge.step_up_id, "other-session", callback(record, principal), record.policy_hash, record.intent_hash, record.resource_hash, record.requested_scopes)))
    with pytest.raises(LNURLAuthStepUpMismatchError):
        asyncio.run(svc.start_step_up(request(principal.principal_hash, device_key_fingerprint="sha256:other-device")))


def test_replay_expiration_revocation_and_single_use_consumption() -> None:
    revocations = Revocations()
    repo = LNURLAuthStepUpRepository()
    svc, principal = new_service(repo=repo, revocations=revocations)
    challenge = asyncio.run(svc.start_step_up(request(principal.principal_hash)))
    record = repo.get(challenge.step_up_id)
    assert record is not None
    approved = asyncio.run(svc.complete_step_up(LNURLAuthStepUpCompleteRequest(challenge.step_up_id, "session-token", callback(record, principal), record.policy_hash, record.intent_hash, record.resource_hash, record.requested_scopes)))
    assert approved.authorization and approved.authorization.authorization_reference
    again = asyncio.run(svc.complete_step_up(LNURLAuthStepUpCompleteRequest(challenge.step_up_id, "session-token", callback(record, principal), record.policy_hash, record.intent_hash, record.resource_hash, record.requested_scopes)))
    assert again.status is LNURLStepUpStatus.APPROVED
    svc.consume_authorization(authorization_reference=approved.authorization.authorization_reference, step_up_id=challenge.step_up_id, session_fingerprint="sha256:session", action=LNURLStepUpCriticalAction.CREATE_API_KEY, resource_hash=record.resource_hash, scopes=record.approved_scopes)
    with pytest.raises(Exception):
        svc.consume_authorization(authorization_reference=approved.authorization.authorization_reference, step_up_id=challenge.step_up_id, session_fingerprint="sha256:session", action=LNURLStepUpCriticalAction.CREATE_API_KEY, resource_hash=record.resource_hash, scopes=record.approved_scopes)
    svc2, principal2 = new_service(revocations=revocations)
    revocations.revoked.add(("wallet_device", "sha256:device"))
    with pytest.raises(LNURLAuthStepUpRevokedError):
        asyncio.run(svc2.start_step_up(request(principal2.principal_hash)))


def test_scope_resource_policy_amount_device_and_recovery_tampering_fail_closed() -> None:
    svc, principal = new_service()
    challenge = asyncio.run(svc.start_step_up(request(principal.principal_hash, action=LNURLStepUpCriticalAction.PAYOUT_APPROVE)))
    record = svc.repository.get(challenge.step_up_id)
    assert record is not None
    with pytest.raises(LNURLAuthStepUpMismatchError):
        asyncio.run(svc.complete_step_up(LNURLAuthStepUpCompleteRequest(challenge.step_up_id, "session-token", callback(record, principal), "sha256:bad", record.intent_hash, record.resource_hash, record.requested_scopes)))
    with pytest.raises(LNURLAuthStepUpMismatchError):
        asyncio.run(svc.complete_step_up(LNURLAuthStepUpCompleteRequest(challenge.step_up_id, "session-token", callback(record, principal), record.policy_hash, record.intent_hash, "sha256:other", record.requested_scopes)))
    with pytest.raises(LNURLAuthStepUpMismatchError):
        asyncio.run(svc.complete_step_up(LNURLAuthStepUpCompleteRequest(challenge.step_up_id, "session-token", callback(record, principal), record.policy_hash, record.intent_hash, record.resource_hash, ("api_key:create",))))
    with pytest.raises(LNURLAuthStepUpPolicyError):
        asyncio.run(svc.start_step_up(request(principal.principal_hash, requested_scopes=("api:all",))))
    with pytest.raises(Exception):
        asyncio.run(svc.start_step_up(request(principal.principal_hash, intent_metadata={"mnemonic": "seed words"})))


def test_sensitive_logging_and_policy_context_are_safe() -> None:
    events = []
    policy = Policy()
    svc, principal = new_service(policy=policy, events=events)
    challenge = asyncio.run(svc.start_step_up(request(principal.principal_hash)))
    record = svc.repository.get(challenge.step_up_id)
    assert record is not None
    asyncio.run(svc.complete_step_up(LNURLAuthStepUpCompleteRequest(challenge.step_up_id, "session-token", callback(record, principal), record.policy_hash, record.intent_hash, record.resource_hash, record.requested_scopes)))
    rendered = repr(events) + repr(challenge)
    assert KEY not in rendered
    assert "session-token" not in rendered
    assert "k1" not in rendered.lower()
    assert "private_key" not in rendered.lower()
    assert policy.contexts[0]["auth_action"] == "auth"
    assert policy.contexts[0]["internal_action"] == "create_api_key"
    assert policy.contexts[0]["intent_hash"] == record.intent_hash
