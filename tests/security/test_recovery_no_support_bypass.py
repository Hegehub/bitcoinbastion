from app.services.wallet_auth.recovery.models import RecoveryFactorType


def test_support_and_email_are_not_factor_types() -> None:
    values = {factor.value for factor in RecoveryFactorType}
    assert "support_ticket" not in values and "email" not in values and "password" not in values
