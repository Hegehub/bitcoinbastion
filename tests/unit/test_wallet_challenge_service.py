from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from app.domain.wallet_auth.networks import WalletNetwork
from app.domain.wallet_auth.proofs import WalletProofType
from app.services.wallet_auth.challenge_service import (
    WalletChallengeConsumedError,
    WalletChallengeContextMismatchError,
    WalletChallengeDeviceMismatchError,
    WalletChallengeExpiredError,
    WalletChallengeIntentMismatchError,
    WalletChallengeNetworkMismatchError,
    WalletChallengeOriginMismatchError,
    WalletChallengePolicyRejectedError,
    WalletChallengeRevokedError,
    WalletChallengeService,
)
from app.services.wallet_auth.repositories.challenges import InMemoryWalletChallengeRepository
from app.services.wallet_auth.types import WalletChallengePurpose, WalletChallengeStatus


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 7, 12, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: int) -> None:
        self.now += timedelta(seconds=seconds)


class Revoked:
    def __init__(self, target: tuple[str, str]) -> None:
        self.target = target

    def is_revoked(self, *, target_type: str, target_hash: str) -> bool:
        return (target_type, target_hash) == self.target


class RateLimited:
    def check(self, **_: object) -> None:
        raise RuntimeError("limited")


def run(coro):
    return asyncio.run(coro)


def service(*, clock: Clock | None = None, audit: list | None = None, **kwargs) -> WalletChallengeService:
    return WalletChallengeService(
        InMemoryWalletChallengeRepository(),
        server_pepper="test-pepper",
        now_factory=clock or Clock(),
        audit_emitter=(lambda event, payload: audit.append((event, payload))) if audit is not None else None,
        **kwargs,
    )


async def create(service: WalletChallengeService, **overrides):
    data = dict(
        purpose=WalletChallengePurpose.LOGIN,
        network=WalletNetwork.BITCOIN_MAINNET,
        proof_type=WalletProofType.BIP322,
        origin="https://auth.bitcoin-bastion.com",
        device_key_fingerprint="dev_fp_12345",
        requested_scopes=(),
    )
    data.update(overrides)
    return await service.create_challenge(**data)


def test_creation_for_required_purposes_and_unique_ids_nonces():
    async def scenario():
        svc = service()
        purposes = [
            WalletChallengePurpose.REGISTER,
            WalletChallengePurpose.LOGIN,
            WalletChallengePurpose.NEW_DEVICE,
            WalletChallengePurpose.STEP_UP,
            WalletChallengePurpose.RECOVERY_START,
            WalletChallengePurpose.LINK_WALLET,
            WalletChallengePurpose.OWNERSHIP_PROOF,
            WalletChallengePurpose.HARDWARE_WALLET_PROOF,
            WalletChallengePurpose.ACCESS_CERTIFICATE_BRIDGE,
        ]
        results = [await create(svc, purpose=purpose, requested_scopes=("devices:write",) if purpose == WalletChallengePurpose.NEW_DEVICE else ()) for purpose in purposes]
        assert len({result.challenge_id for result in results}) == len(results)
        assert len({result.nonce for result in results}) == len(results)
        for result in results:
            assert result.status == WalletChallengeStatus.PENDING.value
            assert "This signature does not authorize a Bitcoin transaction." in result.signable_message
            assert "Nonce:" in result.signable_message
            assert "Origin:" in result.signable_message
            assert result.intent_hash.startswith("sha256:")
    run(scenario())


def test_persists_policy_epoch_and_normalized_scopes():
    async def scenario():
        svc = service()
        result = await create(svc, requested_scopes=("metrics:read", "quotes:read", "metrics:read"))
        record = await svc.get_challenge(result.challenge_id)
        assert record.policy_hash.startswith("hmac-sha256:")
        assert record.policy_epoch == 1
        assert record.crypto_epoch == 1
        assert record.schema_epoch == 1
        assert record.requested_scopes == ("metrics:read", "quotes:read")
        assert record.intent["nonce"] == "<redacted>"
        assert "nonce_hash" in record.intent
    run(scenario())


