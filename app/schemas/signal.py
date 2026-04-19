import json
from datetime import datetime

from pydantic import BaseModel
from pydantic import Field

from app.schemas.common import ExplainabilityOut, FreshnessOut


class SignalOut(BaseModel):
    id: int
    signal_type: str
    severity: str
    score: float
    confidence: float
    title: str
    summary: str
    is_published: bool
    created_at: datetime
    horizons: dict[str, float | str] = {}
    explainability: ExplainabilityOut = Field(default_factory=ExplainabilityOut)
    freshness: FreshnessOut = Field(default_factory=FreshnessOut)

    model_config = {"from_attributes": True}

    @classmethod
    def from_model_with_horizons(cls, obj: object) -> "SignalOut":
        data = cls.model_validate(obj)
        raw_explainability = getattr(obj, "explainability_json", "{}")
        try:
            parsed = json.loads(raw_explainability) if isinstance(raw_explainability, str) else {}
        except json.JSONDecodeError:
            parsed = {}
        horizons = parsed.get("horizons") if isinstance(parsed, dict) else {}
        data.horizons = horizons if isinstance(horizons, dict) else {}
        return data


class EvidenceNodeOut(BaseModel):
    node_key: str
    node_type: str
    label: str
    weight: float


class EvidenceEdgeOut(BaseModel):
    from_node_key: str
    to_node_key: str
    relation: str
    weight: float


class SignalExplanationOut(BaseModel):
    signal_id: int
    explanation_text: str
    confidence_reasoning: str
    horizon: str
    generated_at: datetime
    nodes: list[EvidenceNodeOut]
    edges: list[EvidenceEdgeOut]
    data_sources: list[str] = Field(default_factory=list)
