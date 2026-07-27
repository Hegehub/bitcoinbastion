import pytest

from app.domain.wallet_auth.quorum import (
    QuorumParticipantSlot,
    QuorumParticipantType as P,
    QuorumPolicy,
    QuorumProofMethod as M,
    QuorumType,
)
from app.services.wallet_auth.quorum_policies import (
    business_owner_policy,
    issuer_rotation_policy,
    sovereign_recovery_policy,
)


def _policy(**changes) -> QuorumPolicy:
    values = {
        "policy_id": "business-owner-v1",
        "version": 1,
        "quorum_type": QuorumType.BUSINESS,
        "action": "business_owner_change",
        "threshold": 2,
        "participant_slots": (
            QuorumParticipantSlot("owner", "business_owner"),
            QuorumParticipantSlot("admin", "business_admin"),
        ),
        "minimum_distinct_principals": 2,
        "minimum_distinct_methods": 2,
        "allowed_principal_types": frozenset(
            {P.BITCOIN_WALLET_PRINCIPAL, P.LIGHTNING_WALLET_PRINCIPAL}
        ),
        "allowed_proof_methods": frozenset({M.BIP322, M.LNURL_AUTH}),
        "required_roles": frozenset({"business_owner", "business_admin"}),
    }
    values.update(changes)
    return QuorumPolicy(**values)


def test_policy_hash_is_canonical_and_stable() -> None:
    assert _policy().policy_hash == _policy().policy_hash
    assert _policy(action="enterprise_policy_change").policy_hash != _policy().policy_hash


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"threshold": 3}, "invalid_quorum_threshold"),
        ({"minimum_distinct_methods": 3}, "invalid_quorum_distinct_methods"),
        ({"required_methods": frozenset({M.HARDWARE_WALLET})}, "not_allowed"),
    ],
)
def test_invalid_policy_constraints_fail_closed(changes, reason) -> None:
    with pytest.raises(ValueError, match=reason):
        _policy(**changes)


def test_sovereign_policy_must_forbid_legacy_signature() -> None:
    with pytest.raises(ValueError, match="forbid_legacy"):
        _policy(quorum_type=QuorumType.SOVEREIGN)


def test_policy_metadata_rejects_secret_material() -> None:
    with pytest.raises(ValueError, match="unsafe_quorum_metadata"):
        _policy(metadata={"private_key": "never"})


def test_high_risk_policy_providers_are_valid_and_strong() -> None:
    business = business_owner_policy()
    sovereign = sovereign_recovery_policy()
    issuer = issuer_rotation_policy()
    assert business.required_roles == frozenset({"business_owner", "business_admin"})
    assert sovereign.require_air_gapped_proof and sovereign.require_recovery_capsule
    assert M.LNURL_AUTH in sovereign.forbidden_proof_methods
    assert issuer.require_hardware_wallet and issuer.require_transparency_checkpoint
