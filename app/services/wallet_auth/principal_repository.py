"""Repository boundary for wallet principals.

The in-memory implementation is used by unit tests and local composition. The
SQLAlchemy adapter follows the existing wallet-auth model shape without exposing
ORM rows through service results.
"""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any, Protocol

from app.domain.wallet_auth.networks import WalletNetwork
from app.domain.wallet_auth.principals import WalletPrincipalStatus
from app.domain.wallet_auth.proofs import WalletProofType, WalletVerificationStrength
from app.services.wallet_auth.principal_types import (
    PrincipalType,
    VerifiedWalletProof,
    WalletPrincipalRecord,
    WalletProofAssociation,
    max_strength,
)


class WalletPrincipalRepositoryConflictError(ValueError):
    """Raised when a repository detects a safe uniqueness conflict."""


class WalletPrincipalRepository(Protocol):
    async def get_by_principal_hash(self, principal_hash: str) -> WalletPrincipalRecord | None: ...
    async def get_by_wallet_commitment(
        self, *, principal_type: PrincipalType, wallet_commitment: str, network: WalletNetwork
    ) -> WalletPrincipalRecord | None: ...
    async def create(self, record: WalletPrincipalRecord, *, wallet_commitment: str) -> WalletPrincipalRecord: ...
    async def update(self, record: WalletPrincipalRecord) -> WalletPrincipalRecord: ...
    async def add_proof_association(self, association: WalletProofAssociation) -> bool: ...
    async def list_proof_methods(self, principal_hash: str) -> tuple[WalletProofType, ...]: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...


class InMemoryWalletPrincipalRepository:
    """Atomic in-memory principal repository for service and security tests."""

    def __init__(self) -> None:
        self._principals: dict[str, WalletPrincipalRecord] = {}
        self._wallet_index: dict[tuple[str, str, str], str] = {}
        self._proofs: dict[str, list[WalletProofAssociation]] = {}
        self._proof_hashes: set[tuple[str, str]] = set()
        self._lock = asyncio.Lock()

    async def get_by_principal_hash(self, principal_hash: str) -> WalletPrincipalRecord | None:
        async with self._lock:
            return self._principals.get(principal_hash)

    async def get_by_wallet_commitment(
        self, *, principal_type: PrincipalType, wallet_commitment: str, network: WalletNetwork
    ) -> WalletPrincipalRecord | None:
        async with self._lock:
            key = (principal_type.value, network.value, wallet_commitment)
            principal_hash = self._wallet_index.get(key)
            return self._principals.get(principal_hash) if principal_hash else None

    async def create(self, record: WalletPrincipalRecord, *, wallet_commitment: str) -> WalletPrincipalRecord:
        async with self._lock:
            if record.principal_hash in self._principals:
                raise WalletPrincipalRepositoryConflictError("wallet_principal_duplicate")
            if record.network is None:
                raise WalletPrincipalRepositoryConflictError("wallet_principal_network_required")
            key = (record.principal_type.value, record.network.value, wallet_commitment)
            if key in self._wallet_index:
                raise WalletPrincipalRepositoryConflictError("wallet_principal_wallet_commitment_duplicate")
            self._principals[record.principal_hash] = record
            self._wallet_index[key] = record.principal_hash
            self._proofs.setdefault(record.principal_hash, [])
            return record

    async def update(self, record: WalletPrincipalRecord) -> WalletPrincipalRecord:
        async with self._lock:
            if record.principal_hash not in self._principals:
                raise KeyError("wallet_principal_not_found")
            self._principals[record.principal_hash] = record
            return record

    async def add_proof_association(self, association: WalletProofAssociation) -> bool:
        async with self._lock:
            if association.principal_hash not in self._principals:
                raise KeyError("wallet_principal_not_found")
            key = (association.principal_hash, association.proof_hash)
            if key in self._proof_hashes:
                return False
            self._proof_hashes.add(key)
            self._proofs.setdefault(association.principal_hash, []).append(association)
            return True

    async def list_proof_methods(self, principal_hash: str) -> tuple[WalletProofType, ...]:
        async with self._lock:
            proofs = self._proofs.get(principal_hash, [])
            return tuple(dict.fromkeys(proof.proof_type for proof in proofs))

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


