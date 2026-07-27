from app.services.access.crypto.issuer_envelope import (
    BastionIssuedObjectType,
    build_classical_issuer_envelope,
)


def test_wallet_lnurl_recovery_and_offline_use_same_envelope_type():
    key = "AQIDBAUGBwgJCgsMDQ4PEBESExQVFhcYGRobHB0eHyA"
    values = [
        build_classical_issuer_envelope(
            {},
            object_type=kind,
            object_id_hash="sha256:id",
            object_fingerprint="sha256:o",
            issuer_key_id="issuer",
            issuer_private_key=key,
        ).type
        for kind in (
            BastionIssuedObjectType.WALLET_SUBSCRIPTION_ENTITLEMENT,
            BastionIssuedObjectType.LIGHTNING_SUBSCRIPTION_ENTITLEMENT,
            BastionIssuedObjectType.RECOVERY_CAPSULE,
            BastionIssuedObjectType.OFFLINE_VALIDITY_PACK,
        )
    ]
    assert set(values) == {"bastion_issuer_signature_envelope"}
