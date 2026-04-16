from pydantic import BaseModel, Field


class RecommendationItemOut(BaseModel):
    priority: str
    horizon: str
    action: str
    rationale: str
    evidence_refs: list[str] = Field(default_factory=list)
    policy_refs: list[str] = Field(default_factory=list)
    evidence_paths: list[str] = Field(default_factory=list)
    action_confidence: float = 0.0


class SignalRecommendationOut(BaseModel):
    signal_id: int
    generated_by: str
    recommendations: list[RecommendationItemOut]
