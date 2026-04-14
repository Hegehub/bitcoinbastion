from datetime import datetime

from pydantic import BaseModel


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

    model_config = {"from_attributes": True}


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
