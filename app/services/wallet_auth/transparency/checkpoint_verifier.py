"""Structured checkpoint, chain, signature, and Merkle verification."""

from collections.abc import Callable, Sequence
from typing import Any

from app.services.access.crypto.issuer_envelope import verify_serialized_issuer_envelope

from .canonicalization import checkpoint_signed_payload, hash_checkpoint_payload, hash_transparency_leaf
from .checkpoint_builder import GENESIS_CHECKPOINT_HASH
from .checkpoint_types import PublicationStatus, TransparencyVisibility
from .merkle import build_merkle_root
from .models import CheckpointVerificationResult, TransparencyCheckpoint, TransparencyLeafCommitment
from .privacy import validate_source_metadata


class TransparencyCheckpointVerifier:
    def __init__(
        self,
        *,
        issuer_public_keys: dict[str, str],
        audit_sink: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> None:
        self.issuer_public_keys = issuer_public_keys
        self.audit_sink = audit_sink

    def verify_checkpoint(
        self,
        checkpoint: TransparencyCheckpoint,
        *,
        previous: TransparencyCheckpoint | None = None,
        commitments: Sequence[TransparencyLeafCommitment] | None = None,
    ) -> CheckpointVerificationResult:
        expected_hash = hash_checkpoint_payload(checkpoint)
        hash_valid = expected_hash == checkpoint.checkpoint_hash
        sequence_valid = (
            checkpoint.sequence_number == 1 and checkpoint.previous_checkpoint_hash == GENESIS_CHECKPOINT_HASH
            if previous is None
            else checkpoint.sequence_number == previous.sequence_number + 1
            and checkpoint.previous_checkpoint_hash == previous.checkpoint_hash
        )
        stream_valid = previous is None or previous.stream_id_hash == checkpoint.stream_id_hash
        root_valid: bool | None = None
        if commitments is not None:
            root_valid = (
                len(commitments) == checkpoint.source_count
                and build_merkle_root(tuple(hash_transparency_leaf(item) for item in commitments))
                == checkpoint.root_hash
            )
        visibility_valid = True
        try:
            if checkpoint.visibility is TransparencyVisibility.PUBLIC_SAFE and commitments:
                for commitment in commitments:
                    validate_source_metadata(commitment.to_dict(), public_safe=True)
        except ValueError:
            visibility_valid = False
        envelope = checkpoint.issuer_envelope or {}
        public_key = self.issuer_public_keys.get(checkpoint.issuer_key_id)
        signature_valid = bool(public_key) and verify_serialized_issuer_envelope(
            checkpoint_signed_payload(checkpoint),
            envelope,
            public_key=public_key or "",
            expected_key_id=checkpoint.issuer_key_id,
        )
        issuer_epoch_valid = checkpoint.crypto_epoch == 1
        not_revoked = checkpoint.publication_status not in {
            PublicationStatus.REVOKED,
            PublicationStatus.SUPERSEDED,
        }
        valid = all(
            (
                hash_valid,
                sequence_valid,
                stream_valid,
                root_valid is not False,
                signature_valid,
                issuer_epoch_valid,
                visibility_valid,
                not_revoked,
            )
        )
        reason = None
        if not hash_valid:
            reason = "checkpoint_hash_mismatch"
        elif not stream_valid:
            reason = "cross_stream_link"
        elif not sequence_valid:
            reason = "sequence_gap"
        elif root_valid is False:
            reason = "root_mismatch"
        elif not signature_valid:
            reason = "signature_invalid"
        elif not issuer_epoch_valid:
            reason = "issuer_epoch_invalid"
        elif not visibility_valid:
            reason = "visibility_violation"
        elif not not_revoked:
            reason = "checkpoint_revoked_or_superseded"
        result = CheckpointVerificationResult(
            "valid" if valid else "invalid",
            valid,
            hash_valid,
            signature_valid,
            sequence_valid,
            stream_valid,
            root_valid,
            issuer_epoch_valid,
            visibility_valid,
            reason,
        )
        if self.audit_sink:
            self.audit_sink(
                "transparency_checkpoint_verified" if valid else "transparency_checkpoint_verification_failed",
                {
                    "checkpoint_hash": checkpoint.checkpoint_hash,
                    "checkpoint_type": checkpoint.checkpoint_type.value,
                    "sequence_number": checkpoint.sequence_number,
                    "stream_id_hash": checkpoint.stream_id_hash,
                    "verification_result": result.status,
                },
            )
        return result

    def verify_checkpoint_chain(
        self, checkpoints: Sequence[TransparencyCheckpoint]
    ) -> tuple[CheckpointVerificationResult, ...]:
        results: list[CheckpointVerificationResult] = []
        previous = None
        for checkpoint in checkpoints:
            result = self.verify_checkpoint(checkpoint, previous=previous)
            results.append(result)
            previous = checkpoint
        return tuple(results)

    verify_checkpoint_signature = verify_checkpoint
    verify_checkpoint_sequence = verify_checkpoint
    verify_checkpoint_stream = verify_checkpoint
