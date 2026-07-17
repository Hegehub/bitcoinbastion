from __future__ import annotations

from datetime import UTC, datetime, timedelta

import asyncio

import pytest

from app.domain.lnurl.auth import LNURLAuthAction
from app.domain.wallet_auth.devices import WalletDeviceClass, WalletDeviceStatus
from app.domain.wallet_auth.proofs import WalletVerificationStrength
from app.domain.wallet_auth.sessions import WalletSessionStatus
from app.services.access.crypto.hashing import sha256_prefixed
from app.services.lnurl.auth_callback_verifier import VerifiedLNURLAuthProof
from app.services.lnurl.auth_session_bridge import (
    DeviceBindingBridgeResult,
    LNURLAuthSessionBridge,
    LNURLAuthSessionBridgeReason,
    LNURLAuthSessionBridgeRequest,
    LNURLAuthSessionBridgeStatus,
    LNURLAuthSessionDeviceError,
    LNURLAuthSessionInvalidCallbackError,
    LNURLAuthSessionPolicyError,
    VerifiedLNURLAuthSessionInput,
)
from app.services.lnurl.principal_service import AuthDomainPolicy, InMemoryLightningPrincipalRepository, LightningPrincipalConfig, LightningPrincipalService
from app.services.wallet_auth.session_service import EntitlementSnapshot, PolicyDecision, WalletSessionContext, WalletSessionCreationResult

KEY = "02" + "11" * 32
OTHER_KEY = "03" + "22" * 32
NOW = datetime(2026, 7, 15, tzinfo=UTC)


class DeviceBridge:
    def __init__(self) -> None:
        self.bound: set[tuple[str, str]] = set()
        self.revoked: set[str] = set()
        self.calls = 0

    async def verify_or_bind_device(self, *, principal, request, proof, allow_new_device: bool) -> DeviceBindingBridgeResult:
        self.calls += 1
        if request.device_binding_signature != "sig:valid":
            raise LNURLAuthSessionDeviceError(LNURLAuthSessionBridgeReason.DEVICE_PROOF_INVALID.value)
        if request.device_key_fingerprint in self.revoked:
            raise LNURLAuthSessionDeviceError(LNURLAuthSessionBridgeReason.DEVICE_REVOKED.value)
        key = (principal.principal_hash, request.device_key_fingerprint)
        created = key not in self.bound
        if created and not allow_new_device:
            raise LNURLAuthSessionDeviceError(LNURLAuthSessionBridgeReason.DEVICE_PROOF_INVALID.value)
        self.bound.add(key)
        return DeviceBindingBridgeResult(
            device_binding_id=1,
            device_key_fingerprint=request.device_key_fingerprint,
            status=WalletDeviceStatus.ACTIVE,
            device_class=request.device_class,
            risk_score=10,
            risk_level="low",
            created=created,
        )


class Entitlements:
    def __init__(self, *, active: bool = True, plan: str = "lite", scopes: tuple[str, ...] = ("read",), expires_at=None) -> None:
        self.snapshot = EntitlementSnapshot(active=active, entitlement_id="ent_1" if active else None, effective_plan=plan, allowed_scopes=scopes, expires_at=expires_at)

    async def get_entitlement_for_principal(self, principal_hash: str) -> EntitlementSnapshot:
        return self.snapshot


class Policy:
    def __init__(self, decision: str = "allow") -> None:
        self.decision = decision
        self.inputs: list[dict[str, object]] = []

    async def decide_lnurl_auth_session(self, context):
        self.inputs.append(dict(context))
        return PolicyDecision(decision=self.decision, decision_hash="sha256:policy-decision", reason_code=self.decision)


