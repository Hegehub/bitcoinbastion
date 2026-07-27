import pytest

from app.services.access.crypto.issuer_envelope import (
    BastionIssuedObjectType,
    build_classical_issuer_envelope,
)
from app.services.access.crypto.migration_policy import SignatureRequirementPolicy
from app.services.access.policy_context import (
    AccessPolicyContext,
    PolicyActorType,
    PolicyAuthMethod,
)
from app.services.access.policy_engine import AccessPolicyEngine
from app.domain.access.plans import PlanCode


def test_hybrid_policy_never_downgrades_to_classical():
    with pytest.raises(RuntimeError):
        build_classical_issuer_envelope(
            {},
            object_type=BastionIssuedObjectType.TRANSPARENCY_CHECKPOINT,
            object_id_hash="sha256:id",
            object_fingerprint="sha256:o",
            issuer_key_id="issuer",
            issuer_private_key="AQIDBAUGBwgJCgsMDQ4PEBESExQVFhcYGRobHB0eHyA",
            requirement=SignatureRequirementPolicy.HYBRID_REQUIRED,
        )


def test_policy_engine_uses_granted_assurance_not_algorithm_label():
    decision = AccessPolicyEngine().evaluate(
        AccessPolicyContext(
            actor_type=PolicyActorType.BITCOIN_WALLET_PRINCIPAL,
            actor_hash="hmac:actor",
            principal_hash="hmac:principal",
            auth_methods=frozenset({PolicyAuthMethod.BIP322, PolicyAuthMethod.SESSION_POP}),
            plan_code=PlanCode.PRO,
            issuer_envelope_verified=True,
            signature_requirement_policy="hybrid_required",
            granted_crypto_assurance="classical",
        )
    )
    assert not decision.allowed
    assert decision.reason_code == "required_hybrid_signature_unavailable"
