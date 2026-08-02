import pytest

from app.services.access.crypto.algorithms import SignatureAlgorithm
from app.services.access.crypto.crypto_agility import (
    CryptoProviderUnavailable,
    validate_crypto_configuration,
)


def test_flag_cannot_fabricate_pq_provider(monkeypatch):
    monkeypatch.setenv("ACCESS_PQ_ENABLED", "true")
    with pytest.raises(CryptoProviderUnavailable):
        validate_crypto_configuration(
            pq_enabled=True,
            pq_algorithm=SignatureAlgorithm.ML_DSA_65,
            requirement_policy="classical_required_pq_optional",
        )
