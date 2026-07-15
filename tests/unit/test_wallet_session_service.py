from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.db.repositories.wallet_device_repository import WalletDeviceRecord
from app.domain.wallet_auth.devices import WalletDeviceBindingMethod, WalletDeviceClass, WalletDeviceStatus
from app.domain.wallet_auth.networks import WalletNetwork
from app.domain.wallet_auth.principals import WalletPrincipalStatus
from app.domain.wallet_auth.proofs import WalletProofType, WalletVerificationStrength
from app.services.wallet_auth.device_key_validation import compute_device_key_fingerprint
from app.services.wallet_auth.principal_types import PrincipalType, WalletPrincipalRecord
from app.services.wallet_auth.session_service import (
    EntitlementSnapshot,
    InMemoryWalletSessionRepository,
    PolicyDecision,
    VerifiedWalletAuthenticationContext,
    WalletSessionError,
    WalletSessionService,
    sessions_require_request_signature,
)

NOW = datetime(2026, 7, 14, tzinfo=UTC)
PRINCIPAL_HASH = "hmac-sha256:" + "a" * 64
PROOF_HASH = "sha256:" + "b" * 64
CHALLENGE_HASH = "sha256:" + "c" * 64
DEVICE_FP = "sha256:" + "d" * 64
POLICY_HASH = "sha256:" + "e" * 64


def _public_key() -> str:
    key = Ed25519PrivateKey.generate().public_key()
    raw = key.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
    import base64

    return base64.b64encode(raw).decode("ascii")


def _ctx(session_fp: str, *, used: bool = False, origin: str = "https://app.example", status=WalletPrincipalStatus.ACTIVE, device_status=WalletDeviceStatus.ACTIVE, scopes=("read",), action="create_session", strength=WalletVerificationStrength.STANDARD, recovery=False) -> VerifiedWalletAuthenticationContext:
    return VerifiedWalletAuthenticationContext(
        principal_hash=PRINCIPAL_HASH,
        principal_type=PrincipalType.BITCOIN_WALLET_PRINCIPAL,
        principal_status=status,
        proof_fingerprint=PROOF_HASH,
        proof_type=WalletProofType.BIP322,
        verification_strength=strength,
        proof_verified_at=NOW,
        proof_expires_at=NOW + timedelta(minutes=5),
        challenge_id="challenge-1",
        challenge_hash=CHALLENGE_HASH,
        challenge_action=action,
        challenge_origin="https://app.example",
        challenge_used=used,
        device_binding_id=1,
        device_key_fingerprint=DEVICE_FP,
        device_status=device_status,
        device_risk_score=10,
        requested_scopes=tuple(scopes),
        auth_method="bip322",
        policy_hash=POLICY_HASH,
        policy_epoch=1,
        crypto_epoch=1,
        origin=origin,
        expected_session_public_key_fingerprint=session_fp,
        expected_device_key_fingerprint=DEVICE_FP,
        network="bitcoin-mainnet",
        recovery_only_requested=recovery,
    )


class PrincipalLookup:
    def __init__(self, status=WalletPrincipalStatus.ACTIVE):
        self.status = status

    async def get_principal(self, principal_hash):
        return self._record(principal_hash)

    async def verify_principal_status(self, principal_hash):
        if self.status is not WalletPrincipalStatus.ACTIVE:
            raise WalletSessionError("wallet_session_principal_inactive")
        return self._record(principal_hash)

    def _record(self, principal_hash):
        return WalletPrincipalRecord(
            principal_hash=principal_hash,
            principal_type=PrincipalType.BITCOIN_WALLET_PRINCIPAL,
            status=self.status,
            network=WalletNetwork.BITCOIN_MAINNET,
            primary_proof_method=WalletProofType.BIP322,
            current_proof_strength=WalletVerificationStrength.STANDARD,
            highest_verified_strength=WalletVerificationStrength.STANDARD,
            address_hash=None,
            script_pubkey_hash=None,
            schema_epoch=1,
            crypto_epoch=1,
            policy_epoch=1,
            created_at=NOW,
            updated_at=NOW,
            last_verified_at=NOW,
        )


