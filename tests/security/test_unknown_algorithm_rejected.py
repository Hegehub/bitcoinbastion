import pytest

from app.services.access.crypto.crypto_agility import (
    CryptoCapabilityRegistry,
    CryptoProviderUnavailable,
)


def test_unknown_algorithm_fails_closed():
    with pytest.raises(CryptoProviderUnavailable):
        CryptoCapabilityRegistry().require_verification("future_magic")
