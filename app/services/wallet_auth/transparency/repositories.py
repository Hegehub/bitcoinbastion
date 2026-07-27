"""Checkpoint repositories with immutable signed records and atomic sequencing."""

from dataclasses import dataclass
from threading import RLock

from .checkpoint_types import PublicationStatus, TransparencyVisibility, VerificationStatus
from .errors import CheckpointSequenceConflictError
from .models import TransparencyCheckpoint, TransparencyLeafCommitment


@dataclass(frozen=True, slots=True)
class StoredCheckpoint:
    checkpoint: TransparencyCheckpoint
    batch_identity_hash: str
    leaves: tuple[TransparencyLeafCommitment, ...]
    leaf_hashes: tuple[str, ...]


class InMemoryTransparencyRepository:
    """Reference repository; production SQL repository follows the same atomic contract."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._records: dict[str, StoredCheckpoint] = {}
        self._batches: dict[str, str] = {}
        self._streams: dict[str, list[str]] = {}

    def latest(self, stream_id_hash: str) -> TransparencyCheckpoint | None:
        with self._lock:
            ids = self._streams.get(stream_id_hash, [])
            return self._records[ids[-1]].checkpoint if ids else None

    def find_checkpoint_by_batch_identity(self, batch_identity_hash: str) -> StoredCheckpoint | None:
        with self._lock:
            checkpoint_id = self._batches.get(batch_identity_hash)
            return self._records.get(checkpoint_id) if checkpoint_id else None

    def finalize_signed_checkpoint(self, record: StoredCheckpoint) -> StoredCheckpoint:
        checkpoint = record.checkpoint
        if checkpoint.issuer_envelope is None:
            raise ValueError("unsigned checkpoint cannot be finalized")
        with self._lock:
            existing = self.find_checkpoint_by_batch_identity(record.batch_identity_hash)
            if existing:
                return existing
            latest = self.latest(checkpoint.stream_id_hash)
            expected = 1 if latest is None else latest.sequence_number + 1
            if checkpoint.sequence_number != expected:
                raise CheckpointSequenceConflictError("checkpoint sequence conflict")
            if latest and checkpoint.previous_checkpoint_hash != latest.checkpoint_hash:
                raise CheckpointSequenceConflictError("checkpoint previous hash conflict")
            self._records[checkpoint.checkpoint_id] = record
            self._batches[record.batch_identity_hash] = checkpoint.checkpoint_id
            self._streams.setdefault(checkpoint.stream_id_hash, []).append(checkpoint.checkpoint_id)
            return record

    def get_checkpoint(
        self, checkpoint_id: str, *, include_restricted: bool = False
    ) -> StoredCheckpoint | None:
        record = self._records.get(checkpoint_id)
        if record and not include_restricted and record.checkpoint.visibility is not TransparencyVisibility.PUBLIC_SAFE:
            return None
        return record

    def list_checkpoints(
        self, *, stream_id_hash: str | None = None, include_restricted: bool = False
    ) -> tuple[TransparencyCheckpoint, ...]:
        records = self._records.values()
        return tuple(
            record.checkpoint
            for record in records
            if (stream_id_hash is None or record.checkpoint.stream_id_hash == stream_id_hash)
            and (include_restricted or record.checkpoint.visibility is TransparencyVisibility.PUBLIC_SAFE)
        )

    def get_checkpoint_chain(self, stream_id_hash: str) -> tuple[TransparencyCheckpoint, ...]:
        return tuple(self._records[item].checkpoint for item in self._streams.get(stream_id_hash, []))

    def mark_publication_status(self, checkpoint_id: str, status: PublicationStatus) -> None:
        self._replace_status(checkpoint_id, publication=status)

    def mark_verification_status(self, checkpoint_id: str, status: VerificationStatus) -> None:
        self._replace_status(checkpoint_id, verification=status)

    def supersede_checkpoint(self, checkpoint_id: str) -> None:
        self._replace_status(checkpoint_id, publication=PublicationStatus.SUPERSEDED)

    def _replace_status(
        self,
        checkpoint_id: str,
        *,
        publication: PublicationStatus | None = None,
        verification: VerificationStatus | None = None,
    ) -> None:
        with self._lock:
            record = self._records[checkpoint_id]
            self._records[checkpoint_id] = StoredCheckpoint(
                record.checkpoint.with_operational_status(
                    publication=publication, verification=verification
                ),
                record.batch_identity_hash,
                record.leaves,
                record.leaf_hashes,
            )
