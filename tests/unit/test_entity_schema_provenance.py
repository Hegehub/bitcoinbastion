from datetime import UTC, datetime

from app.schemas.entities import EntityOut


class DummyEntity:
    def __init__(self, confidence: float, source_refs_json: str) -> None:
        now = datetime.now(UTC)
        self.id = 1
        self.name = "Example Cluster"
        self.entity_type = "exchange"
        self.label = "cluster"
        self.description = "desc"
        self.confidence = confidence
        self.source_refs_json = source_refs_json
        self.created_at = now
        self.updated_at = now


def test_entity_out_computes_high_provenance() -> None:
    item = DummyEntity(confidence=0.9, source_refs_json='["a", "b", "c", "d"]')

    out = EntityOut.from_model(item)

    assert out.source_ref_count == 4
    assert out.provenance_score >= 0.8
    assert out.provenance_tier == "high"


def test_entity_out_handles_invalid_source_refs_json() -> None:
    item = DummyEntity(confidence=0.2, source_refs_json='{"bad": true}')

    out = EntityOut.from_model(item)

    assert out.source_ref_count == 0
    assert out.provenance_tier == "low"
