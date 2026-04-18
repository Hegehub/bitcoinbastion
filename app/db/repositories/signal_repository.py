import json
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.explainability import EvidenceEdge, EvidenceNode, SignalExplanation
from app.db.models.signal import Signal
from app.db.models.signal_link import SignalSourceLink


class SignalRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, signal: Signal) -> Signal:
        self.db.add(signal)
        self.db.commit()
        self.db.refresh(signal)
        return signal

    def add_with_source(self, *, signal: Signal, source_type: str, source_id: str, weight: float = 1.0) -> Signal:
        self.db.add(signal)
        self.db.flush()
        self.db.add(
            SignalSourceLink(
                signal_id=signal.id,
                source_type=source_type,
                source_id=source_id,
                weight=weight,
            )
        )
        self.db.commit()
        self.db.refresh(signal)
        return signal

    def has_source_link(self, *, source_type: str, source_id: str) -> bool:
        stmt = (
            select(func.count(SignalSourceLink.id))
            .where(SignalSourceLink.source_type == source_type)
            .where(SignalSourceLink.source_id == source_id)
        )
        try:
            return int(self.db.execute(stmt).scalar_one()) > 0
        except SQLAlchemyError:
            return False

    def get(self, signal_id: int) -> Signal | None:
        stmt = select(Signal).where(Signal.id == signal_id)
        try:
            return self.db.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError:
            return None

    def top(self, limit: int = 10, offset: int = 0, horizon: str | None = None) -> list[Signal]:
        stmt = select(Signal).order_by(Signal.score.desc())
        try:
            if horizon is None:
                stmt = stmt.limit(limit).offset(offset)
                return list(self.db.execute(stmt).scalars())

            # Horizon is currently persisted in explainability_json; filter in-memory.
            candidates = list(self.db.execute(stmt.limit(500)).scalars())
            filtered = [item for item in candidates if self._dominant_horizon(item) == horizon]
            return filtered[offset : offset + limit]
        except SQLAlchemyError:
            return []

    def count(self) -> int:
        stmt = select(func.count()).select_from(Signal)
        try:
            return int(self.db.execute(stmt).scalar_one())
        except SQLAlchemyError:
            return 0

    def unpublished(self, limit: int = 20) -> list[Signal]:
        stmt = (
            select(Signal)
            .where(Signal.is_published.is_(False))
            .order_by(Signal.score.desc(), Signal.created_at.asc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars())

    def mark_published(self, signal_id: int) -> None:
        signal = self.get(signal_id)
        if signal is None:
            return

        signal.is_published = True
        signal.status = "published"
        signal.published_at = datetime.now(UTC)
        self.db.commit()

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

    @staticmethod
    def _dominant_horizon(signal: Signal) -> str | None:
        try:
            parsed = json.loads(signal.explainability_json or "{}")
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, dict):
            horizons = parsed.get("horizons")
            if isinstance(horizons, dict) and isinstance(horizons.get("dominant"), str):
                return str(horizons.get("dominant"))
            raw = parsed.get("horizon")
            if isinstance(raw, str):
                return raw
        return None
