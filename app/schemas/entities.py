import json
from datetime import datetime

from pydantic import BaseModel, Field


class EntityOut(BaseModel):
    id: int
    name: str
    entity_type: str
    label: str
    description: str
    confidence: float
    source_ref_count: int
    provenance_score: float
    provenance_tier: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_model(cls, obj: object) -> "EntityOut":
        raw_refs = getattr(obj, "source_refs_json", "[]")
        try:
            parsed_refs = json.loads(raw_refs) if isinstance(raw_refs, str) else []
        except json.JSONDecodeError:
            parsed_refs = []

        source_ref_count = len(parsed_refs) if isinstance(parsed_refs, list) else 0
        confidence = float(getattr(obj, "confidence", 0.0))
        provenance_score = min(1.0, (confidence * 0.7) + (min(source_ref_count, 5) / 5 * 0.3))

        if provenance_score >= 0.8:
            tier = "high"
        elif provenance_score >= 0.5:
            tier = "medium"
        else:
            tier = "low"

        return cls(
            id=getattr(obj, "id"),
            name=getattr(obj, "name"),
            entity_type=getattr(obj, "entity_type"),
            label=getattr(obj, "label", ""),
            description=getattr(obj, "description", ""),
            confidence=confidence,
            source_ref_count=source_ref_count,
            provenance_score=round(provenance_score, 3),
            provenance_tier=tier,
            created_at=getattr(obj, "created_at"),
            updated_at=getattr(obj, "updated_at"),
        )


class WatchedEntityOut(BaseModel):
    id: int
    name: str
    entity_type: str
    label: str
    address: str
    watch_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProvenanceEntityDeltaOut(BaseModel):
    entity_id: int
    name: str
    old_confidence: float
    new_confidence: float
    drift: float


class ProvenanceRefreshOut(BaseModel):
    scanned: int
    updated: int
    drifted: int
    deltas: list[ProvenanceEntityDeltaOut] = Field(default_factory=list)

