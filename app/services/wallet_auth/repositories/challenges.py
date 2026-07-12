"""Repository primitives for wallet challenge lifecycle persistence.

The in-memory repository is intentionally small and test-oriented. Production API
composition can provide a database-backed implementation behind the same async
protocol without changing challenge lifecycle semantics.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any, Protocol

from app.services.wallet_auth.auth_intent import canonical_intent_json
from app.services.wallet_auth.types import WalletChallengeRecord, WalletChallengeStatus


class WalletChallengeRepository(Protocol):
    async def add(self, record: WalletChallengeRecord) -> WalletChallengeRecord: ...
    async def get(self, challenge_id: str) -> WalletChallengeRecord | None: ...
    async def update(self, record: WalletChallengeRecord) -> WalletChallengeRecord: ...
    async def consume_if_pending(
        self,
        challenge_id: str,
        *,
        now: datetime,
        predicate: Callable[[WalletChallengeRecord], None],
    ) -> WalletChallengeRecord: ...
    async def expire_due(self, *, now: datetime, limit: int) -> int: ...


class InMemoryWalletChallengeRepository:
    """Atomic async repository used by unit/integration tests and adapters."""

    def __init__(self) -> None:
        self._records: dict[str, WalletChallengeRecord] = {}
        self._lock = asyncio.Lock()

    async def add(self, record: WalletChallengeRecord) -> WalletChallengeRecord:
        async with self._lock:
            if record.challenge_id in self._records:
                raise ValueError("wallet_challenge_duplicate")
            self._records[record.challenge_id] = record
            return record

    async def get(self, challenge_id: str) -> WalletChallengeRecord | None:
        async with self._lock:
            return self._records.get(challenge_id)

    async def update(self, record: WalletChallengeRecord) -> WalletChallengeRecord:
        async with self._lock:
            if record.challenge_id not in self._records:
                raise KeyError("wallet_challenge_not_found")
            self._records[record.challenge_id] = record
            return record

    async def consume_if_pending(
        self,
        challenge_id: str,
        *,
        now: datetime,
        predicate: Callable[[WalletChallengeRecord], None],
    ) -> WalletChallengeRecord:
        async with self._lock:
            record = self._records.get(challenge_id)
            if record is None:
                raise KeyError("wallet_challenge_not_found")
            if record.status != WalletChallengeStatus.PENDING.value:
                raise ValueError(f"wallet_challenge_{record.status}")
            if _aware(record.expires_at) <= _aware(now):
                expired = replace(record, status=WalletChallengeStatus.EXPIRED.value, failure_reason_code="wallet_challenge_expired")
                self._records[challenge_id] = expired
                raise TimeoutError("wallet_challenge_expired")
            predicate(record)
            consumed = replace(record, status=WalletChallengeStatus.CONSUMED.value, consumed_at=now)
            self._records[challenge_id] = consumed
            return consumed

    async def expire_due(self, *, now: datetime, limit: int) -> int:
        expired = 0
        async with self._lock:
            for challenge_id, record in list(self._records.items()):
                if expired >= limit:
                    break
                if record.status == WalletChallengeStatus.PENDING.value and _aware(record.expires_at) <= _aware(now):
                    self._records[challenge_id] = replace(
                        record,
                        status=WalletChallengeStatus.EXPIRED.value,
                        failure_reason_code="wallet_challenge_expired",
                    )
                    expired += 1
        return expired


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class SqlAlchemyWalletChallengeRepository:
    """SQLAlchemy-backed wallet challenge repository.

    This adapter persists the Prompt 9 challenge DTO without returning ORM
    objects across the service boundary. It uses the same state-machine errors
    as the in-memory repository so the service can map them safely.
    """

    def __init__(self, db: Any) -> None:
        self.db = db

    async def add(self, record: WalletChallengeRecord) -> WalletChallengeRecord:
        from app.db.models.wallet_auth import WalletAuthChallenge
        from app.services.access.crypto.hashing import sha256_prefixed

        model = WalletAuthChallenge(
            challenge_id=record.challenge_id,
            challenge_hash=record.challenge_hash,
            nonce_hash=record.nonce_hash,
            intent_hash=record.intent_hash,
            purpose=record.purpose,
            action=record.action,
            network=record.network,
            proof_type=record.proof_type,
            origin=record.origin,
            origin_hash=sha256_prefixed(record.origin),
            domain=record.domain,
            device_key_fingerprint=record.device_key_fingerprint,
            policy_hash=record.policy_hash,
            requested_scopes_json=list(record.requested_scopes),
            risk_level=record.risk_level,
            principal_hint_hash=record.principal_hint_hash,
            created_at=record.created_at,
            expires_at=record.expires_at,
            consumed_at=record.consumed_at,
            revoked_at=record.revoked_at,
            failure_reason_code=record.failure_reason_code,
            status=record.status,
            schema_epoch=record.schema_epoch,
            policy_epoch=record.policy_epoch,
            crypto_epoch=record.crypto_epoch,
            intent_json=json.loads(canonical_intent_json(record.intent)),
            signable_message_hash=sha256_prefixed(record.signable_message),
            metadata_json=None,
        )
        self.db.add(model)
        self.db.flush()
        return record

    async def get(self, challenge_id: str) -> WalletChallengeRecord | None:
        from sqlalchemy import select
        from app.db.models.wallet_auth import WalletAuthChallenge

        model = self.db.execute(select(WalletAuthChallenge).where(WalletAuthChallenge.challenge_id == challenge_id)).scalar_one_or_none()
        if model is None:
            return None
        return _record_from_model(model)

    async def update(self, record: WalletChallengeRecord) -> WalletChallengeRecord:
        from sqlalchemy import select
        from app.db.models.wallet_auth import WalletAuthChallenge
        from app.services.access.crypto.hashing import sha256_prefixed

        model = self.db.execute(select(WalletAuthChallenge).where(WalletAuthChallenge.challenge_id == record.challenge_id)).scalar_one_or_none()
        if model is None:
            raise KeyError("wallet_challenge_not_found")
        model.status = record.status
        model.consumed_at = record.consumed_at
        model.revoked_at = record.revoked_at
        model.failure_reason_code = record.failure_reason_code
        model.signable_message_hash = sha256_prefixed(record.signable_message)
        self.db.flush()
        return record

    async def consume_if_pending(
        self,
        challenge_id: str,
        *,
        now: datetime,
        predicate: Callable[[WalletChallengeRecord], None],
    ) -> WalletChallengeRecord:
        from sqlalchemy import select
        from app.db.models.wallet_auth import WalletAuthChallenge

        statement = select(WalletAuthChallenge).where(WalletAuthChallenge.challenge_id == challenge_id).with_for_update()
        model = self.db.execute(statement).scalar_one_or_none()
        if model is None:
            raise KeyError("wallet_challenge_not_found")
        record = _record_from_model(model)
        if record.status != WalletChallengeStatus.PENDING.value:
            raise ValueError(f"wallet_challenge_{record.status}")
        if _aware(record.expires_at) <= _aware(now):
            model.status = WalletChallengeStatus.EXPIRED.value
            model.failure_reason_code = "wallet_challenge_expired"
            self.db.flush()
            raise TimeoutError("wallet_challenge_expired")
        predicate(record)
        model.status = WalletChallengeStatus.CONSUMED.value
        model.consumed_at = now
        self.db.flush()
        return _record_from_model(model)

    async def expire_due(self, *, now: datetime, limit: int) -> int:
        from sqlalchemy import select
        from app.db.models.wallet_auth import WalletAuthChallenge

        statement = (
            select(WalletAuthChallenge)
            .where(WalletAuthChallenge.status == WalletChallengeStatus.PENDING.value, WalletAuthChallenge.expires_at <= now)
            .limit(limit)
        )
        models = list(self.db.execute(statement).scalars())
        for model in models:
            model.status = WalletChallengeStatus.EXPIRED.value
            model.failure_reason_code = "wallet_challenge_expired"
        self.db.flush()
        return len(models)


def _record_from_model(model: Any) -> WalletChallengeRecord:
    return WalletChallengeRecord(
        challenge_id=model.challenge_id,
        challenge_hash=model.challenge_hash,
        nonce_hash=model.nonce_hash,
        intent_hash=model.intent_hash,
        purpose=model.purpose,
        action=model.action,
        network=model.network,
        proof_type=model.proof_type,
        origin=model.origin,
        domain=model.domain,
        device_key_fingerprint=model.device_key_fingerprint,
        policy_hash=model.policy_hash,
        requested_scopes=tuple(model.requested_scopes_json or ()),
        risk_level=model.risk_level,
        principal_hint_hash=model.principal_hint_hash,
        created_at=model.created_at,
        expires_at=model.expires_at,
        consumed_at=model.consumed_at,
        revoked_at=model.revoked_at,
        failure_reason_code=model.failure_reason_code,
        status=model.status,
        schema_epoch=model.schema_epoch,
        policy_epoch=model.policy_epoch,
        crypto_epoch=model.crypto_epoch,
        intent=dict(model.intent_json or {}),
        signable_message="",
    )
