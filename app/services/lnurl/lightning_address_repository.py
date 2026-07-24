"""Repository boundary for Lightning Address records."""
from __future__ import annotations

import threading
from collections.abc import Mapping
from dataclasses import replace
from datetime import UTC, datetime
from typing import Protocol, Any

from app.domain.lnurl.lightning_address import (
    LightningAddressRecord,
    LightningAddressStatus,
    LightningAddressTargetType,
    build_lightning_address,
)


class LightningAddressRepositoryError(ValueError):
    reason_code = "lightning_address_repository_error"


class LightningAddressNotFoundError(LightningAddressRepositoryError):
    reason_code = "lightning_address_not_found"


class LightningAddressConflictError(LightningAddressRepositoryError):
    reason_code = "lightning_address_conflict"


class LightningAddressReservedError(LightningAddressRepositoryError):
    reason_code = "lightning_address_reserved"


class LightningAddressRepository(Protocol):
    def create_address(self, record: LightningAddressRecord) -> LightningAddressRecord: ...
    def get_by_address(self, normalized_address: str) -> LightningAddressRecord | None: ...
    def get_by_local_part_and_domain(self, local_part: str, domain: str) -> LightningAddressRecord | None: ...
    def list_by_target(self, target_type: LightningAddressTargetType | str, target_reference_hash: str) -> tuple[LightningAddressRecord, ...]: ...
    def list_by_domain(self, domain: str) -> tuple[LightningAddressRecord, ...]: ...
    def update_address(self, address_id: str, changes: Mapping[str, Any]) -> LightningAddressRecord: ...
    def suspend_address(self, address_id: str, reason: str) -> LightningAddressRecord: ...
    def reactivate_address(self, address_id: str) -> LightningAddressRecord: ...
    def disable_address(self, address_id: str, reason: str) -> LightningAddressRecord: ...
    def expire_address(self, address_id: str) -> LightningAddressRecord: ...
    def address_exists(self, normalized_address: str) -> bool: ...
    def reserve_local_part(self, local_part: str, domain: str) -> None: ...
    def release_local_part(self, local_part: str, domain: str) -> None: ...


class InMemoryLightningAddressRepository:
    def __init__(self) -> None:
        self._records: dict[str, LightningAddressRecord] = {}
        self._by_address: dict[str, str] = {}
        self._reserved: set[str] = set()
        self._lock = threading.Lock()

    def create_address(self, record: LightningAddressRecord) -> LightningAddressRecord:
        with self._lock:
            existing_id = self._by_address.get(record.normalized_address)
            if existing_id:
                existing = self._records[existing_id]
                if existing == record:
                    return existing
                raise LightningAddressConflictError("lightning_address_conflict")
            if record.normalized_address in self._reserved:
                raise LightningAddressReservedError("lightning_address_reserved")
            self._records[record.address_id] = record
            self._by_address[record.normalized_address] = record.address_id
            return record

    def get_by_address(self, normalized_address: str) -> LightningAddressRecord | None:
        with self._lock:
            record_id = self._by_address.get(normalized_address)
            return self._records.get(record_id) if record_id else None

    def get_by_local_part_and_domain(self, local_part: str, domain: str) -> LightningAddressRecord | None:
        return self.get_by_address(build_lightning_address(local_part, domain))

    def list_by_target(self, target_type: LightningAddressTargetType | str, target_reference_hash: str) -> tuple[LightningAddressRecord, ...]:
        target = LightningAddressTargetType(target_type)
        with self._lock:
            return tuple(record for record in self._records.values() if record.target_type is target and record.target_reference_hash == target_reference_hash)

    def list_by_domain(self, domain: str) -> tuple[LightningAddressRecord, ...]:
        with self._lock:
            return tuple(record for record in self._records.values() if record.domain == domain)

    def update_address(self, address_id: str, changes: Mapping[str, Any]) -> LightningAddressRecord:
        with self._lock:
            record = self._records.get(address_id)
            if record is None:
                raise LightningAddressNotFoundError("lightning_address_not_found")
            forbidden = {"address_id", "normalized_address", "local_part", "domain"}
            safe_changes = {key: value for key, value in changes.items() if key not in forbidden}
            updated = replace(record, **safe_changes, updated_at=datetime.now(UTC), version=record.version + 1)
            self._records[address_id] = updated
            return updated

    def suspend_address(self, address_id: str, reason: str) -> LightningAddressRecord:
        return self.update_address(address_id, {"status": LightningAddressStatus.SUSPENDED})

    def reactivate_address(self, address_id: str) -> LightningAddressRecord:
        return self.update_address(address_id, {"status": LightningAddressStatus.ACTIVE})

    def disable_address(self, address_id: str, reason: str) -> LightningAddressRecord:
        return self.update_address(address_id, {"status": LightningAddressStatus.DISABLED})

    def expire_address(self, address_id: str) -> LightningAddressRecord:
        return self.update_address(address_id, {"status": LightningAddressStatus.EXPIRED})

    def address_exists(self, normalized_address: str) -> bool:
        with self._lock:
            return normalized_address in self._by_address

    def reserve_local_part(self, local_part: str, domain: str) -> None:
        normalized = build_lightning_address(local_part, domain)
        with self._lock:
            if normalized in self._by_address or normalized in self._reserved:
                raise LightningAddressConflictError("lightning_address_conflict")
            self._reserved.add(normalized)

    def release_local_part(self, local_part: str, domain: str) -> None:
        normalized = build_lightning_address(local_part, domain)
        with self._lock:
            self._reserved.discard(normalized)


__all__ = [
    "LightningAddressRepository",
    "InMemoryLightningAddressRepository",
    "LightningAddressRepositoryError",
    "LightningAddressNotFoundError",
    "LightningAddressConflictError",
    "LightningAddressReservedError",
]
