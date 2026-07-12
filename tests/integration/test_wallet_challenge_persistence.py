from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
import app.db.models  # noqa: F401
from app.domain.wallet_auth.networks import WalletNetwork
from app.domain.wallet_auth.proofs import WalletProofType
from app.services.wallet_auth.challenge_service import WalletChallengeConsumedError, WalletChallengeService
from app.services.wallet_auth.repositories.challenges import SqlAlchemyWalletChallengeRepository
from app.services.wallet_auth.types import WalletChallengePurpose, WalletChallengeStatus


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 7, 12, 13, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: int) -> None:
        self.now += timedelta(seconds=seconds)


def run(coro):
    return asyncio.run(coro)


def db_session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Session(engine)


async def create(service: WalletChallengeService):
    return await service.create_challenge(
        purpose=WalletChallengePurpose.LOGIN,
        network=WalletNetwork.BITCOIN_MAINNET,
        proof_type=WalletProofType.BIP322,
        origin="https://auth.bitcoin-bastion.com",
        device_key_fingerprint="dev_fp_persist",
        requested_scopes=("quotes:read",),
    )


def test_challenge_survives_transaction_commit_and_service_recreation():
    async def scenario():
        clock = Clock()
        with db_session() as db:
            first = WalletChallengeService(SqlAlchemyWalletChallengeRepository(db), server_pepper="pepper", now_factory=clock)
            result = await create(first)
            db.commit()
            second = WalletChallengeService(SqlAlchemyWalletChallengeRepository(db), server_pepper="pepper", now_factory=clock)
            record = await second.get_challenge(result.challenge_id)
            assert record.intent_hash == result.intent_hash
            assert record.status == WalletChallengeStatus.PENDING.value
            assert record.principal_hint_hash is None
    run(scenario())


def test_atomic_consume_marks_record_once_and_replay_fails():
    async def scenario():
        with db_session() as db:
            svc = WalletChallengeService(SqlAlchemyWalletChallengeRepository(db), server_pepper="pepper")
            result = await create(svc)
            consumed = await svc.consume_challenge(challenge_id=result.challenge_id, expected_intent_hash=result.intent_hash)
            assert consumed.status == WalletChallengeStatus.CONSUMED.value
            with pytest.raises(WalletChallengeConsumedError):
                await svc.consume_challenge(challenge_id=result.challenge_id, expected_intent_hash=result.intent_hash)
            db.commit()
            assert (await svc.get_challenge(result.challenge_id)).status == WalletChallengeStatus.CONSUMED.value
    run(scenario())


def test_expiry_query_marks_due_records_and_does_not_create_principal_or_session():
    async def scenario():
        clock = Clock()
        audit = []
        with db_session() as db:
            svc = WalletChallengeService(
                SqlAlchemyWalletChallengeRepository(db),
                server_pepper="pepper",
                now_factory=clock,
                audit_emitter=lambda e, p: audit.append((e, p)),
            )
            result = await create(svc)
            clock.advance(301)
            assert await svc.expire_due_challenges(limit=10) == 1
            record = await svc.get_challenge(result.challenge_id)
            assert record.status == WalletChallengeStatus.EXPIRED.value
            assert not hasattr(record, "session_hash")
            assert not hasattr(record, "wallet_principal")
    run(scenario())
