from app.services.access.revocation_registry import RevocationTargetType


def test_quorum_uses_authoritative_revocation_target_names() -> None:
    assert RevocationTargetType.QUORUM_POLICY.value == "quorum_policy"
    assert RevocationTargetType.QUORUM_ATTEMPT.value == "quorum_attempt"
    assert RevocationTargetType.QUORUM_APPROVAL.value == "quorum_approval"
    assert RevocationTargetType.MULTI_METHOD_QUORUM.value == "multi_method_quorum"
