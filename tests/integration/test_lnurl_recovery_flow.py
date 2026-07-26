from app.services.access.revocation_registry import RevocationTargetType
from app.services.wallet_auth.lnurl_recovery_factor import (
    LNURLRecoveryConfig,
    RECOVERY_INTERNAL_ACTION,
    RECOVERY_WARNING,
)
from app.services.wallet_auth.recovery.models import RecoveryFactorType


def test_lnurl_recovery_integration_contract_is_attempt_bound_and_revocable() -> None:
    config = LNURLRecoveryConfig()
    assert config.ttl_seconds == 300
    assert config.require_additional_factor is True
    assert RECOVERY_INTERNAL_ACTION == "recovery_factor_verify"
    assert RecoveryFactorType.LNURL_AUTH_PROOF.value == "lnurl_auth_proof"
    assert RevocationTargetType.LNURL_RECOVERY_CHALLENGE.value == "lnurl_recovery_challenge"
    assert RevocationTargetType.LNURL_RECOVERY_FACTOR.value == "lnurl_recovery_factor"
    assert "does not complete recovery" in RECOVERY_WARNING
