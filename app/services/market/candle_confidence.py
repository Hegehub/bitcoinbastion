
def calculate_candle_provider_confidence(provider_count: int, disagreement: float, degraded: bool) -> float:
    base = 0.35 if provider_count <= 1 else 0.65 if provider_count == 2 else 0.9
    base -= min(0.45, disagreement)
    if degraded:
        base -= 0.2
    return max(0.0, min(1.0, round(base, 4)))
