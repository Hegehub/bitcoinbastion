import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.onchain import OnchainEvent
from app.integrations.bitcoin.provider import ChainEvent


class OnchainRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add_event(self, event: ChainEvent, significance: float) -> OnchainEvent:
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
            confidence_score=0.8,
            explainability_json=json.dumps({"rule": "threshold_transfer"}),
            tags_json=json.dumps([event.event_type]),
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def recent(self, limit: int = 50) -> list[OnchainEvent]:
        stmt = select(OnchainEvent).order_by(OnchainEvent.observed_at.desc()).limit(limit)
        return list(self.db.execute(stmt).scalars())
