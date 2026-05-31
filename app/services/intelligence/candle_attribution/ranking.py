from app.services.intelligence.candle_attribution.schemas import CandidateScoringInputs


class CandleAttributionRankingEngine:
    def raw_score(self, inputs: CandidateScoringInputs) -> float:
        score = (
            inputs.relevance_score
            * inputs.direction_match_score
            * inputs.impact_alignment_score
            * inputs.recency_score
            * inputs.provider_confidence
        )
        return max(0.0, min(1.0, score))

    def normalize(self, scores: list[float]) -> list[float]:
        max_score = max(scores, default=1.0) or 1.0
        return [max(0.0, min(1.0, score / max_score)) for score in scores]
