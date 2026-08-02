from datetime import UTC, datetime

from app.services.wallet_auth.recovery.cooldown import RecoveryCooldownService
from app.services.wallet_auth.recovery.models import RecoveryProfile


def test_profile_minimums_and_risk_extension() -> None:
    now = datetime.now(UTC)
    service = RecoveryCooldownService()
    lite = service.calculate_expiry(profile=RecoveryProfile.LITE_BASIC, risk_level="low", now=now)
    sovereign = service.calculate_expiry(
        profile=RecoveryProfile.SOVEREIGN, risk_level="low", now=now
    )
    risky = service.calculate_expiry(
        profile=RecoveryProfile.LITE_BASIC, risk_level="high", now=now, failed_attempts=2
    )
    assert int((lite - now).total_seconds()) == 1800
    assert int((sovereign - now).total_seconds()) == 172800
    assert risky > lite
