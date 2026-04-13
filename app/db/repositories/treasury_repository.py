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

    def list(self, limit: int, offset: int, status: str | None = None) -> list[TreasuryRequest]:
        stmt = select(TreasuryRequest).order_by(TreasuryRequest.created_at.desc()).limit(limit).offset(offset)
        if status:
            stmt = stmt.where(TreasuryRequest.status == status)
        return list(self.db.execute(stmt).scalars())

    def count(self, status: str | None = None) -> int:
        stmt = select(func.count()).select_from(TreasuryRequest)
        if status:
            stmt = stmt.where(TreasuryRequest.status == status)
        return int(self.db.execute(stmt).scalar_one())
