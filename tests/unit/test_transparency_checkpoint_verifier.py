from dataclasses import replace

from app.services.wallet_auth.transparency.checkpoint_verifier import TransparencyCheckpointVerifier
from tests.unit.transparency_helpers import builder, leaf, public_key, stream


def test_checkpoint_and_chain_verify_with_sources():
    service, repository = builder()
    first = service.build_checkpoint(stream=stream(), commitments=[leaf()], batch_identity_hash="one").checkpoint
    second = service.build_checkpoint(stream=stream(), commitments=[leaf(suffix="2")], batch_identity_hash="two").checkpoint
    verifier = TransparencyCheckpointVerifier(issuer_public_keys={"issuer-v1": public_key()})
    assert verifier.verify_checkpoint(first, commitments=[leaf()]).valid
    assert all(result.valid for result in verifier.verify_checkpoint_chain(repository.get_checkpoint_chain(first.stream_id_hash)))
    assert not verifier.verify_checkpoint(replace(second, previous_checkpoint_hash="sha256:wrong"), previous=first).valid


def test_tampering_and_wrong_issuer_fail():
    service, _ = builder()
    checkpoint = service.build_checkpoint(stream=stream(), commitments=[leaf()], batch_identity_hash="tamper").checkpoint
    assert not TransparencyCheckpointVerifier(issuer_public_keys={}).verify_checkpoint(checkpoint).valid
    assert not TransparencyCheckpointVerifier(issuer_public_keys={"issuer-v1": public_key()}).verify_checkpoint(replace(checkpoint, source_count=9)).valid
