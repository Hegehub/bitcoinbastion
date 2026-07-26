from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlsplit

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models.access import AccessAuditEvent
from app.db.models.lnurl import LNURLAuthChallenge
from app.db.models.wallet_auth import RecoveryCapsule as CapsuleRow, WalletPrincipal
from app.services.access.crypto.hashing import hmac_sha256_prefixed
from app.services.lnurl.auth_callback_verifier import (
    SECP256K1_ORDER,
    LNURLAuthCallbackConfig,
    LNURLAuthCallbackStatus,
    LNURLAuthCallbackVerifier,
)
from app.services.lnurl.auth_challenge_service import InMemoryLNURLAuthChallengeRepository
from app.services.lnurl.k1_registry import (
    InMemoryK1Repository,
    LNURLK1Config,
    LNURLK1RegistryService,
)
from app.services.wallet_auth.lnurl_recovery_factor import (
    LNURLRecoveryConfig,
    LNURLRecoveryFactorService,
    RECOVERY_PUBLIC_ERROR,
    RECOVERY_WARNING,
)
from app.services.wallet_auth.recovery.capsule import RecoveryCapsuleService
from app.services.wallet_auth.recovery.factor_registry import RecoveryFactorRegistry
from app.services.wallet_auth.recovery.models import RecoveryFactorType, RecoveryProfile

NOW = datetime(2099, 7, 26, 12, tzinfo=UTC)


class Clock:
    now = NOW

    def __call__(self) -> datetime:
        return self.now


class Policy:
    def authorize(self, *, action, capsule):
        return True, "policy_allowed"


class Revocations:
    values: dict[str, bool] = {}

    def check(self, **kwargs):
        return dict(self.values)

    def check_recovery_targets(self, **kwargs):
        return dict(self.values)


class Artifacts:
    def secure_after_recovery(self, *, capsule):
        return ("wallet_session",)


class Signer:
    def sign(self, payload):
        return {"alg": "ed25519", "key_id": "test-issuer", "sig": "test-signature"}

    def verify(self, payload, signature):
        return signature == self.sign(payload)


def _key_and_signature(k1: str, private_key=None):
    private_key = private_key or ec.generate_private_key(ec.SECP256K1())
    key = (
        private_key.public_key()
        .public_bytes(serialization.Encoding.X962, serialization.PublicFormat.CompressedPoint)
        .hex()
    )
    while True:
        signature = private_key.sign(bytes.fromhex(k1), ec.ECDSA(utils.Prehashed(hashes.SHA256())))
        _r, s = utils.decode_dss_signature(signature)
        if s <= SECP256K1_ORDER // 2:
            return private_key, key, signature.hex()


def _fixture():
    engine = create_engine("sqlite:///:memory:")
    WalletPrincipal.__table__.create(engine)
    CapsuleRow.__table__.create(engine)
    AccessAuditEvent.__table__.create(engine)
    LNURLAuthChallenge.__table__.create(engine)
    db = Session(engine)
    principal = WalletPrincipal(
        principal_hash="hmac-sha256:principal",
        principal_type="lightning_wallet_principal",
        status="active",
        verification_strength="standard",
        primary_proof_method="lnurl_auth",
        policy_epoch=1,
        crypto_epoch=1,
        schema_epoch=1,
    )
    db.add(principal)
    db.flush()
    clock, registry = Clock(), RecoveryFactorRegistry()
    capsule_service = RecoveryCapsuleService(
        db,
        server_pepper="test-capsule-pepper",
        factor_registry=registry,
        policy_authorizer=Policy(),
        revocation_resolver=Revocations(),
        artifact_manager=Artifacts(),
        clock=clock,
    )
    capsule = capsule_service.create(
        principal_id=principal.id,
        principal_hash=principal.principal_hash,
        principal_type=principal.principal_type,
        recovery_profile=RecoveryProfile.LITE_BASIC,
        recovery_reason="lost_device",
        requested_operations=("bind_replacement_device",),
    )
    k1_registry = LNURLK1RegistryService(
        config=LNURLK1Config(
            server_pepper="test-k1-pepper",
            recovery_ttl_seconds=300,
            allow_test_pepper=True,
        ),
        repository=InMemoryK1Repository(),
        clock=clock,
    )
    challenge_repository = InMemoryLNURLAuthChallengeRepository()
    callback = LNURLAuthCallbackVerifier(
        config=LNURLAuthCallbackConfig(
            principal_server_pepper="test-principal-pepper", allow_test_pepper=True
        ),
        k1_registry=k1_registry,
        challenge_repository=challenge_repository,
        clock=clock,
    )
    service = LNURLRecoveryFactorService(
        config=LNURLRecoveryConfig(),
        capsule_service=capsule_service,
        k1_registry=k1_registry,
        callback_verifier=callback,
        challenge_repository=challenge_repository,
        receipt_signer=Signer(),
        revocation_checker=Revocations(),
        clock=clock,
    )
    registry.register(service.factor_verifier())
    return db, clock, capsule_service, capsule, service


