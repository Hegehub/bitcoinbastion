from app.services.access.crypto.algorithms import CryptoAssuranceLevel, SignatureAlgorithm
from app.services.access.crypto.crypto_agility import CryptoCapabilityRegistry
from app.services.access.crypto.issuer_envelope import (
    BastionIssuedObjectType,
    build_classical_issuer_envelope,
)
from app.services.access.crypto.migration_policy import CryptoEpochRegistry


def test_wallet_and_settled_lnurl_entitlement_share_classical_chain_and_planned_migration():
    key = "AQIDBAUGBwgJCgsMDQ4PEBESExQVFhcYGRobHB0eHyA"
    wallet = build_classical_issuer_envelope(
        {"principal_hash": "hmac-sha256:wallet", "plan": "plus_pass"},
        object_type=BastionIssuedObjectType.WALLET_SUBSCRIPTION_ENTITLEMENT,
        object_id_hash="sha256:wallet-entitlement",
        object_fingerprint="sha256:wallet",
        issuer_key_id="issuer",
        issuer_private_key=key,
    )
    lnurl = build_classical_issuer_envelope(
        {
            "principal_hash": "hmac-sha256:lightning",
            "payment_proof_hash": "sha256:settled",
            "settled": True,
        },
        object_type=BastionIssuedObjectType.LIGHTNING_SUBSCRIPTION_ENTITLEMENT,
        object_id_hash="sha256:lnurl-entitlement",
        object_fingerprint="sha256:lnurl",
        issuer_key_id="issuer",
        issuer_private_key=key,
    )
    assert wallet.type == lnurl.type
    assert wallet.assurance_level is lnurl.assurance_level is CryptoAssuranceLevel.CLASSICAL
    assert CryptoEpochRegistry().get(2).status == "planned_inactive"
    assert not CryptoCapabilityRegistry().get(SignatureAlgorithm.ML_DSA_65).can_verify
