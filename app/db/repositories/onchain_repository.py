import json

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.onchain import OnchainEvent
from app.integrations.bitcoin.provider import ChainEvent


class OnchainRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add_event(
        self,
        event: ChainEvent,
        significance: float,
        confidence: float = 0.8,
        explainability: dict[str, float | str] | None = None,
        tags: list[str] | None = None,
    ) -> OnchainEvent:
        model = OnchainEvent(
            event_type=event.event_type,
            txid=event.txid,
            address=event.address,
            value_sats=event.value_sats,
            block_height=event.block_height,
            observed_at=event.observed_at,
            provider="mock",
            raw_payload_json=json.dumps(event.payload),
            significance_score=significance,
            confidence_score=confidence,
            explainability_json=json.dumps(explainability or {"reason": "threshold_transfer"}),
            tags_json=json.dumps(tags or [event.event_type]),
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def count(self) -> int:
        stmt = select(func.count(OnchainEvent.id))
        try:
            return int(self.db.execute(stmt).scalar_one())
        except SQLAlchemyError:
            return 0

    def recent(self, limit: int = 50, offset: int = 0) -> list[OnchainEvent]:
        stmt = select(OnchainEvent).order_by(OnchainEvent.observed_at.desc()).limit(limit).offset(offset)
        try:
            return list(self.db.execute(stmt).scalars())
        except SQLAlchemyError:
            return []

    def latest_block_height(self) -> int | None:
        stmt = select(func.max(OnchainEvent.block_height))
        try:
            value = self.db.execute(stmt).scalar_one()
        except SQLAlchemyError:
            return None
        if value is None:
            return None
        return int(value)
