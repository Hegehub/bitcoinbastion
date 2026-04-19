from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.explainability import EvidenceNode, SignalExplanation
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
    assert any(item.relation == "self" for item in result.edges)


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


def test_existing_explanation_backfills_graph_nodes_when_missing() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        signal = Signal(
            signal_type="news",
            title="Backfill graph signal",
            score=0.66,
            confidence=0.64,
            explainability_json="{}",
        )
        signal = SignalRepository(db).add_with_source(
            signal=signal,
            source_type="news",
            source_id="existing-explanation-1",
            weight=1.0,
        )
        db.add(
            SignalExplanation(
                signal_id=signal.id,
                explanation_text="precomputed explanation",
                confidence_reasoning="precomputed confidence",
                horizon="short",
            )
        )
        db.commit()

        result = SignalExplainabilityService().get_explanation(db=db, signal_id=signal.id)

    assert result.explanation_text == "precomputed explanation"
    assert any(item.node_type == "source" for item in result.nodes)
    assert any(item.relation == "supports" for item in result.edges)


def test_existing_partial_graph_is_reconciled_with_missing_source_edges() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        signal = Signal(
            signal_type="news",
            title="Partial graph signal",
            score=0.61,
            confidence=0.6,
            explainability_json="{}",
        )
        signal = SignalRepository(db).add_with_source(
            signal=signal,
            source_type="news",
            source_id="partial-graph-1",
            weight=1.0,
        )
        db.add(
            SignalExplanation(
                signal_id=signal.id,
                explanation_text="existing explanation",
                confidence_reasoning="existing confidence",
                horizon="short",
            )
        )
        db.commit()

        db.add(
            EvidenceNode(
                signal_id=signal.id,
                node_key=f"signal:{signal.id}",
                node_type="signal",
                label=signal.title,
                weight=signal.score,
            )
        )
        db.commit()

        result = SignalExplainabilityService().get_explanation(db=db, signal_id=signal.id)

    assert any(item.node_key == "source:news" for item in result.nodes)
    assert any(item.relation == "supports" and item.from_node_key == "source:news" for item in result.edges)
