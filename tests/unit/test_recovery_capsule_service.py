from pathlib import Path


def test_service_requires_policy_revocation_artifact_boundaries_and_has_no_support_bypass() -> None:
    source = Path("app/services/wallet_auth/recovery/capsule.py").read_text()
    assert (
        "policy_authorizer" in source
        and "revocation_resolver" in source
        and "artifact_manager" in source
    )
    assert (
        "support_bypass" not in source
        and "email_reset" not in source
        and "password_reset" not in source
    )
