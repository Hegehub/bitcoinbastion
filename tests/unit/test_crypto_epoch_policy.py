from app.services.access.crypto.migration_policy import (
    CryptoEpochRegistry,
    SignatureRequirementPolicy,
)


def test_only_epoch_one_is_active_and_epoch_two_is_planned():
    registry = CryptoEpochRegistry()
    assert registry.active().epoch == 1
    assert registry.get(2).status == "planned_inactive"
    assert registry.get(2).default_signature_policy is SignatureRequirementPolicy.HYBRID_REQUIRED
