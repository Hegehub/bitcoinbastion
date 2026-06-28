from __future__ import annotations

from datetime import datetime
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.metric_usage_event import MetricUsageEvent

SubjectKind = Literal["pass", "workspace", "api_key", "session"]
SUBJECT_COLUMNS: dict[SubjectKind, str] = {
    "pass": "pass_lookup_hash",
    "workspace": "workspace_id_hash",
    "api_key": "api_key_hash",
    "session": "session_id_hash",
}


class MetricUsageRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record_usage_event(self, event: MetricUsageEvent) -> MetricUsageEvent:
        self.session.add(event)
        self.session.flush()
        return event

    def record_many_usage_events(self, events: list[MetricUsageEvent]) -> list[MetricUsageEvent]:
        self.session.add_all(events)
        self.session.flush()
        return events

    def get_usage_summary(self, from_ts: datetime, to_ts: datetime) -> dict[str, int]:
        rows = self.session.execute(
            select(
                func.coalesce(func.sum(MetricUsageEvent.request_count), 0),
                func.coalesce(func.sum(MetricUsageEvent.credit_cost), 0),
                func.count(MetricUsageEvent.id),
            ).where(MetricUsageEvent.recorded_at >= from_ts, MetricUsageEvent.recorded_at <= to_ts)
        ).one()
        counts = self._decision_counts(from_ts, to_ts)
        return {
            "total_requests": int(rows[0] or 0),
            "total_credits": int(rows[1] or 0),
            "event_count": int(rows[2] or 0),
            "allowed": counts.get("allowed", 0),
            "denied": counts.get("denied", 0),
            "degraded": counts.get("degraded", 0),
            "cached": counts.get("cached", 0),
            "skipped": counts.get("skipped", 0),
        }

    def get_usage_by_metric_group(
        self, metric_group: str, from_ts: datetime, to_ts: datetime, limit: int = 100
    ) -> list[MetricUsageEvent]:
        return list(
            self.session.execute(
                select(MetricUsageEvent)
                .where(
                    MetricUsageEvent.metric_group == metric_group,
                    MetricUsageEvent.recorded_at >= from_ts,
                    MetricUsageEvent.recorded_at <= to_ts,
                )
                .order_by(MetricUsageEvent.recorded_at.desc(), MetricUsageEvent.id.desc())
                .limit(max(1, min(limit, 500)))
            ).scalars()
        )

    def get_usage_by_subject(
        self,
        subject_kind: SubjectKind,
        subject_hash: str,
        from_ts: datetime,
        to_ts: datetime,
        limit: int = 100,
    ) -> list[MetricUsageEvent]:
        column = getattr(MetricUsageEvent, SUBJECT_COLUMNS[subject_kind])
        return list(
            self.session.execute(
                select(MetricUsageEvent)
                .where(
                    column == subject_hash,
                    MetricUsageEvent.recorded_at >= from_ts,
                    MetricUsageEvent.recorded_at <= to_ts,
                )
                .order_by(MetricUsageEvent.recorded_at.desc(), MetricUsageEvent.id.desc())
                .limit(max(1, min(limit, 500)))
            ).scalars()
        )

    def get_credit_consumption(
        self, from_ts: datetime, to_ts: datetime, *, metric_group: str | None = None
    ) -> int:
        stmt = select(func.coalesce(func.sum(MetricUsageEvent.credit_cost), 0)).where(
            MetricUsageEvent.recorded_at >= from_ts,
            MetricUsageEvent.recorded_at <= to_ts,
        )
        if metric_group is not None:
            stmt = stmt.where(MetricUsageEvent.metric_group == metric_group)
        return int(self.session.scalar(stmt) or 0)

    def get_denial_summary(self, from_ts: datetime, to_ts: datetime) -> dict[str, int]:
        rows = self.session.execute(
            select(MetricUsageEvent.denial_reason, func.count(MetricUsageEvent.id))
            .where(
                MetricUsageEvent.recorded_at >= from_ts,
                MetricUsageEvent.recorded_at <= to_ts,
                MetricUsageEvent.decision.in_(["denied", "quota_exceeded", "policy_denied"]),
            )
            .group_by(MetricUsageEvent.denial_reason)
        ).all()
        return {str(reason or "unknown"): int(count) for reason, count in rows}

    def _decision_counts(self, from_ts: datetime, to_ts: datetime) -> dict[str, int]:
        rows = self.session.execute(
            select(
                MetricUsageEvent.decision,
                func.coalesce(func.sum(MetricUsageEvent.request_count), 0),
            )
            .where(MetricUsageEvent.recorded_at >= from_ts, MetricUsageEvent.recorded_at <= to_ts)
            .group_by(MetricUsageEvent.decision)
        ).all()
        return {str(decision): int(count or 0) for decision, count in rows}