class SqlAlchemyWalletPrincipalRepository:
    """SQLAlchemy-backed repository for the existing wallet principal models."""

    def __init__(self, db: Any) -> None:
        self.db = db

    async def get_by_principal_hash(self, principal_hash: str) -> WalletPrincipalRecord | None:
        from sqlalchemy import select
        from app.db.models.wallet_auth import WalletPrincipal

        row = self.db.execute(
            select(WalletPrincipal).where(WalletPrincipal.principal_hash == principal_hash)
        ).scalar_one_or_none()
        return _record_from_model(row) if row is not None else None

    async def get_by_wallet_commitment(
        self, *, principal_type: PrincipalType, wallet_commitment: str, network: WalletNetwork
    ) -> WalletPrincipalRecord | None:
        from sqlalchemy import select
        from app.db.models.wallet_auth import WalletPrincipal

        row = self.db.execute(
            select(WalletPrincipal).where(
                WalletPrincipal.principal_type == principal_type.value,
                WalletPrincipal.network == network.value,
                WalletPrincipal.address_hash == wallet_commitment,
            )
        ).scalar_one_or_none()
        return _record_from_model(row) if row is not None else None

    async def create(self, record: WalletPrincipalRecord, *, wallet_commitment: str) -> WalletPrincipalRecord:
        from sqlalchemy.exc import IntegrityError
        from app.db.models.wallet_auth import WalletPrincipal

        row = WalletPrincipal(
            principal_hash=record.principal_hash,
            principal_type=record.principal_type.value,
            status=record.status.value,
            verification_strength=record.current_proof_strength.value,
            primary_proof_method=record.primary_proof_method.value,
            network=record.network.value if record.network else None,
            address_hash=wallet_commitment,
            script_pubkey_hash=record.script_pubkey_hash,
            policy_epoch=record.policy_epoch,
            crypto_epoch=record.crypto_epoch,
            schema_epoch=record.schema_epoch,
            created_at=record.created_at,
            updated_at=record.updated_at,
            last_verified_at=record.last_verified_at,
            revoked_at=record.revoked_at,
            metadata_json=dict(record.metadata),
        )
        self.db.add(row)
        try:
            self.db.flush()
        except IntegrityError as exc:
            raise WalletPrincipalRepositoryConflictError("wallet_principal_duplicate") from exc
        return record

    async def update(self, record: WalletPrincipalRecord) -> WalletPrincipalRecord:
        from sqlalchemy import select
        from app.db.models.wallet_auth import WalletPrincipal

        row = self.db.execute(
            select(WalletPrincipal).where(WalletPrincipal.principal_hash == record.principal_hash).with_for_update()
        ).scalar_one_or_none()
        if row is None:
            raise KeyError("wallet_principal_not_found")
        row.status = record.status.value
        row.verification_strength = record.current_proof_strength.value
        row.primary_proof_method = record.primary_proof_method.value
        row.updated_at = record.updated_at
        row.last_verified_at = record.last_verified_at
        row.revoked_at = record.revoked_at
        row.metadata_json = dict(record.metadata)
        self.db.flush()
        return record

    async def add_proof_association(self, association: WalletProofAssociation) -> bool:
        from sqlalchemy import select
        from app.db.models.wallet_auth import WalletPrincipal, WalletProof

        existing = self.db.execute(
            select(WalletProof).where(
                WalletProof.principal_hash == association.principal_hash,
                WalletProof.proof_hash == association.proof_hash,
            )
        ).scalar_one_or_none()
        if existing is not None:
            return False
        principal = self.db.execute(
            select(WalletPrincipal).where(WalletPrincipal.principal_hash == association.principal_hash)
        ).scalar_one_or_none()
        if principal is None:
            raise KeyError("wallet_principal_not_found")
        row = WalletProof(
            principal_id=principal.id,
            principal_hash=association.principal_hash,
            proof_type=association.proof_type.value,
            proof_hash=association.proof_hash,
            action=association.action,
            verification_strength=association.verification_strength.value,
            script_type=association.script_type.value,
            network=association.network.value,
            policy_hash=association.policy_hash,
            status="verified",
            verified_at=association.verified_at,
            metadata_json={
                "verifier_name": association.verifier_name,
                "verifier_version": association.verifier_version,
                "limitations": list(association.limitations),
                "policy_hints": list(association.policy_hints),
            },
        )
        self.db.add(row)
        self.db.flush()
        return True

    async def list_proof_methods(self, principal_hash: str) -> tuple[WalletProofType, ...]:
        from sqlalchemy import select
        from app.db.models.wallet_auth import WalletProof

        rows = self.db.execute(
            select(WalletProof.proof_type).where(WalletProof.principal_hash == principal_hash)
        ).scalars()
        return tuple(dict.fromkeys(WalletProofType(value) for value in rows))

    async def commit(self) -> None:
        self.db.commit()

    async def rollback(self) -> None:
        self.db.rollback()


