from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.wallet import WalletProfile


class WalletRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_user(self, user_id: int, limit: int, offset: int) -> list[WalletProfile]:
        stmt = (
            select(WalletProfile)
            .where(WalletProfile.user_id == user_id)
            .order_by(WalletProfile.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars())

    def count_by_user(self, user_id: int) -> int:
        stmt = select(func.count()).select_from(WalletProfile).where(WalletProfile.user_id == user_id)
        return int(self.db.execute(stmt).scalar_one())