def test_valid_callback_satisfies_only_one_attempt_bound_factor() -> None:
    db, _clock, capsules, capsule, service = _fixture()
    private_key, key, _unused = _key_and_signature("00" * 32)
    key_hash = hmac_sha256_prefixed("test-principal-pepper", bytes.fromhex(key))
    challenge = service.issue_challenge(
        recovery_attempt_hash=capsule.capsule_hash,
        lnurl_principal_hash="hmac-sha256:lightning-principal",
        expected_lnurl_key_hash=key_hash,
    )
    # LNURL is bech32, so obtain the raw k1 from the shared registry's test record.
    raw_k1 = next(iter(service.k1_registry.repository._records.values()))
    lookup = raw_k1.k1_lookup_hash
    assert lookup.startswith("hmac-sha256:")
    # The raw value is intentionally absent from storage; recover it from callback URL decoding.
    from app.services.lnurl.encoding import decode_lnurl

    callback_url = decode_lnurl(challenge.lnurl).normalized_url
    k1_value = parse_qs(urlsplit(callback_url).query)["k1"][0]
    _private, key, sig = _key_and_signature(k1_value, private_key)
    response = asyncio.run(
        service.verify_callback(
            k1=k1_value,
            key=key,
            sig=sig,
            callback_host="auth.bitcoin-bastion.com",
        )
    )
    assert response.status is LNURLAuthCallbackStatus.OK
    updated = capsules.get(capsule.capsule_hash)
    assert updated.verified_factors == (RecoveryFactorType.LNURL_AUTH_PROOF,)
    assert updated.status.value == "awaiting_factors"
    assert challenge.remaining_factor_count >= 1
    assert "does not complete recovery" in RECOVERY_WARNING
    db.close()


def test_replay_principal_mismatch_and_expiry_use_same_public_error() -> None:
    db, clock, capsules, capsule, service = _fixture()
    private_key, key, _unused = _key_and_signature("00" * 32)
    expected = hmac_sha256_prefixed("test-principal-pepper", bytes.fromhex(key))
    challenge = service.issue_challenge(
        recovery_attempt_hash=capsule.capsule_hash,
        lnurl_principal_hash="hmac-sha256:lightning-principal",
        expected_lnurl_key_hash=expected,
    )
    from app.services.lnurl.encoding import decode_lnurl

    k1 = parse_qs(urlsplit(decode_lnurl(challenge.lnurl).normalized_url).query)["k1"][0]
    _private, key, sig = _key_and_signature(k1, private_key)
    first = asyncio.run(
        service.verify_callback(k1=k1, key=key, sig=sig, callback_host="auth.bitcoin-bastion.com")
    )
    replay = asyncio.run(
        service.verify_callback(k1=k1, key=key, sig=sig, callback_host="auth.bitcoin-bastion.com")
    )
    assert first.status is LNURLAuthCallbackStatus.OK
    assert replay.reason == RECOVERY_PUBLIC_ERROR
    assert len(capsules.get(capsule.capsule_hash).verified_factors) == 1

    db2, clock2, _capsules2, capsule2, service2 = _fixture()
    _wrong_private, wrong_key, _ = _key_and_signature("00" * 32)
    challenge2 = service2.issue_challenge(
        recovery_attempt_hash=capsule2.capsule_hash,
        lnurl_principal_hash="hmac-sha256:expected",
        expected_lnurl_key_hash="hmac-sha256:not-the-key",
    )
    k12 = parse_qs(urlsplit(decode_lnurl(challenge2.lnurl).normalized_url).query)["k1"][0]
    _p, wrong_key, wrong_sig = _key_and_signature(k12, _wrong_private)
    mismatch = asyncio.run(
        service2.verify_callback(
            k1=k12,
            key=wrong_key,
            sig=wrong_sig,
            callback_host="auth.bitcoin-bastion.com",
        )
    )
    assert mismatch.reason == RECOVERY_PUBLIC_ERROR
    clock2.now += timedelta(seconds=301)
    expired = asyncio.run(
        service2.verify_callback(
            k1=k12,
            key=wrong_key,
            sig=wrong_sig,
            callback_host="auth.bitcoin-bastion.com",
        )
    )
    assert expired.reason == RECOVERY_PUBLIC_ERROR
    db.close()
    db2.close()
