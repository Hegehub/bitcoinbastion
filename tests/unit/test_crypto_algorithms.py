from app.services.access.crypto.algorithms import (
    EncryptionOrKEMAlgorithm,
    HashAlgorithm,
    SignatureAlgorithm,
)


def test_stable_crypto_algorithm_values():
    assert SignatureAlgorithm.ED25519.value == "ed25519"
    assert SignatureAlgorithm.ML_DSA_65.value == "ml_dsa_65"
    assert HashAlgorithm.SHA256.value == "sha256"
    assert EncryptionOrKEMAlgorithm.HYBRID_X25519_ML_KEM_768.value == "hybrid_x25519_ml_kem_768"
