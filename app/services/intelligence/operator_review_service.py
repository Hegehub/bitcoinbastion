from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.intelligence_signals import IntelligenceOperatorReview
from app.db.models.time_utils import utcnow
from app.repositories.intelligence_signal_repository import IntelligenceSignalRepository
from app.schemas.intelligence_signals import SIGNAL_LIMITATIONS
from app.services.intelligence.signal_governance_metrics import (
    INTELLIGENCE_OPERATOR_REVIEWS_TOTAL,
    INTELLIGENCE_SIGNAL_REJECTED_TOTAL,
)


class OperatorReviewService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = IntelligenceSignalRepository(db)

    def review(
        self,
        signal_id: int,
        review_status: str,
        *,
        reviewer_id: int | None = None,
        operator_note: str = "",
        decision_reason: str = "",
        false_positive_marker: bool = False,
        confidence_override: float | None = None,
        publish_override: bool = False,
    ) -> IntelligenceOperatorReview:
        candidate = self.repo.get_candidate(signal_id)
        if candidate is None:
            raise ValueError("signal_candidate_not_found")
        row = IntelligenceOperatorReview(
            signal_candidate_id=signal_id,
            review_status=review_status,
            reviewer_id=reviewer_id,
            operator_note=operator_note,
            decision_reason=decision_reason,
            false_positive_marker=false_positive_marker,
            confidence_override=confidence_override,
            publish_override=publish_override,
        )
        self.repo.add_review(row)
        candidate.status = self._candidate_status(review_status)
        candidate.requires_operator_review = review_status in {"pending", "held", "needs_more_evidence", "false_positive"}
        if review_status == "approved" and publish_override:
            candidate.status = "published"
            candidate.published_at = utcnow()
        if review_status in {"rejected", "false_positive"}:
            INTELLIGENCE_SIGNAL_REJECTED_TOTAL.labels(signal_type=self._bounded_type(candidate.signal_type), reason_code=self._bounded_reason(review_status)).inc()
        INTELLIGENCE_OPERATOR_REVIEWS_TOTAL.labels(status=self._bounded_review(review_status)).inc()
        self.db.flush()
        return row

    def payload(self, row: IntelligenceOperatorReview) -> dict[str, object]:
        return {
            "id": row.id,
            "signal_candidate_id": row.signal_candidate_id,
            "review_status": row.review_status,
            "reviewer_id": row.reviewer_id,
            "operator_note": row.operator_note,
            "decision_reason": row.decision_reason,
            "false_positive_marker": row.false_positive_marker,
            "confidence_override": row.confidence_override,
            "publish_override": row.publish_override,
            "limitations": SIGNAL_LIMITATIONS.copy(),
        }

    def _candidate_status(self, review_status: str) -> str:
        return {
            "approved": "approved",
            "rejected": "rejected",
            "held": "held",
            "needs_more_evidence": "held",
            "false_positive": "rejected",
        }.get(review_status, "pending_review")

    def _bounded_review(self, value: str) -> str:
        return value if value in {"pending", "approved", "rejected", "held", "needs_more_evidence", "false_positive"} else "other"

    def _bounded_type(self, value: str) -> str:
        return value if value in {"news_market_impact", "candle_attribution", "delayed_reaction", "false_signal", "security_shock", "regulatory_risk", "macro_shock", "narrative_spike", "news_shock_index"} else "other"

    def _bounded_reason(self, value: str) -> str:
        return value if value in {"rejected", "false_positive"} else "other"
