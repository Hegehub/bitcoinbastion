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
    WalletChallengeService,
)
from app.services.wallet_auth.repositories.challenges import InMemoryWalletChallengeRepository
from app.services.wallet_auth.types import WalletChallengePurpose, WalletChallengeStatus


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 7, 12, 14, 0, tzinfo=UTC)
    def __call__(self) -> datetime:
        return self.now
    def advance(self, seconds: int) -> None:
        self.now += timedelta(seconds=seconds)


def run(coro):
    return asyncio.run(coro)


async def create(service: WalletChallengeService, **overrides):
    data = dict(
        purpose=WalletChallengePurpose.LOGIN,
        network=WalletNetwork.BITCOIN_MAINNET,
        proof_type=WalletProofType.BIP322,
        origin="https://auth.bitcoin-bastion.com",
        device_key_fingerprint="dev_fp_security",
        requested_scopes=("quotes:read",),
    )
    data.update(overrides)
    return await service.create_challenge(**data)


def test_nonce_challenge_reuse_and_concurrent_replay_fail():
    async def scenario():
        svc = WalletChallengeService(InMemoryWalletChallengeRepository(), server_pepper="pepper")
        result = await create(svc)
        consumed = await svc.consume_challenge(challenge_id=result.challenge_id, expected_intent_hash=result.intent_hash)
        assert consumed.status == WalletChallengeStatus.CONSUMED.value
        with pytest.raises(WalletChallengeConsumedError):
            await svc.consume_challenge(challenge_id=result.challenge_id, expected_intent_hash=result.intent_hash)

        second = await create(svc)
        outcomes = await asyncio.gather(
            svc.consume_challenge(challenge_id=second.challenge_id, expected_intent_hash=second.intent_hash),
            svc.consume_challenge(challenge_id=second.challenge_id, expected_intent_hash=second.intent_hash),
            return_exceptions=True,
        )
        assert sum(not isinstance(item, Exception) for item in outcomes) == 1
        assert sum(isinstance(item, WalletChallengeConsumedError) for item in outcomes) == 1
    run(scenario())


def test_intent_origin_network_device_and_purpose_substitution_fail():
    async def scenario():
        svc = WalletChallengeService(InMemoryWalletChallengeRepository(), server_pepper="pepper")
        result = await create(svc)
        with pytest.raises(WalletChallengeIntentMismatchError):
            await svc.consume_challenge(challenge_id=result.challenge_id, expected_intent_hash="sha256:" + "f" * 64)
        with pytest.raises(WalletChallengeOriginMismatchError):
            await svc.validate_pending_challenge(challenge_id=result.challenge_id, expected_purpose=WalletChallengePurpose.LOGIN, expected_origin="https://bitcoin-bastion.com", expected_network=WalletNetwork.BITCOIN_MAINNET, expected_device_key_fingerprint="dev_fp_security", expected_requested_scopes=("quotes:read",))
        with pytest.raises(WalletChallengeNetworkMismatchError):
            await svc.validate_pending_challenge(challenge_id=result.challenge_id, expected_purpose=WalletChallengePurpose.LOGIN, expected_origin="https://auth.bitcoin-bastion.com", expected_network=WalletNetwork.BITCOIN_TESTNET, expected_device_key_fingerprint="dev_fp_security", expected_requested_scopes=("quotes:read",))
        with pytest.raises(WalletChallengeDeviceMismatchError):
            await svc.validate_pending_challenge(challenge_id=result.challenge_id, expected_purpose=WalletChallengePurpose.LOGIN, expected_origin="https://auth.bitcoin-bastion.com", expected_network=WalletNetwork.BITCOIN_MAINNET, expected_device_key_fingerprint="dev_fp_wrong", expected_requested_scopes=("quotes:read",))
        with pytest.raises(WalletChallengeContextMismatchError):
            await svc.validate_pending_challenge(challenge_id=result.challenge_id, expected_purpose=WalletChallengePurpose.REGISTER, expected_origin="https://auth.bitcoin-bastion.com", expected_network=WalletNetwork.BITCOIN_MAINNET, expected_device_key_fingerprint="dev_fp_security", expected_requested_scopes=("quotes:read",))
    run(scenario())


def test_scope_escalation_stale_challenge_and_secret_errors_are_safe():
    async def scenario():
        clock = Clock()
        svc = WalletChallengeService(InMemoryWalletChallengeRepository(), server_pepper="pepper", now_factory=clock)
        with pytest.raises(WalletChallengePolicyRejectedError):
            await create(svc, requested_scopes=("quotes:read", "admin:all"))
        result = await create(svc)
        with pytest.raises(WalletChallengeContextMismatchError):
            await svc.validate_pending_challenge(challenge_id=result.challenge_id, expected_purpose=WalletChallengePurpose.LOGIN, expected_origin="https://auth.bitcoin-bastion.com", expected_network=WalletNetwork.BITCOIN_MAINNET, expected_device_key_fingerprint="dev_fp_security", expected_requested_scopes=("metrics:read", "quotes:read"))
        clock.advance(301)
        with pytest.raises(WalletChallengeExpiredError):
            await svc.consume_challenge(challenge_id=result.challenge_id, expected_intent_hash=result.intent_hash)
        record = await svc.get_challenge(result.challenge_id)
        assert record.status == WalletChallengeStatus.EXPIRED.value
        with pytest.raises(Exception) as excinfo:
            await create(svc, device_key_fingerprint="private_key_material")
        assert "private_key_material" not in str(excinfo.value)
    run(scenario())
