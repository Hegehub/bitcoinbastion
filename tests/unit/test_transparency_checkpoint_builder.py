from app.services.wallet_auth.transparency.checkpoint_types import TransparencyCheckpointType
from tests.unit.transparency_helpers import builder, leaf, stream


def test_builder_is_idempotent_and_chains_monotonic_sequences():
    service, repository = builder()
    first = service.build_checkpoint(stream=stream(), commitments=[leaf()], batch_identity_hash="sha256:batch1")
    duplicate = service.build_checkpoint(stream=stream(), commitments=[leaf()], batch_identity_hash="sha256:batch1")
    second = service.build_checkpoint(stream=stream(), commitments=[leaf(suffix="2")], batch_identity_hash="sha256:batch2")
    assert duplicate.checkpoint.checkpoint_hash == first.checkpoint.checkpoint_hash
    assert second.checkpoint.sequence_number == 2
    assert second.checkpoint.previous_checkpoint_hash == first.checkpoint.checkpoint_hash
    assert len(repository.get_checkpoint_chain(first.checkpoint.stream_id_hash)) == 2


def test_cross_type_source_is_rejected():
    service, _ = builder()
    bad = leaf("recovery_event")
    try:
        service.build_checkpoint(stream=stream(TransparencyCheckpointType.POLICY_EPOCH), commitments=[bad], batch_identity_hash="bad")
    except ValueError:
        pass
    else:
        raise AssertionError("incompatible source accepted")
