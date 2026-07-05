CORRELATION_LIMITATION = "Correlation is not proof of causation."


class CandleAttributionLimitationsBuilder:
    def build(
        self, provider_confidence: float, event_density: int, elevated_volatility: bool
    ) -> list[str]:
        limitations = [CORRELATION_LIMITATION]
        if provider_confidence < 0.5:
            limitations.append("Provider confidence degraded")
        if event_density == 0:
            limitations.append("Low event density")
        if event_density > 1:
            limitations.append("Multiple overlapping events detected")
        if elevated_volatility:
            limitations.append("Candle occurred during elevated volatility")
        return limitations
