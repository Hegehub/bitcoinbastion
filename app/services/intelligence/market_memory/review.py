from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.db.models.market_memory_operator_review import MarketMemoryOperatorReview
from app.db.models.market_pattern import MarketPattern
from app.services.intelligence.market_memory_service import MarketMemoryService


class OperatorReviewService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.memory = MarketMemoryService(db)

    def record_review(
        self,
        *,
        event_id: int,
        pattern: str | int | None = None,
        action: str,
        approved: bool | None = None,
        override_confidence: float | None = None,
        notes: str = "",
        similar_event_id: int | None = None,
        false_similarity: bool = False,
        operator: str = "system",
    ) -> MarketMemoryOperatorReview:
        pattern_row: MarketPattern | None = self.memory.get_pattern(pattern) if pattern is not None else None
        row = MarketMemoryOperatorReview(
            event_id=event_id,
            pattern_id=pattern_row.id if pattern_row else None,
            similar_event_id=similar_event_id,
            action=action,
            approved=approved,
            override_confidence=override_confidence,
            notes=notes,
            false_similarity=false_similarity,
            audit_json={
                "operator": operator,
                "action": action,
                "pattern": pattern,
                "approved": approved,
                "override_confidence": override_confidence,
                "false_similarity": false_similarity,
            },
        )
        self.db.add(row)
        self.db.flush()
        return row

    def payload(self, row: MarketMemoryOperatorReview) -> dict[str, Any]:
        return {
            "id": row.id,
            "event_id": row.event_id,
            "pattern_id": row.pattern_id,
            "similar_event_id": row.similar_event_id,
            "action": row.action,
            "approved": row.approved,
            "override_confidence": row.override_confidence,
            "notes": row.notes,
            "false_similarity": row.false_similarity,
            "audit": row.audit_json,
            "created_at": row.created_at,
        }
