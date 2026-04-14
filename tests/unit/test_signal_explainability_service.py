from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.signal import Signal
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
