import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.explainability import EvidenceEdge, EvidenceNode, SignalExplanation
from app.db.models.signal import Signal


class SignalRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, signal: Signal) -> Signal:
        self.db.add(signal)
        self.db.commit()
        self.db.refresh(signal)
        return signal

    def get(self, signal_id: int) -> Signal | None:
        stmt = select(Signal).where(Signal.id == signal_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def top(self, limit: int = 10, offset: int = 0) -> list[Signal]:
        stmt = select(Signal).order_by(Signal.score.desc()).limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars())

    def count(self) -> int:
        stmt = select(func.count()).select_from(Signal)
        return int(self.db.execute(stmt).scalar_one())

    def latest_explanation(self, signal_id: int) -> SignalExplanation | None:
        stmt = (
            select(SignalExplanation)
            .where(SignalExplanation.signal_id == signal_id)
            .order_by(SignalExplanation.generated_at.desc())
        )
        return self.db.execute(stmt).scalars().first()

    def list_nodes(self, signal_id: int) -> list[EvidenceNode]:
        stmt = select(EvidenceNode).where(EvidenceNode.signal_id == signal_id).order_by(EvidenceNode.id.asc())
        return list(self.db.execute(stmt).scalars())

    def list_edges(self, signal_id: int) -> list[EvidenceEdge]:
        stmt = select(EvidenceEdge).where(EvidenceEdge.signal_id == signal_id).order_by(EvidenceEdge.id.asc())
        return list(self.db.execute(stmt).scalars())

    def create_default_explanation(self, signal: Signal) -> SignalExplanation:
        payload = json.loads(signal.explainability_json or "{}")
        explanation = SignalExplanation(
            signal_id=signal.id,
            explanation_text=payload.get(
                "reason",
                f"Signal '{signal.title}' was generated from current scoring inputs.",
            ),
            confidence_reasoning=payload.get(
                "confidence_reasoning",
                "Confidence combines relevance, impact and source quality features.",
            ),
            horizon=payload.get("horizon", "short"),
        )
        self.db.add(explanation)

        if not self.list_nodes(signal.id):
            self.db.add(
                EvidenceNode(
                    signal_id=signal.id,
                    node_key=f"signal:{signal.id}",
                    node_type="signal",
                    label=signal.title,
                    weight=signal.score,
                )
            )
        self.db.commit()
        self.db.refresh(explanation)
        return explanation
