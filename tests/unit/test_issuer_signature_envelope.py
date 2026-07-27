from dataclasses import replace

import pytest

from app.services.access.crypto.algorithms import CryptoAssuranceLevel
from app.services.access.crypto.issuer_envelope import (
    BastionIssuedObjectType,
    build_classical_issuer_envelope,
)
from app.services.access.crypto.migration_policy import SignatureRequirementPolicy


TEST_KEY = "AQIDBAUGBwgJCgsMDQ4PEBESExQVFhcYGRobHB0eHyA"


def test_envelope_serialization_is_stable_and_truthful():
    payload = {"principal_hash": "hmac-sha256:p", "plan": "plus_pass"}
    envelope = build_classical_issuer_envelope(
        payload,
        object_type=BastionIssuedObjectType.WALLET_SUBSCRIPTION_ENTITLEMENT,
        object_id_hash="hmac-sha256:id",
        object_fingerprint="sha256:object",
        issuer_key_id="issuer-1",
        issuer_private_key=TEST_KEY,
    )
    assert envelope.to_dict() == envelope.to_dict()
    assert envelope.assurance_level is CryptoAssuranceLevel.CLASSICAL
    assert envelope.post_quantum_signature.sig is None
    with pytest.raises(ValueError):
        replace(envelope, assurance_level=CryptoAssuranceLevel.POST_QUANTUM)


def test_hybrid_signing_fails_without_provider():
    with pytest.raises(RuntimeError):
        build_classical_issuer_envelope(
            {},
            object_type=BastionIssuedObjectType.RECOVERY_CAPSULE,
            object_id_hash="sha256:id",
            object_fingerprint="sha256:o",
            issuer_key_id="issuer",
            issuer_private_key=TEST_KEY,
            requirement=SignatureRequirementPolicy.HYBRID_REQUIRED,
        )
