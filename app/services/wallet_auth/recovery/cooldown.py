from dataclasses import dataclass
from datetime import datetime, timedelta

from app.services.wallet_auth.recovery.models import RecoveryProfile


@dataclass(frozen=True, slots=True)
class RecoveryCooldownConfig:
    seconds: dict[RecoveryProfile, int]

    @classmethod
    def defaults(cls) -> "RecoveryCooldownConfig":
        return cls(
            {
                RecoveryProfile.LITE_BASIC: 1800,
                RecoveryProfile.PLUS: 7200,
                RecoveryProfile.PRO: 21600,
                RecoveryProfile.BUSINESS: 43200,
                RecoveryProfile.ENTERPRISE: 86400,
                RecoveryProfile.SOVEREIGN: 172800,
            }
        )


class RecoveryCooldownService:
    def __init__(self, config: RecoveryCooldownConfig | None = None) -> None:
        self.config = config or RecoveryCooldownConfig.defaults()

    def calculate_expiry(
        self,
        *,
        profile: RecoveryProfile,
        risk_level: str,
        now: datetime,
        failed_attempts: int = 0,
        recent_security_change: bool = False,
    ) -> datetime:
        base = self.config.seconds[profile]
        multiplier = 1 + min(failed_attempts, 4) * 0.25
        if risk_level in {"high", "critical"}:
            multiplier += 0.5
        if recent_security_change:
            multiplier += 0.5
        return now + timedelta(seconds=int(base * multiplier))

    def extend(
        self, current_expiry: datetime, *, profile: RecoveryProfile, now: datetime, risk_level: str
    ) -> datetime:
        mandatory = self.calculate_expiry(profile=profile, risk_level=risk_level, now=now)
        return max(current_expiry, mandatory)
