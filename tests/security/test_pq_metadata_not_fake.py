from app.services.access.crypto.algorithms import CryptoCapabilityStatus, SignatureAlgorithm
from app.services.access.crypto.crypto_agility import CryptoCapabilityRegistry


def test_metadata_only_ml_dsa_has_no_crypto_operations():
    capability = CryptoCapabilityRegistry().get(SignatureAlgorithm.ML_DSA_65)
    assert capability.capability_status is CryptoCapabilityStatus.METADATA_ONLY
    assert not capability.can_sign and not capability.can_verify
