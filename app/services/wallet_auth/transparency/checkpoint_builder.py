"""Idempotent checkpoint builder with per-stream hash chaining."""

from dataclasses import replace
from datetime import UTC, datetime
from typing import Any, Callable, Sequence

from app.services.access.crypto.hashing import canonical_json, sha256_prefixed

from .canonicalization import hash_checkpoint_payload, hash_transparency_leaf
from .checkpoint_signer import TransparencyCheckpointSigner
from .checkpoint_types import PERMITTED_LEAF_TYPES, TransparencyVisibility, default_visibility
from .errors import InvalidCheckpointSourceError
from .merkle import build_merkle_root, deterministic_leaf_ordering
from .models import CheckpointStream, TransparencyCheckpoint, TransparencyLeafCommitment
from .privacy import validate_source_metadata
from .repositories import InMemoryTransparencyRepository, StoredCheckpoint

GENESIS_CHECKPOINT_HASH = "GENESIS"


def stream_id_hash(stream: CheckpointStream) -> str:
    return sha256_prefixed(
        "BASTION_TRANSPARENCY_STREAM_V1\x00"
        + canonical_json(
            {
                "checkpoint_type": stream.checkpoint_type.value,
                "environment": stream.environment,
                "issuer_family": stream.issuer_family,
                "auth_domain_hash": stream.auth_domain_hash,
                "product_context": stream.product_context,
            }
        )
    )


class TransparencyCheckpointBuilder:
    def __init__(
        self,
        *,
        repository: InMemoryTransparencyRepository,
        signer: TransparencyCheckpointSigner,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        audit_sink: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> None:
        self.repository, self.signer, self.clock, self.audit_sink = repository, signer, clock, audit_sink

    def validate_checkpoint_sources(
        self,
        stream: CheckpointStream,
        commitments: Sequence[TransparencyLeafCommitment],
        visibility: TransparencyVisibility,
    ) -> None:
        allowed = PERMITTED_LEAF_TYPES[stream.checkpoint_type]
        for leaf in commitments:
            if leaf.leaf_type not in allowed:
                raise InvalidCheckpointSourceError("source is not permitted for checkpoint type")
            validate_source_metadata(leaf.to_dict(), public_safe=visibility is TransparencyVisibility.PUBLIC_SAFE)

    def build_checkpoint_from_commitments(
        self,
        *,
        stream: CheckpointStream,
        commitments: Sequence[TransparencyLeafCommitment],
        batch_identity_hash: str,
        policy_epoch: int = 1,
        crypto_epoch: int = 1,
        schema_epoch: int = 1,
        visibility: TransparencyVisibility | None = None,
        revocation_epoch: int | None = None,
        metadata_commitment: str | None = None,
    ) -> StoredCheckpoint:
        existing = self.repository.find_checkpoint_by_batch_identity(batch_identity_hash)
        if existing:
            return existing
        visibility = visibility or default_visibility(stream.checkpoint_type)
        self.validate_checkpoint_sources(stream, commitments, visibility)
        ordered_leaves = tuple(
            sorted(commitments, key=lambda leaf: (leaf.event_time, leaf.leaf_type, leaf.object_hash))
        )
        leaf_hashes = deterministic_leaf_ordering(
            tuple(hash_transparency_leaf(leaf) for leaf in ordered_leaves)
        )
        latest = self.repository.latest(stream_id_hash(stream))
        now = self.clock()
        start = min((leaf.event_time for leaf in ordered_leaves), default=now)
        end = max((leaf.event_time for leaf in ordered_leaves), default=now)
        checkpoint_id = sha256_prefixed(f"checkpoint:v1:{stream_id_hash(stream)}:{batch_identity_hash}")
        draft = TransparencyCheckpoint(
            checkpoint_id=checkpoint_id,
            checkpoint_type=stream.checkpoint_type,
            version=1,
            schema_epoch=schema_epoch,
            crypto_epoch=crypto_epoch,
            policy_epoch=policy_epoch,
            issuer_key_id=self.signer.issuer_key_id,
            hash_suite="sha256",
            signature_suite="ed25519",
            visibility=visibility,
            stream_id_hash=stream_id_hash(stream),
            sequence_number=1 if latest is None else latest.sequence_number + 1,
            source_count=len(ordered_leaves),
            batch_start_time=start,
            batch_end_time=end,
            root_hash=build_merkle_root(leaf_hashes),
            previous_checkpoint_hash=latest.checkpoint_hash if latest else GENESIS_CHECKPOINT_HASH,
            checkpoint_hash="sha256:" + "0" * 64,
            created_at=now,
            metadata_commitment=metadata_commitment,
            revocation_epoch=revocation_epoch,
            auth_domain_hash=stream.auth_domain_hash,
            environment=stream.environment,
        )
        finalized_hash = hash_checkpoint_payload(draft)
        signed = self.signer.sign(replace(draft, checkpoint_hash=finalized_hash))
        stored = self.repository.finalize_signed_checkpoint(
            StoredCheckpoint(signed, batch_identity_hash, ordered_leaves, leaf_hashes)
        )
        if self.audit_sink:
            self.audit_sink(
                "transparency_checkpoint_signed",
                {
                    "checkpoint_hash": signed.checkpoint_hash,
                    "checkpoint_type": signed.checkpoint_type.value,
                    "sequence_number": signed.sequence_number,
                    "stream_id_hash": signed.stream_id_hash,
                },
            )
        return stored

    build_checkpoint = build_checkpoint_from_commitments

    def preview_checkpoint(self, **kwargs: object) -> StoredCheckpoint:
        raise NotImplementedError("preview requires a non-persisting signer boundary")
