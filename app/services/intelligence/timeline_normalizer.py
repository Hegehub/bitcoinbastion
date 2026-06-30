from __future__ import annotations

from datetime import UTC, datetime

from app.domain.intelligence.timeline import (
    TimelineEventType,
    TimelineImportance,
    TimelineVisibility,
    TimelineSourceKind,
)


class TimelineNormalizationService:
    def _base(
        self, event_type: TimelineEventType, title: str, event_time: datetime
    ) -> dict[str, object]:
        et = event_time if event_time.tzinfo else event_time.replace(tzinfo=UTC)
        return {
            "event_type": event_type.value,
            "importance": TimelineImportance.MEDIUM.value,
            "visibility": TimelineVisibility.INTERNAL.value,
            "source_kind": TimelineSourceKind.INTERNAL.value,
            "title": title,
            "summary": "",
            "event_time": et,
            "metadata_json": {},
        }

    def normalize_news_article(self, article: object) -> dict[str, object]:
        return self._base(
            TimelineEventType.NEWS_ARTICLE,
            getattr(article, "title", "news article"),
            getattr(article, "published_at"),
        )

    def normalize_news_event(self, event: object) -> dict[str, object]:
        return self._base(
            TimelineEventType.NEWS_EVENT,
            getattr(event, "canonical_title", "news event"),
            getattr(event, "first_seen_at"),
        )

    def normalize_signal(self, signal: object) -> dict[str, object]:
        return self._base(
            TimelineEventType.MARKET_SIGNAL,
            getattr(signal, "signal_type", "signal"),
            getattr(signal, "created_at"),
        )

    def normalize_btc_candle(self, candle: object) -> dict[str, object]:
        return self._base(
            TimelineEventType.BTC_CANDLE,
            f"BTC {getattr(candle, 'timeframe', '')} candle",
            getattr(candle, "open_time"),
        )

    def normalize_provider_health(self, health: object) -> dict[str, object]:
        return self._base(
            TimelineEventType.PROVIDER_HEALTH_EVENT,
            f"Provider health {getattr(health, 'provider_name', '')}",
            getattr(health, "updated_at"),
        )

    def normalize_operator_action(self, action: str, when: datetime) -> dict[str, object]:
        e = self._base(TimelineEventType.OPERATOR_ACTION, action, when)
        e["visibility"] = TimelineVisibility.OPERATOR_ONLY.value
        e["source_kind"] = TimelineSourceKind.OPERATOR.value
        return e
