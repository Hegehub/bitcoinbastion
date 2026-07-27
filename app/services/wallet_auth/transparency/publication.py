"""Idempotent internal and signed-artifact publication boundary."""

from collections.abc import Callable
from typing import Any, Mapping

from .checkpoint_types import PublicationStatus, TransparencyVisibility
from .errors import CheckpointPublicationError
from .models import TransparencyCheckpoint
from .privacy import sanitize_public_artifact
from .repositories import InMemoryTransparencyRepository


class TransparencyPublisher:
    def __init__(
        self,
        repository: InMemoryTransparencyRepository,
        audit_sink: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> None:
        self.repository = repository
        self.audit_sink = audit_sink
        self._artifacts: dict[str, dict[str, Any]] = {}

    def publish_checkpoint(
        self, checkpoint: TransparencyCheckpoint, *, target: str = "internal"
    ) -> Mapping[str, Any]:
        if target not in {"internal", "signed_artifact"}:
            raise CheckpointPublicationError("unsupported publication target")
        if target == "signed_artifact" and checkpoint.visibility is not TransparencyVisibility.PUBLIC_SAFE:
            raise CheckpointPublicationError("restricted checkpoint cannot be publicly published")
        artifact = checkpoint_artifact(checkpoint)
        if target == "signed_artifact":
            artifact = sanitize_public_artifact(artifact)
        self._artifacts.setdefault(checkpoint.checkpoint_id, artifact)
        self.repository.mark_publication_status(checkpoint.checkpoint_id, PublicationStatus.PUBLISHED)
        if self.audit_sink:
            self.audit_sink(
                "transparency_checkpoint_published",
                {
                    "checkpoint_hash": checkpoint.checkpoint_hash,
                    "checkpoint_type": checkpoint.checkpoint_type.value,
                    "sequence_number": checkpoint.sequence_number,
                    "stream_id_hash": checkpoint.stream_id_hash,
                    "publication_result": target,
                },
            )
        return self._artifacts[checkpoint.checkpoint_id]

    def get_publication_status(self, checkpoint_id: str) -> PublicationStatus | None:
        record = self.repository.get_checkpoint(checkpoint_id, include_restricted=True)
        return record.checkpoint.publication_status if record else None

    def retry_publication(self, checkpoint: TransparencyCheckpoint, *, target: str) -> Mapping[str, Any]:
        return self.publish_checkpoint(checkpoint, target=target)

    def verify_published_artifact(self, checkpoint_id: str, checkpoint_hash: str) -> bool:
        artifact = self._artifacts.get(checkpoint_id)
        return bool(artifact and artifact.get("checkpoint_hash") == checkpoint_hash)


def checkpoint_artifact(checkpoint: TransparencyCheckpoint) -> dict[str, Any]:
    envelope = checkpoint.issuer_envelope or {}
    issuer = envelope.get("issuer", {})
    signatures = envelope.get("signatures", {})
    return {
        "type": "bastion_transparency_checkpoint",
        "version": 1,
        "checkpoint_id": checkpoint.checkpoint_id,
        "checkpoint_type": checkpoint.checkpoint_type.value,
        "stream": {"environment": checkpoint.environment, "sequence_number": checkpoint.sequence_number},
        "epochs": {"schema": checkpoint.schema_epoch, "crypto": checkpoint.crypto_epoch, "policy": checkpoint.policy_epoch, "revocation": checkpoint.revocation_epoch},
        "root_hash": checkpoint.root_hash,
        "previous_checkpoint_hash": checkpoint.previous_checkpoint_hash,
        "checkpoint_hash": checkpoint.checkpoint_hash,
        "source_count": checkpoint.source_count,
        "created_at": checkpoint.created_at.isoformat(),
        "expires_at": checkpoint.expires_at.isoformat() if checkpoint.expires_at else None,
        "issuer": {"key_id": issuer.get("key_id"), "classical_signature": signatures.get("classical"), "post_quantum_signature": signatures.get("post_quantum")},
        "visibility": checkpoint.visibility.value,
        "hash_suite": checkpoint.hash_suite,
        "signature_suite": checkpoint.signature_suite,
        "environment": checkpoint.environment,
        "metadata_commitment": checkpoint.metadata_commitment,
    }
