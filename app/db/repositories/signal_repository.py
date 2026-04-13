from sqlalchemy import select
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

    def top(self, limit: int = 10) -> list[Signal]:
        stmt = select(Signal).order_by(Signal.score.desc()).limit(limit)
        return list(self.db.execute(stmt).scalars())
