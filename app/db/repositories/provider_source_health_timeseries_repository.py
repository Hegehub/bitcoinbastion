from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.provider_source_health_timeseries import (
    ProviderConfidenceTimeSeriesEvent,
    ProviderHealthTimeSeriesSnapshot,
    SourceConfidenceTimeSeriesEvent,
    SourceHealthTimeSeriesSnapshot,
)

MAX_HISTORY_LIMIT = 500
DEFAULT_HISTORY_LIMIT = 100


def _bounded_limit(limit: int | None) -> int:
    if limit is None:
        return DEFAULT_HISTORY_LIMIT
    return max(1, min(int(limit), MAX_HISTORY_LIMIT))


class ProviderSourceHealthTimeSeriesRepository:
    """Repository for bounded provider/source health time-series observations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def record_provider_snapshot(self, **values: Any) -> ProviderHealthTimeSeriesSnapshot:
        snapshot = ProviderHealthTimeSeriesSnapshot(**values)
        self.session.add(snapshot)
        self.session.flush()
        return snapshot

    def record_source_snapshot(self, **values: Any) -> SourceHealthTimeSeriesSnapshot:
        snapshot = SourceHealthTimeSeriesSnapshot(**values)
        self.session.add(snapshot)
        self.session.flush()
        return snapshot

    def record_provider_confidence_event(self, **values: Any) -> ProviderConfidenceTimeSeriesEvent:
        event = ProviderConfidenceTimeSeriesEvent(**values)
        self.session.add(event)
        self.session.flush()
        return event

    def record_source_confidence_event(self, **values: Any) -> SourceConfidenceTimeSeriesEvent:
        event = SourceConfidenceTimeSeriesEvent(**values)
        self.session.add(event)
        self.session.flush()
        return event

    def latest_provider_snapshot(
        self, provider_key: str
    ) -> ProviderHealthTimeSeriesSnapshot | None:
        return self.session.execute(
            select(ProviderHealthTimeSeriesSnapshot)
            .where(ProviderHealthTimeSeriesSnapshot.provider_key == provider_key)
            .order_by(
                ProviderHealthTimeSeriesSnapshot.observed_at.desc(),
                ProviderHealthTimeSeriesSnapshot.id.desc(),
            )
            .limit(1)
        ).scalar_one_or_none()

    def latest_source_snapshot(self, source_key: str) -> SourceHealthTimeSeriesSnapshot | None:
        return self.session.execute(
            select(SourceHealthTimeSeriesSnapshot)
            .where(SourceHealthTimeSeriesSnapshot.source_key == source_key)
            .order_by(
                SourceHealthTimeSeriesSnapshot.observed_at.desc(),
                SourceHealthTimeSeriesSnapshot.id.desc(),
            )
            .limit(1)
        ).scalar_one_or_none()

    def provider_history(
        self,
        provider_key: str,
        from_ts: datetime,
        to_ts: datetime,
        limit: int | None = None,
        *,
        domain: str | None = None,
        status: str | None = None,
        is_degraded: bool | None = None,
    ) -> list[ProviderHealthTimeSeriesSnapshot]:
        stmt = select(ProviderHealthTimeSeriesSnapshot).where(
            ProviderHealthTimeSeriesSnapshot.provider_key == provider_key,
            ProviderHealthTimeSeriesSnapshot.observed_at >= from_ts,
            ProviderHealthTimeSeriesSnapshot.observed_at <= to_ts,
        )
        if domain is not None:
            stmt = stmt.where(ProviderHealthTimeSeriesSnapshot.domain == domain)
        if status is not None:
            stmt = stmt.where(ProviderHealthTimeSeriesSnapshot.status == status)
        if is_degraded is not None:
            stmt = stmt.where(ProviderHealthTimeSeriesSnapshot.is_degraded == is_degraded)
        return list(
            self.session.execute(
                stmt.order_by(
                    ProviderHealthTimeSeriesSnapshot.observed_at.desc(),
                    ProviderHealthTimeSeriesSnapshot.id.desc(),
                ).limit(_bounded_limit(limit))
            ).scalars()
        )

    def source_history(
        self,
        source_key: str,
        from_ts: datetime,
        to_ts: datetime,
        limit: int | None = None,
        *,
        domain: str | None = None,
        status: str | None = None,
        is_degraded: bool | None = None,
    ) -> list[SourceHealthTimeSeriesSnapshot]:
        stmt = select(SourceHealthTimeSeriesSnapshot).where(
            SourceHealthTimeSeriesSnapshot.source_key == source_key,
            SourceHealthTimeSeriesSnapshot.observed_at >= from_ts,
            SourceHealthTimeSeriesSnapshot.observed_at <= to_ts,
        )
        if domain is not None:
            stmt = stmt.where(SourceHealthTimeSeriesSnapshot.domain == domain)
        if status is not None:
            stmt = stmt.where(SourceHealthTimeSeriesSnapshot.status == status)
        if is_degraded is not None:
            stmt = stmt.where(SourceHealthTimeSeriesSnapshot.is_degraded == is_degraded)
        return list(
            self.session.execute(
                stmt.order_by(
                    SourceHealthTimeSeriesSnapshot.observed_at.desc(),
                    SourceHealthTimeSeriesSnapshot.id.desc(),
                ).limit(_bounded_limit(limit))
            ).scalars()
        )

    def degraded_providers(
        self, since: datetime, limit: int | None = None
    ) -> list[ProviderHealthTimeSeriesSnapshot]:
        return list(
            self.session.execute(
                select(ProviderHealthTimeSeriesSnapshot)
                .where(
                    ProviderHealthTimeSeriesSnapshot.is_degraded.is_(True),
                    ProviderHealthTimeSeriesSnapshot.observed_at >= since,
                )
                .order_by(
                    ProviderHealthTimeSeriesSnapshot.observed_at.desc(),
                    ProviderHealthTimeSeriesSnapshot.id.desc(),
                )
                .limit(_bounded_limit(limit))
            ).scalars()
        )

    def degraded_sources(
        self, since: datetime, limit: int | None = None
    ) -> list[SourceHealthTimeSeriesSnapshot]:
        return list(
            self.session.execute(
                select(SourceHealthTimeSeriesSnapshot)
                .where(
                    SourceHealthTimeSeriesSnapshot.is_degraded.is_(True),
                    SourceHealthTimeSeriesSnapshot.observed_at >= since,
                )
                .order_by(
                    SourceHealthTimeSeriesSnapshot.observed_at.desc(),
                    SourceHealthTimeSeriesSnapshot.id.desc(),
                )
                .limit(_bounded_limit(limit))
            ).scalars()
        )

    def health_summary(self, from_ts: datetime, to_ts: datetime) -> dict[str, int]:
        provider_total = (
            self.session.scalar(
                select(func.count())
                .select_from(ProviderHealthTimeSeriesSnapshot)
                .where(
                    ProviderHealthTimeSeriesSnapshot.observed_at >= from_ts,
                    ProviderHealthTimeSeriesSnapshot.observed_at <= to_ts,
                )
            )
            or 0
        )
        source_total = (
            self.session.scalar(
                select(func.count())
                .select_from(SourceHealthTimeSeriesSnapshot)
                .where(
                    SourceHealthTimeSeriesSnapshot.observed_at >= from_ts,
                    SourceHealthTimeSeriesSnapshot.observed_at <= to_ts,
                )
            )
            or 0
        )
        degraded_provider_total = (
            self.session.scalar(
                select(func.count())
                .select_from(ProviderHealthTimeSeriesSnapshot)
                .where(
                    ProviderHealthTimeSeriesSnapshot.observed_at >= from_ts,
                    ProviderHealthTimeSeriesSnapshot.observed_at <= to_ts,
                    ProviderHealthTimeSeriesSnapshot.is_degraded.is_(True),
                )
            )
            or 0
        )
        degraded_source_total = (
            self.session.scalar(
                select(func.count())
                .select_from(SourceHealthTimeSeriesSnapshot)
                .where(
                    SourceHealthTimeSeriesSnapshot.observed_at >= from_ts,
                    SourceHealthTimeSeriesSnapshot.observed_at <= to_ts,
                    SourceHealthTimeSeriesSnapshot.is_degraded.is_(True),
                )
            )
            or 0
        )
        return {
            "provider_snapshot_count": int(provider_total),
            "source_snapshot_count": int(source_total),
            "degraded_provider_count": int(degraded_provider_total),
            "degraded_source_count": int(degraded_source_total),
        }
