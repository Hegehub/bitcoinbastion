from dataclasses import replace

import pytest

from app.services.wallet_auth.transparency.repositories import StoredCheckpoint
from tests.unit.transparency_helpers import builder, leaf, stream


def test_signed_checkpoint_is_frozen_and_duplicate_sequence_is_rejected():
    service, repository = builder()
    first = service.build_checkpoint(stream=stream(), commitments=[leaf()], batch_identity_hash="one")
    with pytest.raises((AttributeError, TypeError)):
        first.checkpoint.sequence_number = 9  # type: ignore[misc]
    with pytest.raises(TypeError):
        first.checkpoint.issuer_envelope["version"] = 2  # type: ignore[index]
    conflicting = StoredCheckpoint(
        replace(first.checkpoint, checkpoint_id="sha256:other", checkpoint_hash="sha256:other"),
        "another-batch", first.leaves, first.leaf_hashes,
    )
    with pytest.raises(ValueError):
        repository.finalize_signed_checkpoint(conflicting)