def build_principal_record(
    *,
    principal_hash: str,
    proof: VerifiedWalletProof,
    now: datetime,
    status: WalletPrincipalStatus = WalletPrincipalStatus.ACTIVE,
) -> WalletPrincipalRecord:
    high_at = now if proof.verification_strength in {
        WalletVerificationStrength.HIGH_ASSURANCE,
        WalletVerificationStrength.SOVEREIGN,
    } else None
    return WalletPrincipalRecord(
        principal_hash=principal_hash,
        principal_type=PrincipalType.BITCOIN_WALLET_PRINCIPAL,
        status=status,
        network=proof.network,
        primary_proof_method=proof.proof_type,
        current_proof_strength=proof.verification_strength,
        highest_verified_strength=proof.verification_strength,
        address_hash=proof.wallet_identifier_commitment,
        script_pubkey_hash=proof.script_pubkey_hash,
        schema_epoch=1,
        crypto_epoch=1,
        policy_epoch=1,
        created_at=now,
        updated_at=now,
        last_verified_at=proof.verified_at,
        last_high_assurance_at=high_at,
        metadata={"verifier_name": proof.verifier_name, "verifier_version": proof.verifier_version},
    )


def apply_successful_verification(
    *, record: WalletPrincipalRecord, proof: VerifiedWalletProof, now: datetime
) -> WalletPrincipalRecord:
    high_at = record.last_high_assurance_at
    if proof.verification_strength in {WalletVerificationStrength.HIGH_ASSURANCE, WalletVerificationStrength.SOVEREIGN}:
        high_at = proof.verified_at
    return replace(
        record,
        primary_proof_method=proof.proof_type,
        current_proof_strength=proof.verification_strength,
        highest_verified_strength=max_strength(record.highest_verified_strength, proof.verification_strength),
        last_verified_at=proof.verified_at,
        last_high_assurance_at=high_at,
        updated_at=now,
        metadata={**dict(record.metadata), "verifier_name": proof.verifier_name, "verifier_version": proof.verifier_version},
    )


def _record_from_model(row: Any) -> WalletPrincipalRecord:
    metadata = row.metadata_json or {}
    return WalletPrincipalRecord(
        principal_hash=row.principal_hash,
        principal_type=PrincipalType(row.principal_type),
        status=WalletPrincipalStatus(row.status),
        network=WalletNetwork(row.network) if row.network else None,
        primary_proof_method=WalletProofType(row.primary_proof_method),
        current_proof_strength=WalletVerificationStrength(row.verification_strength),
        highest_verified_strength=WalletVerificationStrength(
            metadata.get("highest_verified_strength", row.verification_strength)
        ),
        address_hash=row.address_hash,
        script_pubkey_hash=row.script_pubkey_hash,
        schema_epoch=row.schema_epoch,
        crypto_epoch=row.crypto_epoch,
        policy_epoch=row.policy_epoch,
        created_at=_aware(row.created_at),
        updated_at=_aware(row.updated_at),
        last_verified_at=_aware(row.last_verified_at) if row.last_verified_at else None,
        last_high_assurance_at=None,
        revoked_at=_aware(row.revoked_at) if row.revoked_at else None,
        metadata=metadata,
    )


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)