class PopSessions:
    def __init__(self) -> None:
        self.created: list[object] = []

    async def create_session(self, *, auth_context, session_public_key, requested_ttl_seconds=None) -> WalletSessionCreationResult:
        self.created.append(auth_context)
        expires = NOW + timedelta(seconds=requested_ttl_seconds or 900)
        context = WalletSessionContext(
            session_lookup_hash="hmac-sha256:session",
            principal_hash=auth_context.principal_hash,
            principal_type=auth_context.principal_type,
            device_binding_id=auth_context.device_binding_id,
            device_key_fingerprint=auth_context.device_key_fingerprint,
            session_public_key_b64="c2Vzc2lvbg",
            session_public_key_fingerprint=auth_context.expected_session_public_key_fingerprint,
            auth_method="lnurl_auth",
            verification_strength=auth_context.verification_strength,
            effective_plan="lite",
            effective_scopes=auth_context.requested_scopes,
            entitlement_id="ent_1",
            policy_hash=auth_context.policy_hash,
            policy_epoch=auth_context.policy_epoch,
            crypto_epoch=auth_context.crypto_epoch,
            origin=auth_context.origin,
            risk_snapshot={},
            issued_at=NOW,
            expires_at=expires,
            session_status=WalletSessionStatus.ACTIVE,
            requires_request_signature=True,
        )
        return WalletSessionCreationResult(
            session_token="bbp_sess_secret_once",
            token_type="PoP",
            expires_at=expires,
            principal_pseudonym=auth_context.principal_hash,
            device_fingerprint=auth_context.device_key_fingerprint,
            session_public_key_fingerprint=auth_context.expected_session_public_key_fingerprint,
            effective_plan="lite",
            effective_scopes=auth_context.requested_scopes,
            policy_mode="proof_of_possession",
            requires_request_signature=True,
            request_signature_algorithm="ed25519",
            server_time=NOW,
            warning="PoP required",
            context=context,
        )


class Revocations:
    def __init__(self) -> None:
        self.revoked: set[tuple[str, str]] = set()

    def is_revoked(self, *, target_type: str, target_hash: str) -> bool:
        return (target_type, target_hash) in self.revoked


def principal_service() -> LightningPrincipalService:
    return LightningPrincipalService(
        repository=InMemoryLightningPrincipalRepository(),
        config=LightningPrincipalConfig(
            lnurl_auth_server_pepper="lnurl-pepper",
            principal_server_pepper="principal-pepper",
            domain_policy=AuthDomainPolicy(merchant_custom_domains=frozenset({"merchant.example.com"})),
        ),
        clock=lambda: NOW,
    )


def proof(action: LNURLAuthAction = LNURLAuthAction.REGISTER, key: str = KEY) -> VerifiedLNURLAuthProof:
    temp = principal_service()
    return VerifiedLNURLAuthProof(
        lnurl_key_hash=temp.derive_lnurl_key_hash(normalized_linking_public_key=key, auth_domain="auth.bitcoin-bastion.com"),
        key_fingerprint=sha256_prefixed(bytes.fromhex(key)),
        auth_domain="auth.bitcoin-bastion.com",
        lnurl_action=action,
        bastion_action="wallet_principal_create" if action is LNURLAuthAction.REGISTER else "wallet_principal_authenticate",
        challenge_id="lac_123",
        policy_intent_hash="sha256:intent",
        verification_strength=WalletVerificationStrength.STANDARD,
        device_key_fingerprint="sha256:device",
        verified_at=NOW,
    )


def verified(action: LNURLAuthAction = LNURLAuthAction.REGISTER, *, consumed: bool = True, replay_status: str = "consumed") -> VerifiedLNURLAuthSessionInput:
    p = proof(action)
    return VerifiedLNURLAuthSessionInput(
        verified=True,
        consumed=consumed,
        replay_status=replay_status,
        action=action,
        auth_domain=p.auth_domain,
        k1_hash="sha256:k1",
        linking_key_hash=p.lnurl_key_hash,
        proof_type="lnurl_auth",
        verification_strength=p.verification_strength,
        challenge_id=p.challenge_id,
        verified_at=p.verified_at,
        callback_fingerprint="sha256:callback",
        policy_intent_hash=p.policy_intent_hash,
        device_key_fingerprint="sha256:device",
        proof=p,
    )


def request(action: LNURLAuthAction = LNURLAuthAction.REGISTER, **overrides) -> LNURLAuthSessionBridgeRequest:
    v = overrides.pop("verified_callback_result", verified(action))
    data = dict(
        verified_callback_result=v,
        action=action,
        auth_domain=v.auth_domain,
        challenge_id=v.challenge_id,
        k1_hash=v.k1_hash,
        linking_key_hash=v.linking_key_hash,
        device_public_key="device-public-key",
        device_key_fingerprint="sha256:device",
        device_binding_signature="sig:valid",
        device_class=WalletDeviceClass.MOBILE_VAULT,
        requested_scopes=("read", "pro"),
        client_origin="https://app.example",
        normalized_linking_public_key=KEY,
        session_public_key="session-public-key",
        session_public_key_fingerprint="sha256:session",
    )
    data.update(overrides)
    return LNURLAuthSessionBridgeRequest(**data)