class DeviceLookup:
    def __init__(self, status=WalletDeviceStatus.ACTIVE):
        self.status = status

    async def assert_device_active(self, *, principal_hash, device_key_fingerprint):
        if self.status is not WalletDeviceStatus.ACTIVE:
            raise WalletSessionError("wallet_session_device_inactive")
        return WalletDeviceRecord(
            id=1,
            principal_hash=principal_hash,
            device_id_hash="hmac-sha256:" + "f" * 64,
            device_key_fingerprint=device_key_fingerprint,
            device_public_key_b64="pub",
            key_algorithm="ed25519",
            device_class=WalletDeviceClass.DESKTOP_VAULT,
            binding_method=WalletDeviceBindingMethod.WALLET_PROOF_REGISTRATION,
            proof_type=WalletProofType.BIP322,
            verification_strength=WalletVerificationStrength.STANDARD,
            status=self.status,
            risk_score=10,
            risk_level="low",
            risk_reason_codes=(),
        )


class ChallengeConsumer:
    def __init__(self):
        self.used = set()

    async def consume_for_session(self, *, challenge_id, challenge_hash, origin):
        if challenge_id in self.used:
            raise WalletSessionError("wallet_session_challenge_used")
        self.used.add(challenge_id)


class Policy:
    def __init__(self, decision="allow"):
        self.decision = decision

    async def decide_session_create(self, context):
        return PolicyDecision(decision=self.decision, decision_hash="sha256:" + "1" * 64, reason_code=f"policy_{self.decision}")


class Entitlements:
    def __init__(self, active=True, scopes=("read", "write"), expires_at=NOW + timedelta(hours=1)):
        self.snapshot = EntitlementSnapshot(active=active, entitlement_id="ent_1", effective_plan="basic", allowed_scopes=tuple(scopes), expires_at=expires_at)

    async def get_entitlement_for_principal(self, principal_hash):
        return self.snapshot


class Revocations:
    def __init__(self, revoked=()):
        self.revoked = set(revoked)

    def is_revoked(self, *, target_type, target_hash):
        return (target_type, target_hash) in self.revoked


def _service(**kwargs):
    events = []
    svc = WalletSessionService(
        repository=kwargs.get("repository") or InMemoryWalletSessionRepository(),
        principal_lookup=kwargs.get("principal") or PrincipalLookup(),
        device_lookup=kwargs.get("device") or DeviceLookup(),
        challenge_consumer=kwargs.get("challenge") or ChallengeConsumer(),
        policy_engine=kwargs.get("policy") or Policy(),
        entitlement_service=kwargs.get("entitlement") or Entitlements(),
        revocation_checker=kwargs.get("revocation"),
        audit_chain=lambda e, p: events.append((e, p)),
        server_pepper="test-pepper",
        clock=lambda: NOW,
        max_active_sessions_per_principal=kwargs.get("principal_limit", 5),
        max_active_sessions_per_device=kwargs.get("device_limit", 3),
    )
    return svc, events


def test_verified_bip322_context_creates_pop_session_and_consumes_challenge():
    async def run():
        pub = _public_key()
        fp = compute_device_key_fingerprint(pub)
        svc, events = _service()
        result = await svc.create_session(auth_context=_ctx(fp), session_public_key=pub)
        assert result.token_type == "PoP"
        assert result.session_token.startswith("sess_")
        assert result.requires_request_signature is True
        assert sessions_require_request_signature(result.context) is True
        assert result.context.session_public_key_fingerprint == fp
        assert any(name == "wallet_session_created" for name, _payload in events)



    asyncio.run(run())
def test_raw_token_is_returned_once_but_only_hash_is_persisted():
    async def run():
        pub = _public_key()
        fp = compute_device_key_fingerprint(pub)
        repo = InMemoryWalletSessionRepository()
        svc, _ = _service(repository=repo)
        result = await svc.create_session(auth_context=_ctx(fp), session_public_key=pub)
        stored = await repo.get_by_lookup_hash(result.context.session_lookup_hash)
        assert stored is not None
        assert stored.session_lookup_hash != result.session_token
        assert result.session_token not in repr(stored)



    asyncio.run(run())
@pytest.mark.parametrize("ctx_kwargs,reason", [
    ({"used": True}, "wallet_session_challenge_used"),
    ({"origin": "https://evil.example"}, "wallet_session_origin_mismatch"),
    ({"status": WalletPrincipalStatus.SUSPENDED}, "wallet_session_principal_inactive"),
    ({"device_status": WalletDeviceStatus.SUSPENDED}, "wallet_session_device_inactive"),
])
def test_precondition_failures(ctx_kwargs, reason):
    async def run():
        pub = _public_key()
        fp = compute_device_key_fingerprint(pub)
        svc, _ = _service()
        with pytest.raises(WalletSessionError) as exc:
            await svc.create_session(auth_context=_ctx(fp, **ctx_kwargs), session_public_key=pub)
        assert exc.value.reason_code == reason



    asyncio.run(run())
