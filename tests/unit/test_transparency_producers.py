from datetime import UTC, datetime

from app.services.wallet_auth.transparency.producers import (
    issuer_key_epoch_commitment, lnurl_payment_proof_commitment,
    policy_epoch_commitment, recovery_event_commitment, revocation_epoch_commitment,
)

NOW = datetime(2026, 7, 27, tzinfo=UTC)


def test_producers_emit_commitments_not_source_secrets():
    leaves = [
        issuer_key_epoch_commitment(key_id_hash="sha256:key", crypto_epoch=1, status="active", signature_suite="ed25519", event_time=NOW),
        policy_epoch_commitment(policy_bundle_hash="sha256:policy", policy_epoch=1, schema_version=1, environment="production", event_time=NOW),
        revocation_epoch_commitment(registry_root_hash="sha256:root", revocation_epoch=2, entry_count=3, event_time=NOW),
        recovery_event_commitment(recovery_event_hash="sha256:event", profile="pro", outcome="complete", cooldown_class="long", quorum_class="2of3", object_epoch=1, policy_hash="sha256:policy", event_time=NOW),
        lnurl_payment_proof_commitment(proof_fingerprint="sha256:proof", payment_status_commitment="sha256:settled", entitlement_commitment_hash="sha256:ent", payment_method="lnurl_pay", settlement_method="node", amount_bucket="small", object_epoch=1, policy_hash="sha256:policy", event_time=NOW),
    ]
    assert all(item.object_hash.startswith("sha256:") for item in leaves)
    assert "invoice" not in repr(leaves)
    assert "private_key" not in repr(leaves)
