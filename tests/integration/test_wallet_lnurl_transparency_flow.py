from datetime import UTC, datetime

from app.services.wallet_auth.transparency import (
    CheckpointStream, TransparencyCheckpointType, TransparencyCheckpointVerifier,
)
from app.services.wallet_auth.transparency.producers import (
    entitlement_commitment, lnurl_payment_proof_commitment, recovery_event_commitment,
    lightning_principal_commitment, revocation_epoch_commitment, wallet_credential_commitment,
)
from tests.unit.transparency_helpers import builder, public_key

NOW = datetime(2026, 7, 27, tzinfo=UTC)


def test_wallet_lnurl_entitlement_recovery_and_revocation_checkpoint_flow():
    service, repository = builder()
    cases = [
        (TransparencyCheckpointType.WALLET_CREDENTIAL_BATCH_ROOT, wallet_credential_commitment(credential_commitment="sha256:wallet-local", proof_method="bip322", status="active", object_epoch=1, policy_hash="sha256:policy", event_time=NOW)),
        (TransparencyCheckpointType.LIGHTNING_PRINCIPAL_BATCH_ROOT, lightning_principal_commitment(principal_commitment="sha256:lnurl-local", auth_domain_hash="sha256:domain", proof_method="lnurl_auth", verification_strength="standard", object_epoch=1, policy_hash="sha256:policy", event_time=NOW)),
        (TransparencyCheckpointType.LNURL_PAYMENT_PROOF_BATCH_ROOT, lnurl_payment_proof_commitment(proof_fingerprint="sha256:payment-local", payment_status_commitment="sha256:settled", entitlement_commitment_hash="sha256:ent", payment_method="lnurl_pay", settlement_method="node", amount_bucket=None, object_epoch=1, policy_hash="sha256:policy", event_time=NOW)),
        (TransparencyCheckpointType.SUBSCRIPTION_ENTITLEMENT_BATCH_ROOT, entitlement_commitment(entitlement_fingerprint="sha256:ent-local", plan_commitment="sha256:plan", validity_commitment="sha256:valid", status="active", object_epoch=1, policy_hash="sha256:policy", event_time=NOW)),
        (TransparencyCheckpointType.RECOVERY_EVENT_ROOT, recovery_event_commitment(recovery_event_hash="sha256:recovery-local", profile="pro", outcome="complete", cooldown_class="long", quorum_class="2of3", object_epoch=1, policy_hash="sha256:policy", event_time=NOW)),
        (TransparencyCheckpointType.REVOCATION_EPOCH, revocation_epoch_commitment(registry_root_hash="sha256:revocation-root", revocation_epoch=2, entry_count=4, event_time=NOW)),
    ]
    verifier = TransparencyCheckpointVerifier(issuer_public_keys={"issuer-v1": public_key()})
    for index, (kind, commitment) in enumerate(cases):
        record = service.build_checkpoint(
            stream=CheckpointStream(kind, "test", "bastion-access"),
            commitments=[commitment], batch_identity_hash=f"sha256:batch-{index}",
        )
        assert verifier.verify_checkpoint(record.checkpoint, commitments=[commitment]).valid
    assert len(repository.list_checkpoints(include_restricted=True)) == 6
