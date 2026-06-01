def uncertainty_flags(provider_confidence: float, provider_count: int, stale: bool, high_volatility: bool, simultaneous_events: int) -> list[str]:
    flags: list[str] = []
    if provider_confidence < 0.5:
        flags.append("provider_disagreement")
    if provider_count <= 1:
        flags.append("single_source_dependency")
    if stale:
        flags.append("stale_data")
    if high_volatility:
        flags.append("high_noise_environment")
    if simultaneous_events > 1:
        flags.append("multiple_simultaneous_events")
    return flags