def test_session_key_fingerprint_mismatch_rejected():
    async def run():
        pub = _public_key()
        other = _public_key()
        fp = compute_device_key_fingerprint(other)
        svc, _ = _service()
        with pytest.raises(WalletSessionError) as exc:
            await svc.create_session(auth_context=_ctx(fp), session_public_key=pub)
        assert exc.value.reason_code == "wallet_session_key_binding_mismatch"



    asyncio.run(run())
def test_policy_deny_and_step_up_do_not_create_session():
    async def run():
        pub = _public_key()
        fp = compute_device_key_fingerprint(pub)
        for decision, expected in [("deny", "wallet_session_policy_denied"), ("step_up_required", "wallet_session_step_up_required")]:
            svc, _ = _service(policy=Policy(decision))
            with pytest.raises(WalletSessionError) as exc:
                await svc.create_session(auth_context=_ctx(fp), session_public_key=pub)
            assert exc.value.reason_code == expected



    asyncio.run(run())
def test_entitlement_scope_and_expiry_caps_session():
    async def run():
        pub = _public_key()
        fp = compute_device_key_fingerprint(pub)
        entitlement = Entitlements(scopes=("read",), expires_at=NOW + timedelta(minutes=2))
        svc, _ = _service(entitlement=entitlement)
        result = await svc.create_session(auth_context=_ctx(fp, scopes=("read",)), session_public_key=pub, requested_ttl_seconds=900)
        assert result.expires_at == entitlement.snapshot.expires_at
        svc2, _ = _service(entitlement=Entitlements(scopes=("read",)))
        with pytest.raises(WalletSessionError) as exc:
            await svc2.create_session(auth_context=_ctx(fp, scopes=("admin",)), session_public_key=pub)
        assert exc.value.reason_code == "wallet_session_scope_not_allowed"



    asyncio.run(run())
def test_session_limits_revocation_freeze_expire_and_rotation():
    async def run():
        pub = _public_key()
        fp = compute_device_key_fingerprint(pub)
        svc, _ = _service(principal_limit=1)
        result = await svc.create_session(auth_context=_ctx(fp), session_public_key=pub)
        with pytest.raises(WalletSessionError):
            await svc.create_session(auth_context=replace(_ctx(fp), challenge_id="challenge-2"), session_public_key=pub)
        assert await svc.freeze_sessions_for_principal(principal_hash=PRINCIPAL_HASH, reason_code="lockdown") == 1
        with pytest.raises(WalletSessionError):
            await svc.validate_session_state(session_token=result.session_token)
        pub2 = _public_key()
        rotated = await svc.rotate_session(session_token=result.session_token, new_session_public_key=pub2)
        assert rotated.session_token != result.session_token
        revoked = await svc.revoke_session(session_token=rotated.session_token, reason_code="user_revoked")
        assert revoked.session_status.value == "revoked"



    asyncio.run(run())
def test_compatibility_and_high_risk_contexts_get_short_ttl_and_private_key_rejected():
    async def run():
        pub = _public_key()
        fp = compute_device_key_fingerprint(pub)
        svc, _ = _service()
        result = await svc.create_session(auth_context=_ctx(fp, strength=WalletVerificationStrength.COMPATIBILITY), session_public_key=pub)
        assert result.expires_at <= NOW + timedelta(minutes=5)
        with pytest.raises(WalletSessionError) as exc:
            await svc.create_session(auth_context=replace(_ctx(fp), challenge_id="challenge-2"), session_public_key="-----BEGIN PRIVATE KEY-----\nabc")
        assert exc.value.reason_code == "wallet_session_private_key_rejected"



    asyncio.run(run())
def test_concurrent_challenge_reuse_allows_one_session():
    async def run():
        pub = _public_key()
        fp = compute_device_key_fingerprint(pub)
        challenge = ChallengeConsumer()
        svc, _ = _service(challenge=challenge, principal_limit=10, device_limit=10)

        async def attempt():
            return await svc.create_session(auth_context=_ctx(fp), session_public_key=pub)

        results = await asyncio.gather(attempt(), attempt(), return_exceptions=True)
        assert sum(not isinstance(item, Exception) for item in results) == 1
        assert sum(isinstance(item, Exception) for item in results) == 1

    asyncio.run(run())
