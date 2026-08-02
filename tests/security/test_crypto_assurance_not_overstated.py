from app.services.access.crypto.algorithms import CryptoAssuranceLevel
from app.services.access.crypto.issuer_envelope import (
    BastionIssuedObjectType,
    build_classical_issuer_envelope,
)


def test_classical_signature_grants_only_classical_assurance():
    envelope = build_classical_issuer_envelope(
        {},
        object_type=BastionIssuedObjectType.RECOVERY_CAPSULE,
        object_id_hash="sha256:id",
        object_fingerprint="sha256:o",
        issuer_key_id="issuer",
        issuer_private_key="AQIDBAUGBwgJCgsMDQ4PEBESExQVFhcYGRobHB0eHyA",
    )
    assert envelope.assurance_level is CryptoAssuranceLevel.CLASSICAL
