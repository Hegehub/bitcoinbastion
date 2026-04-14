from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SignalExplanation(Base):
    __tablename__ = "signal_explanations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    signal_id: Mapped[int] = mapped_column(ForeignKey("signals.id"), index=True)
    explanation_text: Mapped[str] = mapped_column(Text, default="")
    confidence_reasoning: Mapped[str] = mapped_column(Text, default="")
    horizon: Mapped[str] = mapped_column(String(40), default="short")
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EvidenceNode(Base):
    __tablename__ = "evidence_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    signal_id: Mapped[int] = mapped_column(ForeignKey("signals.id"), index=True)
    node_key: Mapped[str] = mapped_column(String(120), index=True)
    node_type: Mapped[str] = mapped_column(String(60), default="article")
    label: Mapped[str] = mapped_column(String(255), default="")
    weight: Mapped[float] = mapped_column(Float, default=0.0)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")


class EvidenceEdge(Base):
    __tablename__ = "evidence_edges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    signal_id: Mapped[int] = mapped_column(ForeignKey("signals.id"), index=True)
    from_node_key: Mapped[str] = mapped_column(String(120), index=True)
    to_node_key: Mapped[str] = mapped_column(String(120), index=True)
    relation: Mapped[str] = mapped_column(String(80), default="supports")
    weight: Mapped[float] = mapped_column(Float, default=0.0)
