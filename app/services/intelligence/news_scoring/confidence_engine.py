def compute_confidence(
    source_credibility: float,
    keyword_strength: float,
    category_confidence: float,
    freshness: float,
    completeness: float,
    provider_health: float,
) -> float:
    score = (
        source_credibility * 0.30
        + keyword_strength * 0.20
        + category_confidence * 0.20
        + freshness * 0.15
        + completeness * 0.10
        + provider_health * 0.05
    )
    return max(0.0, min(1.0, score))


def calculate_confidence(
    provider_confidence: float, source_credibility: float, novelty: float
) -> float:
    return compute_confidence(source_credibility, novelty, novelty, 0.8, 0.8, provider_confidence)
