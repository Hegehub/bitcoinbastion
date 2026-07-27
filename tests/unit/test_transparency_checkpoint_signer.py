from app.services.access.crypto.migration_policy import SignatureRequirementPolicy
from app.services.wallet_auth.transparency.checkpoint_signer import TransparencyCheckpointSigner
from tests.unit.transparency_helpers import PRIVATE, builder, leaf, stream


def test_checkpoint_has_real_classical_and_truthful_metadata_only_pq_signature():
    service, _ = builder()
    checkpoint = service.build_checkpoint(stream=stream(), commitments=[leaf()], batch_identity_hash="signed").checkpoint
    signatures = checkpoint.issuer_envelope["signatures"]
    assert signatures["classical"]["sig"]
    assert signatures["post_quantum"]["sig"] is None
    assert signatures["post_quantum"]["status"] == "metadata_only"


def test_required_hybrid_signing_fails_without_provider():
    service, _ = builder()
    checkpoint = service.build_checkpoint(stream=stream(), commitments=[leaf()], batch_identity_hash="base").checkpoint
    signer = TransparencyCheckpointSigner(issuer_key_id="issuer-v1", issuer_private_key=PRIVATE)
    try:
        signer.sign(checkpoint, requirement=SignatureRequirementPolicy.HYBRID_REQUIRED)
    except ValueError:
        pass
    else:
        raise AssertionError("fake hybrid signature accepted")
