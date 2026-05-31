from datetime import datetime

from app.services.intelligence.candle_attribution.schemas import CandidateScoringInputs


class CandleAttributionCandidateBuilder:
    def build_inputs(
        self,
        relevance_score: float,
        direction_match_score: float,
        impact_alignment_score: float,
        event_time: datetime,
        reference_time: datetime,
        provider_confidence: float,
    ) -> CandidateScoringInputs:
        distance_seconds = abs((reference_time - event_time).total_seconds())
        recency_score = max(0.0, min(1.0, 0.5 ** ((distance_seconds / 60.0) / 120.0)))
        return CandidateScoringInputs(
            relevance_score=max(0.0, min(1.0, relevance_score)),
            direction_match_score=max(0.0, min(1.0, direction_match_score)),
            impact_alignment_score=max(0.0, min(1.0, impact_alignment_score)),
            recency_score=recency_score,
            provider_confidence=max(0.0, min(1.0, provider_confidence)),
        )
