from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.signal import Signal


class SignalRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, signal: Signal) -> Signal:
        self.db.add(signal)
        self.db.commit()
        self.db.refresh(signal)
        return signal

    def top(self, limit: int = 10, offset: int = 0) -> list[Signal]:
        stmt = select(Signal).order_by(Signal.score.desc()).limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars())

    def count(self) -> int:
        stmt = select(func.count()).select_from(Signal)
        return int(self.db.execute(stmt).scalar_one())
