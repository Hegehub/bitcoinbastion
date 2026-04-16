from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.treasury import TreasuryRequest


class TreasuryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, item: TreasuryRequest) -> TreasuryRequest:
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(self, item: TreasuryRequest) -> TreasuryRequest:
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get(self, request_id: int) -> TreasuryRequest | None:
        stmt = select(TreasuryRequest).where(TreasuryRequest.id == request_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list(self, limit: int, offset: int, status: str | None = None) -> list[TreasuryRequest]:
        stmt = select(TreasuryRequest).order_by(TreasuryRequest.created_at.desc()).limit(limit).offset(offset)
        if status:
            stmt = stmt.where(TreasuryRequest.status == status)
        return list(self.db.execute(stmt).scalars())

    def list_pending_approvals(self, limit: int, offset: int) -> list[TreasuryRequest]:
        stmt = (
            select(TreasuryRequest)
            .where(TreasuryRequest.status.in_(["pending", "needs_review", "awaiting_approval"]))
            .order_by(TreasuryRequest.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars())

    def count(self, status: str | None = None) -> int:
        stmt = select(func.count()).select_from(TreasuryRequest)
        if status:
            stmt = stmt.where(TreasuryRequest.status == status)
        return int(self.db.execute(stmt).scalar_one())

    def count_pending_approvals(self) -> int:
        stmt = (
            select(func.count())
            .select_from(TreasuryRequest)
            .where(TreasuryRequest.status.in_(["pending", "needs_review", "awaiting_approval"]))
        )
        return int(self.db.execute(stmt).scalar_one())
