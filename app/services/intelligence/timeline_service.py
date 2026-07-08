from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.intelligence_timeline import IntelligenceTimelineEvent
from app.services.intelligence.timeline_deduplication import dedup_key


class TimelineService:
    def create_timeline_event(
        self, db: Session, payload: dict[str, object]
    ) -> IntelligenceTimelineEvent:
        e = IntelligenceTimelineEvent(**payload)
        db.add(e)
        db.commit()
        db.refresh(e)
        return e

    def store_normalized_event(
        self, db: Session, payload: dict[str, object]
    ) -> IntelligenceTimelineEvent | None:
        key = dedup_key(
            str(payload["event_type"]),
            str(payload["event_time"]),
            str(payload.get("title", "")),
            {},
        )
        exists = db.execute(
            select(IntelligenceTimelineEvent).where(
                IntelligenceTimelineEvent.metadata_json["dedup_key"].as_string() == key
            )
        ).scalar_one_or_none()
        if exists:
            return None
        payload.setdefault("metadata_json", {})
        metadata_json = payload["metadata_json"]
        if isinstance(metadata_json, dict):
            metadata_json["dedup_key"] = key
        return self.create_timeline_event(db, payload)

    def bulk_store(self, db: Session, payloads: list[dict[str, object]]) -> int:
        n = 0
        for p in payloads:
            n += 1 if self.store_normalized_event(db, p) else 0
        return n

    def get_timeline(
        self, db: Session, limit: int = 100, event_type: str | None = None
    ) -> list[IntelligenceTimelineEvent]:
        q = select(IntelligenceTimelineEvent).where(IntelligenceTimelineEvent.is_deleted.is_(False))
        if event_type:
            q = q.where(IntelligenceTimelineEvent.event_type == event_type)
        q = q.order_by(
            IntelligenceTimelineEvent.event_time.desc(), IntelligenceTimelineEvent.id.desc()
        ).limit(limit)
        return list(db.execute(q).scalars())

    def get_window(
        self, db: Session, start: datetime, end: datetime, limit: int = 500
    ) -> list[IntelligenceTimelineEvent]:
        q = (
            select(IntelligenceTimelineEvent)
            .where(
                IntelligenceTimelineEvent.event_time >= start,
                IntelligenceTimelineEvent.event_time <= end,
            )
            .order_by(
                IntelligenceTimelineEvent.event_time.asc(), IntelligenceTimelineEvent.id.asc()
            )
            .limit(limit)
        )
        return list(db.execute(q).scalars())

    def get_latest(self, db: Session, limit: int = 20) -> list[IntelligenceTimelineEvent]:
        return self.get_timeline(db, limit=limit)

    def get_related_events(
        self, db: Session, event_id: int, limit: int = 50
    ) -> list[IntelligenceTimelineEvent]:
        base = db.get(IntelligenceTimelineEvent, event_id)
        if base is None:
            return []
        return self.get_window(
            db, base.event_time.replace(second=0), base.event_time.replace(second=59), limit
        )

    def get_event_context(self, db: Session, event_id: int) -> dict[str, object]:
        base = db.get(IntelligenceTimelineEvent, event_id)
        if base is None:
            return {"event": None, "related": []}
        rel = self.get_related_events(db, event_id)
        return {"event": base, "related": rel}

    def build_replay_window(
        self, db: Session, start: datetime, end: datetime
    ) -> list[IntelligenceTimelineEvent]:
        return self.get_window(db, start, end)
