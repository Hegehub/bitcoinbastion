from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.signal import Signal
from app.db.repositories.signal_repository import SignalRepository
from app.services.explainability.signal_explainability_service import SignalExplainabilityService


def test_signal_explanation_is_generated_when_missing() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        signal = Signal(
            signal_type="news",
            title="Test signal",
            score=0.92,
            confidence=0.81,
            explainability_json='{"reason":"Derived from clustered high-impact coverage."}',
        )
        db.add(signal)
        db.commit()
        db.refresh(signal)
        signal_id = signal.id

        result = SignalExplainabilityService().get_explanation(db=db, signal_id=signal_id)

    assert result.signal_id == signal_id
    assert "Derived from clustered" in result.explanation_text
    assert len(result.nodes) == 1


def test_default_explanation_adds_cross_source_narrative_and_graph_nodes() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        signal = Signal(
            signal_type="onchain",
            title="Cross-source signal",
            score=0.77,
            confidence=0.74,
            explainability_json="{}",
        )
        signal = SignalRepository(db).add_with_source(
            signal=signal,
            source_type="news",
            source_id="article-1",
            weight=0.8,
        )
        signal_id = signal.id

        result = SignalExplainabilityService().get_explanation(db=db, signal_id=signal_id)

    assert result.signal_id == signal_id
    assert "evidence from news(1)" in result.explanation_text
    assert "linked source reference" in result.confidence_reasoning
    assert any(item.node_type == "source" for item in result.nodes)
    assert any(item.relation == "supports" for item in result.edges)
