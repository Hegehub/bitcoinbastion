from pydantic import BaseModel


class ImpactConfidenceResult(BaseModel):
    confidence_score: float
    confidence_band: str
    confidence_contributions: list[dict[str, object]]
    degradation_factors: list[str]
    uncertainty_flags: list[str]
    freshness_weight: float
    provider_confidence: float
    direction_match: bool
    delayed_reaction_detected: bool
    false_signal_detected: bool
    explanation_summary: str
    limitation: str
