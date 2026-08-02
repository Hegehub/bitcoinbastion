"""Version-one canonicalization for transparency commitments."""

from datetime import datetime
from typing import Any, Mapping

from app.services.access.crypto.hashing import canonical_json, sha256_prefixed

from .errors import CheckpointCanonicalizationError
from .models import TransparencyCheckpoint, TransparencyLeafCommitment, utc_iso


def canonicalize_transparency_leaf(leaf: TransparencyLeafCommitment) -> str:
    return canonical_json(leaf.to_dict())


def hash_transparency_leaf(leaf: TransparencyLeafCommitment) -> str:
    return sha256_prefixed("BASTION_TRANSPARENCY_LEAF_V1\x00" + canonicalize_transparency_leaf(leaf))


def checkpoint_signed_payload(checkpoint: TransparencyCheckpoint) -> dict[str, Any]:
    """Return immutable fields only; signatures/publication state are deliberately excluded."""
    return {
        "type": "bastion_transparency_checkpoint",
        "version": checkpoint.version,
        "checkpoint_id": checkpoint.checkpoint_id,
        "checkpoint_type": checkpoint.checkpoint_type.value,
        "epochs": {
            "schema": checkpoint.schema_epoch,
            "crypto": checkpoint.crypto_epoch,
            "policy": checkpoint.policy_epoch,
            "revocation": checkpoint.revocation_epoch,
        },
        "issuer_key_id": checkpoint.issuer_key_id,
        "hash_suite": checkpoint.hash_suite,
        "signature_suite": checkpoint.signature_suite,
        "visibility": checkpoint.visibility.value,
        "stream_id_hash": checkpoint.stream_id_hash,
        "environment": checkpoint.environment,
        "sequence_number": checkpoint.sequence_number,
        "source_count": checkpoint.source_count,
        "batch_start_time": utc_iso(checkpoint.batch_start_time),
        "batch_end_time": utc_iso(checkpoint.batch_end_time),
        "root_hash": checkpoint.root_hash,
        "previous_checkpoint_hash": checkpoint.previous_checkpoint_hash,
        "created_at": utc_iso(checkpoint.created_at),
        "expires_at": utc_iso(checkpoint.expires_at) if checkpoint.expires_at else None,
        "metadata_commitment": checkpoint.metadata_commitment,
        "auth_domain_hash": checkpoint.auth_domain_hash,
        "service_instance_class": checkpoint.service_instance_class,
        "retention_class": checkpoint.retention_class,
        "supersedes_checkpoint_id": checkpoint.supersedes_checkpoint_id,
        "emergency_reason_code": checkpoint.emergency_reason_code,
    }


def canonicalize_checkpoint_payload(checkpoint: TransparencyCheckpoint) -> str:
    try:
        return canonical_json(checkpoint_signed_payload(checkpoint))
    except (TypeError, ValueError) as exc:
        raise CheckpointCanonicalizationError("checkpoint cannot be canonicalized") from exc


def hash_checkpoint_payload(checkpoint: TransparencyCheckpoint) -> str:
    return sha256_prefixed(
        "BASTION_TRANSPARENCY_CHECKPOINT_V1\x00" + canonicalize_checkpoint_payload(checkpoint)
    )


def canonical_commitment(value: Mapping[str, Any], *, context: str) -> str:
    return sha256_prefixed(f"BASTION_TRANSPARENCY_COMMITMENT_V1\x00{context}\x00{canonical_json(dict(value))}")


def normalize_timestamp(value: datetime) -> str:
    return utc_iso(value)
