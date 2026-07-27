"""Immutable transparency domain models."""

from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from .checkpoint_types import (
    PublicationStatus,
    TransparencyCheckpointType,
    TransparencyVisibility,
    VerificationStatus,
)


def utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class TransparencyLeafCommitment:
    leaf_type: str
    object_hash: str
    object_version: int
    object_epoch: int
    event_time: datetime
    policy_hash: str
    status_commitment: str
    metadata_commitment: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["event_time"] = utc_iso(self.event_time)
        return value


@dataclass(frozen=True, slots=True)
class CheckpointStream:
    checkpoint_type: TransparencyCheckpointType
    environment: str
    issuer_family: str
    auth_domain_hash: str | None = None
    product_context: str | None = None

    def __post_init__(self) -> None:
        if self.environment not in {"production", "testnet", "signet", "regtest", "test"}:
            raise ValueError("unsupported transparency environment")
        if not self.issuer_family:
            raise ValueError("issuer family is required")


@dataclass(frozen=True, slots=True)
class TransparencyCheckpoint:
    checkpoint_id: str
    checkpoint_type: TransparencyCheckpointType
    version: int
    schema_epoch: int
    crypto_epoch: int
    policy_epoch: int
    issuer_key_id: str
    hash_suite: str
    signature_suite: str
    visibility: TransparencyVisibility
    stream_id_hash: str
    sequence_number: int
    source_count: int
    batch_start_time: datetime
    batch_end_time: datetime
    root_hash: str
    previous_checkpoint_hash: str
    checkpoint_hash: str
    created_at: datetime
    expires_at: datetime | None = None
    metadata_commitment: str | None = None
    issuer_envelope: Mapping[str, Any] | None = None
    post_quantum_signature: Mapping[str, Any] | None = None
    publication_status: PublicationStatus = PublicationStatus.INTERNAL
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    revocation_epoch: int | None = None
    auth_domain_hash: str | None = None
    environment: str = "production"
    service_instance_class: str | None = None
    retention_class: str = "security"
    supersedes_checkpoint_id: str | None = None
    emergency_reason_code: str | None = None

    def __post_init__(self) -> None:
        if self.version != 1 or min(self.schema_epoch, self.crypto_epoch, self.policy_epoch) < 1:
            raise ValueError("unsupported checkpoint version or epoch")
        if self.sequence_number < 1 or self.source_count < 0:
            raise ValueError("invalid checkpoint sequence or source count")
        if self.batch_end_time < self.batch_start_time:
            raise ValueError("invalid checkpoint batch window")
        if self.issuer_envelope is not None and not isinstance(self.issuer_envelope, MappingProxyType):
            object.__setattr__(self, "issuer_envelope", _freeze(self.issuer_envelope))
        if self.post_quantum_signature is not None and not isinstance(
            self.post_quantum_signature, MappingProxyType
        ):
            object.__setattr__(self, "post_quantum_signature", _freeze(self.post_quantum_signature))

    def with_operational_status(
        self,
        *,
        publication: PublicationStatus | None = None,
        verification: VerificationStatus | None = None,
    ) -> "TransparencyCheckpoint":
        """Only mutable operational state is represented by replacement records."""
        return replace(
            self,
            publication_status=publication or self.publication_status,
            verification_status=verification or self.verification_status,
        )


@dataclass(frozen=True, slots=True)
class MerkleProofStep:
    sibling_hash: str
    sibling_on_left: bool


@dataclass(frozen=True, slots=True)
class CheckpointVerificationResult:
    status: str
    valid: bool
    checkpoint_hash_valid: bool
    signature_valid: bool
    sequence_valid: bool
    stream_valid: bool
    root_valid: bool | None
    issuer_epoch_valid: bool
    visibility_valid: bool
    failure_reason: str | None = None
    warnings: tuple[str, ...] = ()


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(child) for key, child in value.items()})
    if isinstance(value, list | tuple):
        return tuple(_freeze(child) for child in value)
    return value