def bridge(*, principal=None, device=None, entitlement=None, policy=None, pop=None, revocations=None, events=None) -> LNURLAuthSessionBridge:
    return LNURLAuthSessionBridge(
        principal_service=principal or principal_service(),
        device_binding=device or DeviceBridge(),
        entitlement_service=entitlement or Entitlements(scopes=("read",)),
        policy_engine=policy or Policy(),
        pop_session_service=pop or PopSessions(),
        revocation_registry=revocations,
        audit_emitter=(lambda event, payload: events.append((event, payload))) if events is not None else None,
        clock=lambda: NOW,
    )


def test_register_creates_principal_binds_device_and_restricted_pop_session() -> None:
    events: list[tuple[str, dict[str, object]]] = []
    pop = PopSessions()
    result = asyncio.run(bridge(pop=pop, events=events).create_session(request()))
    assert result.status is LNURLAuthSessionBridgeStatus.SESSION_CREATED
    assert result.session_token == "bbp_sess_secret_once"
    assert result.approved_scopes == ("read",)
    assert result.denied_scopes == ("pro",)
    assert pop.created[0].auth_method == "lnurl_auth"
    assert pop.created[0].device_key_fingerprint == "sha256:device"
    assert "lnurl_session_created" in [name for name, _ in events]


def test_login_resolves_existing_principal_and_does_not_create_missing() -> None:
    principals = principal_service()
    asyncio.run(bridge(principal=principals).create_session(request()))
    result = asyncio.run(bridge(principal=principals).create_session(request(LNURLAuthAction.LOGIN, verified_callback_result=verified(LNURLAuthAction.LOGIN))))
    assert result.status is LNURLAuthSessionBridgeStatus.SESSION_CREATED
    missing = principal_service()
    with pytest.raises(Exception) as exc:
        asyncio.run(bridge(principal=missing).create_session(request(LNURLAuthAction.LOGIN, verified_callback_result=verified(LNURLAuthAction.LOGIN))))
    assert getattr(exc.value, "reason_code") == "principal_not_found"


def test_auth_creates_narrow_step_up_bound_to_pending_intent() -> None:
    principals = principal_service()
    device = DeviceBridge()
    asyncio.run(bridge(principal=principals, device=device).create_session(request()))
    result = asyncio.run(bridge(principal=principals, device=device).create_session(
        request(LNURLAuthAction.AUTH, verified_callback_result=verified(LNURLAuthAction.AUTH), pending_intent_hash="sha256:intent")
    ))
    assert result.status is LNURLAuthSessionBridgeStatus.STEP_UP_CREATED
    assert result.session_token is None
    assert result.step_up is not None
    assert result.step_up.intent_hash == "sha256:intent"


def test_link_requires_existing_session_and_policy_allow() -> None:
    principals = principal_service()
    device = DeviceBridge()
    asyncio.run(bridge(principal=principals, device=device).create_session(request()))
    with pytest.raises(LNURLAuthSessionPolicyError):
        asyncio.run(bridge(principal=principals, device=device).create_session(request(LNURLAuthAction.LINK, verified_callback_result=verified(LNURLAuthAction.LINK))))
    result = asyncio.run(bridge(principal=principals, device=device).create_session(
        request(LNURLAuthAction.LINK, verified_callback_result=verified(LNURLAuthAction.LINK), existing_session_context={"session": "active"}, pending_intent_hash="sha256:link")
    ))
    assert result.status is LNURLAuthSessionBridgeStatus.LINKED
    assert result.session_token is None
    assert "no_automatic_merge" in result.limitations


def test_callback_validation_rejects_unverified_unconsumed_replay_and_mismatch() -> None:
    for bad in (
        verified(consumed=False),
        verified(replay_status="replayed"),
    ):
        with pytest.raises(LNURLAuthSessionInvalidCallbackError):
            asyncio.run(bridge().create_session(request(verified_callback_result=bad)))
    bad = verified()
    object.__setattr__(bad, "verified", False)
    with pytest.raises(LNURLAuthSessionInvalidCallbackError):
        asyncio.run(bridge().create_session(request(verified_callback_result=bad)))
    with pytest.raises(LNURLAuthSessionInvalidCallbackError):
        asyncio.run(bridge().create_session(request(LNURLAuthAction.LOGIN, verified_callback_result=verified(LNURLAuthAction.REGISTER))))


