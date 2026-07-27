from app.services.access.crypto.algorithms import CryptoCapabilityStatus, SignatureAlgorithm
from app.services.access.crypto.crypto_agility import CryptoCapabilityRegistry


def test_registry_reports_reality_not_environment_intent():
    registry = CryptoCapabilityRegistry()
    assert registry.get(SignatureAlgorithm.ED25519).can_sign
    pq = registry.get(SignatureAlgorithm.ML_DSA_65)
    assert pq.capability_status is CryptoCapabilityStatus.METADATA_ONLY
    assert not pq.can_sign and not pq.can_verify
