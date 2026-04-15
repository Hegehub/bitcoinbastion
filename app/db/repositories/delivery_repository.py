import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.delivery import DeliveryLog


class DeliveryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def already_sent(self, *, signal_id: int, destination: str) -> bool:
        stmt = (
            select(func.count())
            .select_from(DeliveryLog)
            .where(DeliveryLog.signal_id == signal_id)
            .where(DeliveryLog.destination == destination)
            .where(DeliveryLog.delivery_status == "sent")
        )
        return int(self.db.execute(stmt).scalar_one()) > 0

    def record_sent(
        self,
        *,
        signal_id: int,
        destination: str,
        payload_snapshot: dict[str, str | int | float],
        provider_message_id: str = "simulated",
    ) -> DeliveryLog:
        item = DeliveryLog(
            signal_id=signal_id,
            channel_type="telegram",
            destination=destination,
            provider_message_id=provider_message_id,
            delivery_status="sent",
            payload_snapshot_json=json.dumps(payload_snapshot),
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def sent_count_last_24h(self) -> int:
        since = datetime.now(UTC) - timedelta(hours=24)
        stmt = (
            select(func.count())
            .select_from(DeliveryLog)
            .where(DeliveryLog.delivery_status == "sent")
            .where(DeliveryLog.sent_at >= since)
        )
        try:
            return int(self.db.execute(stmt).scalar_one())
        except SQLAlchemyError:
            return 0

    def failed_count_last_24h(self) -> int:
        since = datetime.now(UTC) - timedelta(hours=24)
        stmt = (
            select(func.count())
            .select_from(DeliveryLog)
            .where(DeliveryLog.delivery_status.in_(["failed", "error"]))
            .where(DeliveryLog.sent_at >= since)
        )
        try:
            return int(self.db.execute(stmt).scalar_one())
        except SQLAlchemyError:
            return 0
