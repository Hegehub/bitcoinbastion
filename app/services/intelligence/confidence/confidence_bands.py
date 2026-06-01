def confidence_band(score: float) -> str:
    if score < 0.25:
        return "very_low"
    if score < 0.45:
        return "low"
    if score < 0.65:
        return "medium"
    if score < 0.85:
        return "high"
    return "very_high"
