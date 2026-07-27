import pytest

from app.services.wallet_auth.transparency.privacy import (
    context_commitment, sanitize_public_artifact, validate_source_metadata,
)


@pytest.mark.parametrize("field", ["wallet_address", "linking_key", "raw_k1", "invoice", "preimage", "recovery_phrase", "session_token", "principal_hash"])
def test_public_source_rejects_sensitive_fields(field: str):
    with pytest.raises(ValueError):
        validate_source_metadata({field: "sensitive"}, public_safe=True)


def test_context_commitments_prevent_cross_stream_correlation():
    assert context_commitment(secret="pepper", stream_context="a", value="same") != context_commitment(secret="pepper", stream_context="b", value="same")
    with pytest.raises(ValueError):
        sanitize_public_artifact({"type": "bastion_transparency_checkpoint", "raw_source": {}})
