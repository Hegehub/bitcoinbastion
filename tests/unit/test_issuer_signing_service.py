from app.services.access.crypto.issuer_envelope import (
    BastionIssuedObjectType,
    build_classical_issuer_envelope,
)


def test_all_supported_object_types_use_common_envelope():
    key = "AQIDBAUGBwgJCgsMDQ4PEBESExQVFhcYGRobHB0eHyA"
    for object_type in BastionIssuedObjectType:
        envelope = build_classical_issuer_envelope(
            {"value": object_type.value},
            object_type=object_type,
            object_id_hash="sha256:id",
            object_fingerprint="sha256:object",
            issuer_key_id="issuer",
            issuer_private_key=key,
        )
        assert envelope.type == "bastion_issuer_signature_envelope"
