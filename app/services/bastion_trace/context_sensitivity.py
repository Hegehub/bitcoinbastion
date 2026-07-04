from app.schemas.bastion_trace import AmountSensitivity, ContextSensitivity


class ContextSensitivityService:
    def amount_sensitivity(self, amount_sats: int | None) -> AmountSensitivity:
        if amount_sats is None:
            return AmountSensitivity.UNKNOWN
        if amount_sats < 100_000:
            return AmountSensitivity.LOW
        if amount_sats <= 5_000_000:
            return AmountSensitivity.MEDIUM
        if amount_sats <= 50_000_000:
            return AmountSensitivity.HIGH
        return AmountSensitivity.VERY_HIGH

    def context_sensitivity(
        self, amount: AmountSensitivity, treasury: bool, urgent: bool
    ) -> ContextSensitivity:
        if amount == AmountSensitivity.UNKNOWN:
            return ContextSensitivity.UNKNOWN
        idx = [
            AmountSensitivity.LOW,
            AmountSensitivity.MEDIUM,
            AmountSensitivity.HIGH,
            AmountSensitivity.VERY_HIGH,
        ].index(amount)
        idx += int(treasury) + int(urgent)
        return [
            ContextSensitivity.LOW,
            ContextSensitivity.MEDIUM,
            ContextSensitivity.HIGH,
            ContextSensitivity.VERY_HIGH,
        ][min(idx, 3)]
