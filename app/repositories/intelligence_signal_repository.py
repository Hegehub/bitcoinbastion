from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.intelligence_signals import (
    IntelligenceOperatorReview,
    IntelligencePublishingPolicy,
    IntelligenceSignalCandidate,
    IntelligenceSignalDeliveryLog,
)


class IntelligenceSignalRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add_candidate(self, candidate: IntelligenceSignalCandidate) -> IntelligenceSignalCandidate:
        self.db.add(candidate)
        self.db.flush()
        return candidate

    def get_candidate(self, signal_id: int) -> IntelligenceSignalCandidate | None:
        return self.db.get(IntelligenceSignalCandidate, signal_id)

    def list_candidates(
        self, *, status: str | None = None, signal_type: str | None = None, limit: int = 50
    ) -> list[IntelligenceSignalCandidate]:
        query = self.db.query(IntelligenceSignalCandidate)
        if status is not None:
            query = query.filter(IntelligenceSignalCandidate.status == status)
        if signal_type is not None:
            query = query.filter(IntelligenceSignalCandidate.signal_type == signal_type)
        return query.order_by(IntelligenceSignalCandidate.created_at.desc(), IntelligenceSignalCandidate.id.desc()).limit(limit).all()

    def duplicate_count(self, candidate: IntelligenceSignalCandidate) -> int:
        query = self.db.query(IntelligenceSignalCandidate).filter(
            IntelligenceSignalCandidate.signal_type == candidate.signal_type,
            IntelligenceSignalCandidate.source_entity_type == candidate.source_entity_type,
            IntelligenceSignalCandidate.source_entity_id == candidate.source_entity_id,
        )
        if candidate.id is not None:
            query = query.filter(IntelligenceSignalCandidate.id != candidate.id)
        return int(query.count())

    def add_review(self, review: IntelligenceOperatorReview) -> IntelligenceOperatorReview:
        self.db.add(review)
        self.db.flush()
        return review

    def reviews_for(self, signal_id: int) -> list[IntelligenceOperatorReview]:
        return (
            self.db.query(IntelligenceOperatorReview)
            .filter(IntelligenceOperatorReview.signal_candidate_id == signal_id)
            .order_by(IntelligenceOperatorReview.created_at.desc(), IntelligenceOperatorReview.id.desc())
            .all()
        )

    def active_policy(self) -> IntelligencePublishingPolicy:
        policy = (
            self.db.query(IntelligencePublishingPolicy)
            .filter(IntelligencePublishingPolicy.is_active.is_(True))
            .order_by(IntelligencePublishingPolicy.id.asc())
            .first()
        )
        if policy is None:
            policy = IntelligencePublishingPolicy(name="default", is_active=True, allow_auto_publish=False)
            self.db.add(policy)
            self.db.flush()
        return policy

    def add_delivery_log(self, row: IntelligenceSignalDeliveryLog) -> IntelligenceSignalDeliveryLog:
        self.db.add(row)
        self.db.flush()
        return row

    def delivery_logs_for(self, signal_id: int) -> list[IntelligenceSignalDeliveryLog]:
        return (
            self.db.query(IntelligenceSignalDeliveryLog)
            .filter(IntelligenceSignalDeliveryLog.signal_candidate_id == signal_id)
            .order_by(IntelligenceSignalDeliveryLog.created_at.desc(), IntelligenceSignalDeliveryLog.id.desc())
            .all()
        )