def test_validation_rejects_wrong_context():
    async def scenario():
        svc = service()
        result = await create(svc, requested_scopes=("quotes:read",))
        await svc.validate_pending_challenge(
            challenge_id=result.challenge_id,
            expected_purpose=WalletChallengePurpose.LOGIN,
            expected_origin="https://auth.bitcoin-bastion.com",
            expected_network=WalletNetwork.BITCOIN_MAINNET,
            expected_device_key_fingerprint="dev_fp_12345",
            expected_requested_scopes=("quotes:read",),
        )
        with pytest.raises(WalletChallengeContextMismatchError):
            await svc.validate_pending_challenge(challenge_id=result.challenge_id, expected_purpose=WalletChallengePurpose.REGISTER, expected_origin="https://auth.bitcoin-bastion.com", expected_network=WalletNetwork.BITCOIN_MAINNET, expected_device_key_fingerprint="dev_fp_12345")
        with pytest.raises(WalletChallengeOriginMismatchError):
            await svc.validate_pending_challenge(challenge_id=result.challenge_id, expected_purpose=WalletChallengePurpose.LOGIN, expected_origin="https://bitcoin-bastion.com", expected_network=WalletNetwork.BITCOIN_MAINNET, expected_device_key_fingerprint="dev_fp_12345")
        with pytest.raises(WalletChallengeNetworkMismatchError):
            await svc.validate_pending_challenge(challenge_id=result.challenge_id, expected_purpose=WalletChallengePurpose.LOGIN, expected_origin="https://auth.bitcoin-bastion.com", expected_network=WalletNetwork.BITCOIN_TESTNET, expected_device_key_fingerprint="dev_fp_12345")
        with pytest.raises(WalletChallengeDeviceMismatchError):
            await svc.validate_pending_challenge(challenge_id=result.challenge_id, expected_purpose=WalletChallengePurpose.LOGIN, expected_origin="https://auth.bitcoin-bastion.com", expected_network=WalletNetwork.BITCOIN_MAINNET, expected_device_key_fingerprint="dev_fp_other")
    run(scenario())


def test_policy_rejects_bad_proof_broad_scopes_and_secret_inputs():
    async def scenario():
        svc = service()
        with pytest.raises(ValueError):
            await create(svc, network="dogecoin")
        with pytest.raises(WalletChallengePolicyRejectedError):
            await create(svc, requested_scopes=("api:all",))
        with pytest.raises(WalletChallengePolicyRejectedError):
            await create(svc, requested_scopes=("unknown:scope",))
        with pytest.raises(WalletChallengePolicyRejectedError):
            await create(svc, purpose=WalletChallengePurpose.RECOVERY_START, proof_type=WalletProofType.LEGACY_MESSAGE_SIGNATURE)
        with pytest.raises(WalletChallengeDeviceMismatchError) as excinfo:
            await create(svc, device_key_fingerprint="xprv-secret-device")
        assert "xprv-secret-device" not in str(excinfo.value)
    run(scenario())


def test_expiry_revoke_and_state_machine():
    async def scenario():
        clock = Clock()
        svc = service(clock=clock)
        result = await create(svc)
        clock.advance(301)
        with pytest.raises(WalletChallengeExpiredError):
            await svc.validate_pending_challenge(challenge_id=result.challenge_id, expected_purpose=WalletChallengePurpose.LOGIN, expected_origin="https://auth.bitcoin-bastion.com", expected_network=WalletNetwork.BITCOIN_MAINNET, expected_device_key_fingerprint="dev_fp_12345")
        with pytest.raises(WalletChallengeExpiredError):
            await svc.consume_challenge(challenge_id=result.challenge_id, expected_intent_hash=result.intent_hash)
        assert await svc.expire_due_challenges() == 0

        fresh = await create(svc)
        revoked = await svc.revoke_challenge(challenge_id=fresh.challenge_id, reason_code="operator_revoked")
        assert revoked.status == WalletChallengeStatus.REVOKED.value
        with pytest.raises(WalletChallengeRevokedError):
            await svc.validate_pending_challenge(challenge_id=fresh.challenge_id, expected_purpose=WalletChallengePurpose.LOGIN, expected_origin="https://auth.bitcoin-bastion.com", expected_network=WalletNetwork.BITCOIN_MAINNET, expected_device_key_fingerprint="dev_fp_12345")
        with pytest.raises(Exception):
            await svc.revoke_challenge(challenge_id=fresh.challenge_id, reason_code="again")
    run(scenario())


def test_consume_is_single_use_and_intent_bound():
    async def scenario():
        audit = []
        svc = service(audit=audit)
        result = await create(svc)
        with pytest.raises(WalletChallengeIntentMismatchError):
            await svc.consume_challenge(challenge_id=result.challenge_id, expected_intent_hash="sha256:" + "0" * 64)
        consumed = await svc.consume_challenge(challenge_id=result.challenge_id, expected_intent_hash=result.intent_hash)
        assert consumed.status == WalletChallengeStatus.CONSUMED.value
        with pytest.raises(WalletChallengeConsumedError):
            await svc.consume_challenge(challenge_id=result.challenge_id, expected_intent_hash=result.intent_hash)
        assert "wallet_challenge_consumed" in [event for event, _ in audit]
        assert "wallet_challenge_replay_rejected" in [event for event, _ in audit]
    run(scenario())


def test_revocation_and_rate_limit_hooks():
    async def scenario():
        with pytest.raises(WalletChallengeRevokedError):
            await create(service(revocation_checker=Revoked(("proof_method", WalletProofType.BIP322.value))))
        with pytest.raises(Exception):
            await create(service(rate_limiter=RateLimited()))
    run(scenario())


def test_audit_payload_has_no_raw_nonce_or_wallet_secret():
    async def scenario():
        audit = []
        svc = service(audit=audit)
        result = await create(svc)
        payload = audit[0][1]
        assert result.nonce not in str(payload)
        assert "seed" not in str(payload).lower()
        assert "private" not in str(payload).lower()
        assert "origin_hash" in payload
        assert "challenge_hash" in payload
    run(scenario())
