"""Repository boundary for wallet device bindings."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from typing import Any, Protocol

from app.domain.wallet_auth.devices import WalletDeviceBindingMethod, WalletDeviceClass, WalletDeviceStatus
from app.domain.wallet_auth.networks import WalletNetwork
from app.domain.wallet_auth.proofs import WalletProofType, WalletVerificationStrength


@dataclass(frozen=True, slots=True)
class WalletDeviceRecord:
    id: int
    principal_hash: str
    device_id_hash: str
    device_key_fingerprint: str
    device_public_key_b64: str
    key_algorithm: str
    device_class: WalletDeviceClass
    binding_method: WalletDeviceBindingMethod
    proof_type: WalletProofType
    verification_strength: WalletVerificationStrength
    status: WalletDeviceStatus
    risk_score: int
    risk_level: str
    risk_reason_codes: tuple[str, ...]
    network: WalletNetwork | None = None
    auth_domain: str | None = None
    attestation_type: str | None = None
    attestation_status: str | None = None
    client_name: str | None = None
    client_version: str | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    last_proof_at: datetime | None = None
    key_rotated_at: datetime | None = None
    suspended_at: datetime | None = None
    revoked_at: datetime | None = None
    revocation_reason_code: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def safe_summary(self) -> dict[str, object]:
        return {
            "id": self.id,
            "principal_hash": self.principal_hash,
            "device_id_hash": self.device_id_hash,
            "device_key_fingerprint": self.device_key_fingerprint,
            "key_algorithm": self.key_algorithm,
            "device_class": self.device_class.value,
            "binding_method": self.binding_method.value,
            "proof_type": self.proof_type.value,
            "verification_strength": self.verification_strength.value,
            "status": self.status.value,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "risk_reason_codes": list(self.risk_reason_codes),
        }


class WalletDeviceRepositoryConflictError(ValueError):
    """Raised when a device binding uniqueness rule is violated."""


class WalletDeviceRepository(Protocol):
    async def create_device(self, record: WalletDeviceRecord) -> WalletDeviceRecord: ...
    async def get_by_id(self, device_id: int) -> WalletDeviceRecord | None: ...
    async def get_by_principal_and_fingerprint(
        self, *, principal_hash: str, device_key_fingerprint: str
    ) -> WalletDeviceRecord | None: ...
    async def get_by_device_id_hash(self, device_id_hash: str) -> WalletDeviceRecord | None: ...
    async def list_for_principal(self, principal_hash: str, *, limit: int = 100) -> tuple[WalletDeviceRecord, ...]: ...
    async def update_last_seen(self, *, principal_hash: str, device_key_fingerprint: str, seen_at: datetime) -> WalletDeviceRecord: ...
    async def update_status(
        self,
        *,
        principal_hash: str,
        device_key_fingerprint: str,
        status: WalletDeviceStatus,
        reason_code: str | None,
        now: datetime,
    ) -> WalletDeviceRecord: ...
    async def rotate_key(
        self,
        *,
        principal_hash: str,
        old_fingerprint: str,
        new_fingerprint: str,
        new_public_key_b64: str,
        key_algorithm: str,
        now: datetime,
    ) -> WalletDeviceRecord: ...
    async def count_active_devices(self, principal_hash: str) -> int: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...


class InMemoryWalletDeviceRepository:
    def __init__(self) -> None:
        self._records: dict[int, WalletDeviceRecord] = {}
        self._principal_fingerprint_index: dict[tuple[str, str], int] = {}
        self._device_id_index: dict[str, int] = {}
        self._next_id = 1
        self._lock = asyncio.Lock()

    async def create_device(self, record: WalletDeviceRecord) -> WalletDeviceRecord:
        async with self._lock:
            existing_id = self._principal_fingerprint_index.get((record.principal_hash, record.device_key_fingerprint))
            if existing_id is not None:
                return self._records[existing_id]
            other_id = self._device_id_index.get(record.device_id_hash)
            if other_id is not None:
                other = self._records[other_id]
                if other.principal_hash != record.principal_hash:
                    raise WalletDeviceRepositoryConflictError("wallet_device_binding_conflict")
                return other
            assigned = replace(record, id=self._next_id)
            self._next_id += 1
            self._records[assigned.id] = assigned
            self._principal_fingerprint_index[(assigned.principal_hash, assigned.device_key_fingerprint)] = assigned.id
            self._device_id_index[assigned.device_id_hash] = assigned.id
            return assigned

    async def get_by_id(self, device_id: int) -> WalletDeviceRecord | None:
        async with self._lock:
            return self._records.get(device_id)

    async def get_by_principal_and_fingerprint(
        self, *, principal_hash: str, device_key_fingerprint: str
    ) -> WalletDeviceRecord | None:
        async with self._lock:
            record_id = self._principal_fingerprint_index.get((principal_hash, device_key_fingerprint))
            return self._records.get(record_id) if record_id is not None else None

    async def get_by_device_id_hash(self, device_id_hash: str) -> WalletDeviceRecord | None:
        async with self._lock:
            record_id = self._device_id_index.get(device_id_hash)
            return self._records.get(record_id) if record_id is not None else None

    async def list_for_principal(self, principal_hash: str, *, limit: int = 100) -> tuple[WalletDeviceRecord, ...]:
        async with self._lock:
            return tuple(record for record in self._records.values() if record.principal_hash == principal_hash)[:limit]

    async def update_last_seen(self, *, principal_hash: str, device_key_fingerprint: str, seen_at: datetime) -> WalletDeviceRecord:
        async with self._lock:
            record = self._get_locked(principal_hash, device_key_fingerprint)
            if record.status is WalletDeviceStatus.REVOKED:
                return record
            updated = replace(record, last_seen_at=seen_at, updated_at=seen_at)
            self._records[record.id] = updated
            return updated

    async def update_status(
        self,
        *,
        principal_hash: str,
        device_key_fingerprint: str,
        status: WalletDeviceStatus,
        reason_code: str | None,
        now: datetime,
    ) -> WalletDeviceRecord:
        async with self._lock:
            record = self._get_locked(principal_hash, device_key_fingerprint)
            updated = replace(
                record,
                status=status,
                suspended_at=now if status is WalletDeviceStatus.SUSPENDED else record.suspended_at,
                revoked_at=now if status is WalletDeviceStatus.REVOKED else record.revoked_at,
                revocation_reason_code=reason_code if status is WalletDeviceStatus.REVOKED else record.revocation_reason_code,
                updated_at=now,
            )
            self._records[record.id] = updated
            return updated

    async def rotate_key(
        self,
        *,
        principal_hash: str,
        old_fingerprint: str,
        new_fingerprint: str,
        new_public_key_b64: str,
        key_algorithm: str,
        now: datetime,
    ) -> WalletDeviceRecord:
        async with self._lock:
            record = self._get_locked(principal_hash, old_fingerprint)
            if (principal_hash, new_fingerprint) in self._principal_fingerprint_index:
                raise WalletDeviceRepositoryConflictError("wallet_device_key_reuse")
            old_key = (principal_hash, old_fingerprint)
            del self._principal_fingerprint_index[old_key]
            self._principal_fingerprint_index[(principal_hash, new_fingerprint)] = record.id
            history = _history_list(record.metadata.get("previous_key_fingerprints", []))
            history.append(old_fingerprint)
            updated = replace(
                record,
                device_key_fingerprint=new_fingerprint,
                device_public_key_b64=new_public_key_b64,
                key_algorithm=key_algorithm,
                key_rotated_at=now,
                updated_at=now,
                metadata={**record.metadata, "previous_key_fingerprints": history},
            )
            self._records[record.id] = updated
            return updated

    async def count_active_devices(self, principal_hash: str) -> int:
        async with self._lock:
            return sum(
                1
                for record in self._records.values()
                if record.principal_hash == principal_hash and record.status is WalletDeviceStatus.ACTIVE
            )

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None

    def _get_locked(self, principal_hash: str, fingerprint: str) -> WalletDeviceRecord:
        record_id = self._principal_fingerprint_index.get((principal_hash, fingerprint))
        if record_id is None:
            raise KeyError("wallet_device_not_found")
        return self._records[record_id]


class SqlAlchemyWalletDeviceRepository:
    """SQLAlchemy adapter storing extended fields in metadata_json until migrations evolve."""

    def __init__(self, db: Any) -> None:
        self.db = db

    async def create_device(self, record: WalletDeviceRecord) -> WalletDeviceRecord:
        from sqlalchemy import select
        from app.db.models.wallet_auth import WalletDevice, WalletPrincipal

        existing = await self.get_by_principal_and_fingerprint(
            principal_hash=record.principal_hash, device_key_fingerprint=record.device_key_fingerprint
        )
        if existing is not None:
            return existing
        principal = self.db.execute(
            select(WalletPrincipal).where(WalletPrincipal.principal_hash == record.principal_hash)
        ).scalar_one_or_none()
        if principal is None:
            raise KeyError("wallet_principal_not_found")
        row = WalletDevice(
            principal_id=principal.id,
            principal_hash=record.principal_hash,
            device_id_hash=record.device_id_hash,
            device_key_fingerprint=record.device_key_fingerprint,
            device_class=record.device_class.value,
            binding_method=record.binding_method.value,
            status=record.status.value,
            risk_score=record.risk_score,
            first_seen_at=record.first_seen_at,
            last_seen_at=record.last_seen_at,
            revoked_at=record.revoked_at,
            created_at=record.created_at or _now(),
            updated_at=record.updated_at or _now(),
            metadata_json=_metadata(record),
        )
        self.db.add(row)
        self.db.flush()
        return replace(record, id=row.id)

    async def get_by_id(self, device_id: int) -> WalletDeviceRecord | None:
        from sqlalchemy import select
        from app.db.models.wallet_auth import WalletDevice

        row = self.db.execute(select(WalletDevice).where(WalletDevice.id == device_id)).scalar_one_or_none()
        return _from_model(row) if row is not None else None

    async def get_by_principal_and_fingerprint(
        self, *, principal_hash: str, device_key_fingerprint: str
    ) -> WalletDeviceRecord | None:
        from sqlalchemy import select
        from app.db.models.wallet_auth import WalletDevice

        row = self.db.execute(
            select(WalletDevice).where(
                WalletDevice.principal_hash == principal_hash,
                WalletDevice.device_key_fingerprint == device_key_fingerprint,
            )
        ).scalar_one_or_none()
        return _from_model(row) if row is not None else None

    async def get_by_device_id_hash(self, device_id_hash: str) -> WalletDeviceRecord | None:
        from sqlalchemy import select
        from app.db.models.wallet_auth import WalletDevice

        row = self.db.execute(select(WalletDevice).where(WalletDevice.device_id_hash == device_id_hash)).scalar_one_or_none()
        return _from_model(row) if row is not None else None

    async def list_for_principal(self, principal_hash: str, *, limit: int = 100) -> tuple[WalletDeviceRecord, ...]:
        from sqlalchemy import select
        from app.db.models.wallet_auth import WalletDevice

        rows = self.db.execute(
            select(WalletDevice).where(WalletDevice.principal_hash == principal_hash).limit(limit)
        ).scalars()
        return tuple(_from_model(row) for row in rows)

    async def update_last_seen(self, *, principal_hash: str, device_key_fingerprint: str, seen_at: datetime) -> WalletDeviceRecord:
        row = await self.get_by_principal_and_fingerprint(principal_hash=principal_hash, device_key_fingerprint=device_key_fingerprint)
        if row is None:
            raise KeyError("wallet_device_not_found")
        updated = replace(row, last_seen_at=seen_at, updated_at=seen_at)
        return await self._save_existing(updated)

    async def update_status(
        self,
        *,
        principal_hash: str,
        device_key_fingerprint: str,
        status: WalletDeviceStatus,
        reason_code: str | None,
        now: datetime,
    ) -> WalletDeviceRecord:
        row = await self.get_by_principal_and_fingerprint(principal_hash=principal_hash, device_key_fingerprint=device_key_fingerprint)
        if row is None:
            raise KeyError("wallet_device_not_found")
        updated = replace(
            row,
            status=status,
            suspended_at=now if status is WalletDeviceStatus.SUSPENDED else row.suspended_at,
            revoked_at=now if status is WalletDeviceStatus.REVOKED else row.revoked_at,
            revocation_reason_code=reason_code if status is WalletDeviceStatus.REVOKED else row.revocation_reason_code,
            updated_at=now,
        )
        return await self._save_existing(updated)

    async def rotate_key(
        self,
        *,
        principal_hash: str,
        old_fingerprint: str,
        new_fingerprint: str,
        new_public_key_b64: str,
        key_algorithm: str,
        now: datetime,
    ) -> WalletDeviceRecord:
        row = await self.get_by_principal_and_fingerprint(principal_hash=principal_hash, device_key_fingerprint=old_fingerprint)
        if row is None:
            raise KeyError("wallet_device_not_found")
        history = _history_list(row.metadata.get("previous_key_fingerprints", []))
        history.append(old_fingerprint)
        updated = replace(
            row,
            device_key_fingerprint=new_fingerprint,
            device_public_key_b64=new_public_key_b64,
            key_algorithm=key_algorithm,
            key_rotated_at=now,
            updated_at=now,
            metadata={**row.metadata, "previous_key_fingerprints": history},
        )
        return await self._save_existing(updated)

    async def count_active_devices(self, principal_hash: str) -> int:
        return sum(1 for row in await self.list_for_principal(principal_hash) if row.status is WalletDeviceStatus.ACTIVE)

    async def commit(self) -> None:
        self.db.commit()

    async def rollback(self) -> None:
        self.db.rollback()

    async def _save_existing(self, record: WalletDeviceRecord) -> WalletDeviceRecord:
        from sqlalchemy import select
        from app.db.models.wallet_auth import WalletDevice

        row = self.db.execute(select(WalletDevice).where(WalletDevice.id == record.id)).scalar_one()
        row.device_key_fingerprint = record.device_key_fingerprint
        row.status = record.status.value
        row.risk_score = record.risk_score
        row.last_seen_at = record.last_seen_at
        row.revoked_at = record.revoked_at
        row.updated_at = record.updated_at
        row.metadata_json = _metadata(record)
        self.db.flush()
        return record


def _metadata(record: WalletDeviceRecord) -> dict[str, object]:
    return {
        **record.metadata,
        "device_public_key_b64": record.device_public_key_b64,
        "key_algorithm": record.key_algorithm,
        "proof_type": record.proof_type.value,
        "verification_strength": record.verification_strength.value,
        "network": record.network.value if record.network else None,
        "auth_domain": record.auth_domain,
        "risk_level": record.risk_level,
        "risk_reason_codes": list(record.risk_reason_codes),
        "last_proof_at": record.last_proof_at.isoformat() if record.last_proof_at else None,
        "key_rotated_at": record.key_rotated_at.isoformat() if record.key_rotated_at else None,
        "suspended_at": record.suspended_at.isoformat() if record.suspended_at else None,
        "revocation_reason_code": record.revocation_reason_code,
    }


def _from_model(row: Any) -> WalletDeviceRecord:
    metadata = row.metadata_json or {}
    return WalletDeviceRecord(
        id=row.id,
        principal_hash=row.principal_hash,
        device_id_hash=row.device_id_hash,
        device_key_fingerprint=row.device_key_fingerprint,
        device_public_key_b64=str(metadata.get("device_public_key_b64", "")),
        key_algorithm=str(metadata.get("key_algorithm", "ed25519")),
        device_class=WalletDeviceClass(row.device_class),
        binding_method=WalletDeviceBindingMethod(row.binding_method),
        proof_type=WalletProofType(str(metadata.get("proof_type", WalletProofType.BIP322.value))),
        verification_strength=WalletVerificationStrength(str(metadata.get("verification_strength", "compatibility"))),
        status=WalletDeviceStatus(row.status),
        risk_score=row.risk_score or 0,
        risk_level=str(metadata.get("risk_level", "unknown")),
        risk_reason_codes=tuple(metadata.get("risk_reason_codes", [])),
        network=WalletNetwork(metadata["network"]) if metadata.get("network") else None,
        auth_domain=metadata.get("auth_domain"),
        first_seen_at=_aware(row.first_seen_at) if row.first_seen_at else None,
        last_seen_at=_aware(row.last_seen_at) if row.last_seen_at else None,
        last_proof_at=_parse_dt(metadata.get("last_proof_at")),
        key_rotated_at=_parse_dt(metadata.get("key_rotated_at")),
        suspended_at=_parse_dt(metadata.get("suspended_at")),
        revoked_at=_aware(row.revoked_at) if row.revoked_at else None,
        revocation_reason_code=metadata.get("revocation_reason_code"),
        created_at=_aware(row.created_at),
        updated_at=_aware(row.updated_at),
        metadata={k: v for k, v in metadata.items() if k not in {"device_public_key_b64"}},
    )


def _parse_dt(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    return datetime.fromisoformat(value)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _now() -> datetime:
    return datetime.now(UTC)


def _history_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, tuple):
        return [str(item) for item in value]
    return []
