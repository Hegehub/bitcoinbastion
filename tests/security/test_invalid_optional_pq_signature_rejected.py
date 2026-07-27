from dataclasses import replace

import pytest

from app.services.access.crypto.algorithms import CryptoCapabilityStatus, SignatureAlgorithm
from app.services.access.crypto.crypto_agility import (
    CryptoCapabilityRegistry,
    CryptoProviderUnavailable,
)
from app.services.access.crypto.issuer_envelope import (
    BastionIssuedObjectType,
    EnvelopeSignature,
    build_classical_issuer_envelope,
)


def test_supplied_invalid_pq_is_not_ignored():
    envelope = build_classical_issuer_envelope(
        {},
        object_type=BastionIssuedObjectType.OFFLINE_VALIDITY_PACK,
        object_id_hash="sha256:id",
        object_fingerprint="sha256:o",
        issuer_key_id="issuer",
        issuer_private_key="AQIDBAUGBwgJCgsMDQ4PEBESExQVFhcYGRobHB0eHyA",
    )
    supplied = replace(
        envelope,
        post_quantum_signature=EnvelopeSignature(
            SignatureAlgorithm.ML_DSA_65, "pq-key", "invalid", CryptoCapabilityStatus.ACTIVE
        ),
    )
    with pytest.raises(CryptoProviderUnavailable):
        CryptoCapabilityRegistry().require_verification(supplied.post_quantum_signature.alg)
