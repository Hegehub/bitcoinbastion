from app.services.wallet_auth.recovery.policy import PROFILE_REQUIREMENTS


def test_payment_cannot_complete_any_profile_alone() -> None:
    for requirements in PROFILE_REQUIREMENTS.values():
        assert requirements.required_factor_count > 1
        assert not requirements.principal_proof_one_of.issubset({})