def test_device_failures_and_duplicate_binding_idempotency() -> None:
    device = DeviceBridge()
    svc = bridge(device=device)
    asyncio.run(svc.create_session(request()))
    again = asyncio.run(svc.create_session(request()))
    assert again.status is LNURLAuthSessionBridgeStatus.SESSION_CREATED
    assert device.calls == 2
    with pytest.raises(LNURLAuthSessionDeviceError):
        asyncio.run(bridge(device=DeviceBridge()).create_session(request(device_binding_signature="sig:bad")))
    revoked = DeviceBridge()
    revoked.revoked.add("sha256:device")
    with pytest.raises(LNURLAuthSessionDeviceError):
        asyncio.run(bridge(device=revoked).create_session(request()))


def test_entitlement_and_policy_intersection_no_wildcards_or_premium_escalation() -> None:
    result = asyncio.run(bridge(entitlement=Entitlements(scopes=("read",))).create_session(request(requested_scopes=("read", "admin"))))
    assert result.approved_scopes == ("read",)
    assert result.denied_scopes == ("admin",)
    with pytest.raises(LNURLAuthSessionPolicyError):
        asyncio.run(bridge().create_session(request(requested_scopes=("api:all",))))
    with pytest.raises(LNURLAuthSessionPolicyError):
        asyncio.run(bridge(policy=Policy("deny")).create_session(request()))
    with pytest.raises(LNURLAuthSessionPolicyError):
        asyncio.run(bridge(policy=Policy("step_up_required")).create_session(request()))


def test_access_certificate_required_returns_next_action_without_session() -> None:
    result = asyncio.run(bridge(policy=Policy("access_certificate_required")).create_session(request()))
    assert result.status is LNURLAuthSessionBridgeStatus.DENIED
    assert result.session_token is None
    assert result.access_certificate_required is True
    assert result.next_action == "issue_access_certificate"


def test_revocation_recovery_and_suspended_principal_handling() -> None:
    revocations = Revocations()
    principals = principal_service()
    asyncio.run(bridge(principal=principals).create_session(request()))
    existing = principals.find_by_lnurl_key(normalized_linking_public_key=KEY, auth_domain="auth.bitcoin-bastion.com")
    assert existing is not None
    principals.suspend_principal(existing.principal_hash, reason_code="risk")
    with pytest.raises(Exception):
        asyncio.run(bridge(principal=principals).create_session(request(LNURLAuthAction.LOGIN, verified_callback_result=verified(LNURLAuthAction.LOGIN))))
    principals.activate_principal(existing.principal_hash, reason_code="ok")
    revocations.revoked.add(("lightning_wallet_principal", existing.principal_hash))
    with pytest.raises(Exception) as exc:
        asyncio.run(bridge(principal=principals, revocations=revocations).create_session(request(LNURLAuthAction.LOGIN, verified_callback_result=verified(LNURLAuthAction.LOGIN))))
    assert getattr(exc.value, "reason_code") == "principal_revoked"


def test_response_logs_and_audit_exclude_raw_secrets_and_secret_inputs_rejected() -> None:
    events: list[tuple[str, dict[str, object]]] = []
    result = asyncio.run(bridge(events=events).create_session(request(request_context={"safe": "metadata"})))
    rendered = repr(result) + repr(events)
    assert KEY not in rendered
    assert "k1_raw_secret" not in rendered
    assert "wallet_signature" not in rendered
    assert "bbp_sess_secret_once" in result.session_token
    assert "bbp_sess_secret_once" not in repr(events)
    with pytest.raises(Exception):
        asyncio.run(bridge().create_session(request(request_context={"mnemonic": "seed phrase words"})))


def test_session_token_returned_once_and_reused_callback_not_allowed_by_replay_status() -> None:
    first = asyncio.run(bridge().create_session(request()))
    assert first.session_token == "bbp_sess_secret_once"
    replayed = verified(replay_status="replayed")
    with pytest.raises(LNURLAuthSessionInvalidCallbackError):
        asyncio.run(bridge().create_session(request(verified_callback_result=replayed)))


def test_policy_request_contains_required_actor_device_entitlement_and_risk_context() -> None:
    policy = Policy()
    asyncio.run(bridge(policy=policy, entitlement=Entitlements(plan="pro", scopes=("read", "pro"))).create_session(request(requested_scopes=("read", "pro"))))
    payload = policy.inputs[0]
    assert payload["actor_type"] == "lightning_wallet_principal"
    assert payload["auth_method"] == "lnurl_auth"
    assert payload["device_key_fingerprint"] == "sha256:device"
    assert payload["subscription_plan"] == "pro"
    assert payload["lnurl_action"] == "register"
