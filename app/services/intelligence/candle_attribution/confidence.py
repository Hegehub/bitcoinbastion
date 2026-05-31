from app.services.intelligence.candle_attribution.schemas import CandidateScoringInputs, ConfidenceResult


class CandleAttributionConfidenceBuilder:
    def build(self, inputs: CandidateScoringInputs, event_density: int, volatility_penalty: float, limitations: list[str]) -> ConfidenceResult:
        base = (
            inputs.relevance_score
            * inputs.direction_match_score
            * inputs.impact_alignment_score
            * inputs.recency_score
            * inputs.provider_confidence
        )
        density_penalty = 0.9 if event_density > 3 else 1.0
        score = max(0.0, min(1.0, base * density_penalty * max(0.0, min(1.0, volatility_penalty))))
        if score < 0.45:
            band = "LOW"
        elif score < 0.7:
            band = "MEDIUM"
        else:
            band = "HIGH"
        return ConfidenceResult(confidence_score=score, confidence_band=band, limitations=limitations)
