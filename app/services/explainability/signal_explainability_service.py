from fastapi import HTTPException
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.db.repositories.signal_repository import SignalRepository
from app.schemas.signal import EvidenceEdgeOut, EvidenceNodeOut, SignalExplanationOut


class SignalExplainabilityService:
    def get_explanation(self, db: Session, signal_id: int) -> SignalExplanationOut:
        repo = SignalRepository(db)
        try:
            signal = repo.get(signal_id)
            if signal is None:
                raise HTTPException(status_code=404, detail="Signal not found")

            explanation = repo.latest_explanation(signal_id)
            if explanation is None:
                explanation = repo.create_default_explanation(signal)
            else:
                repo.ensure_evidence_graph(signal=signal)
                db.commit()

            nodes = [
                EvidenceNodeOut(
                    node_key=item.node_key,
                    node_type=item.node_type,
                    label=item.label,
                    weight=item.weight,
                )
                for item in repo.list_nodes(signal_id)
            ]
            edges = [
                EvidenceEdgeOut(
                    from_node_key=item.from_node_key,
                    to_node_key=item.to_node_key,
                    relation=item.relation,
                    weight=item.weight,
                )
                for item in repo.list_edges(signal_id)
            ]
            return SignalExplanationOut(
                signal_id=signal_id,
                explanation_text=explanation.explanation_text,
                confidence_reasoning=explanation.confidence_reasoning,
                horizon=explanation.horizon,
                generated_at=explanation.generated_at,
                nodes=nodes,
                edges=edges,
            )
        except OperationalError as exc:
            db.rollback()
            raise HTTPException(status_code=503, detail="Explainability storage is unavailable") from exc
