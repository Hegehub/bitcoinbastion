from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateScoringInputs:
    relevance_score: float
    direction_match_score: float
    impact_alignment_score: float
    recency_score: float
    provider_confidence: float


@dataclass(frozen=True)
class ConfidenceResult:
    confidence_score: float
    confidence_band: str
    limitations: list[str]
