from pydantic import BaseModel


class SourceReputationResponse(BaseModel):
    source_id: int
    reliability_score: float
    signal_quality_score: float
