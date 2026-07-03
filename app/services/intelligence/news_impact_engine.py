from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, cast

from prometheus_client import Counter, Gauge
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.btc_candle import BTCCandle
from app.db.models.btc_price_point import BTCPricePoint
from app.db.models.impact_confidence_breakdown import ImpactConfidenceBreakdown
from app.db.models.impact_window_snapshot import ImpactWindowSnapshot
from app.db.models.news_article import NewsArticle
from app.db.models.news_event import NewsEvent
from app.db.models.news_price_impact import NewsPriceImpact
from app.db.models.news_score import NewsScore
from app.db.models.time_utils import utcnow

logger = logging.getLogger(__name__)

NEWS_IMPACT_CALCULATIONS_TOTAL = Counter(
    "news_impact_calculations_total", "Total news impact calculations."
)
NEWS_IMPACT_FAILURES_TOTAL = Counter(
    "news_impact_failures_total", "Total failed news impact calculations."
)
NEWS_IMPACT_DEGRADED_TOTAL = Counter(
    "news_impact_degraded_total", "Total degraded news impact calculations."
)
NEWS_IMPACT_AVG_CONFIDENCE = Gauge(
    "news_impact_avg_confidence", "Latest news impact confidence score."
)
NEWS_IMPACT_WINDOW_DISTRIBUTION = Counter(
    "news_impact_window_distribution", "Dominant news impact windows.", ["window"]
)

CORRELATION_LIMITATION = "correlation_not_causation"


@dataclass(frozen=True)
class PriceObservation:
    price: float | None
    provider_confidence: float
    provider_count: int
    volatility_score: float
    source: str
    degraded: bool


@dataclass(frozen=True)
class WindowImpact:
    name: str
    minutes: int
    price_before: float | None
    price_after: float | None
    change_pct: float | None
    absolute_change: float | None
    volatility_score: float
    provider_confidence: float
    direction_match: str
    window_weight: float
    degraded: bool


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


class NewsImpactEngine:
    """Correlation-based BTC price reaction analysis for news articles and events."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.flat_threshold = float(self.settings.market_flat_threshold_pct)
        self.windows = self._parse_windows(str(self.settings.news_impact_windows_minutes))

    def calculate_article_impact(self, db: Session, article_id: int) -> NewsPriceImpact | None:
        NEWS_IMPACT_CALCULATIONS_TOTAL.inc()
        article = db.get(NewsArticle, article_id)
        if article is None:
            return None
        try:
            published_at = article.published_at
            score = self._latest_score(db, article_id=article_id)
            sentiment = self._article_sentiment(article, score)
            source_credibility = self._source_credibility(article, score)
            context: dict[str, Any] = {
                "article_id": article.id,
                "event_id": None,
                "title": article.title,
                "published_at": published_at,
                "sentiment_label": sentiment,
                "btc_relevance_score": clamp(
                    float(
                        article.btc_relevance_score or (score.btc_relevance_score if score else 0.0)
                    )
                ),
                "market_impact_score": clamp(
                    float(
                        article.market_impact_score or (score.market_impact_score if score else 0.0)
                    )
                ),
                "source_credibility_score": source_credibility,
                "source_count": 1,
            }
            return self._calculate(db, context, published_at)
        except Exception:
            NEWS_IMPACT_FAILURES_TOTAL.inc()
            logger.exception("news_impact_article_failed", extra={"article_id": article_id})
            raise

    def calculate_event_impact(self, db: Session, event_id: int) -> NewsPriceImpact | None:
        NEWS_IMPACT_CALCULATIONS_TOTAL.inc()
        event = db.get(NewsEvent, event_id)
        if event is None:
            return None
        try:
            source_credibility = clamp(
                (float(event.cluster_confidence or 0.0) + float(event.provider_confidence or 0.0))
                / 2.0
            )
            source_count_boost = min(0.15, max(0, int(event.source_count or 1) - 1) * 0.03)
            context: dict[str, Any] = {
                "article_id": None,
                "event_id": event.id,
                "title": event.canonical_title,
                "published_at": event.first_seen_at,
                "sentiment_label": event.event_sentiment or "UNKNOWN",
                "btc_relevance_score": clamp(float(event.btc_relevance_score or 0.0)),
                "market_impact_score": clamp(float(event.market_impact_score or 0.0)),
                "source_credibility_score": clamp(source_credibility + source_count_boost),
                "source_count": int(event.source_count or 1),
                "primary_article_id": event.primary_article_id,
            }
            return self._calculate(db, context, event.first_seen_at)
        except Exception:
            NEWS_IMPACT_FAILURES_TOTAL.inc()
            logger.exception("news_impact_event_failed", extra={"event_id": event_id})
            raise

    def calculate_price_window(
        self, db: Session, published_at: datetime, window_minutes: int, sentiment_label: str
    ) -> WindowImpact:
        before = self._lookup_price(db, published_at)
        after = self._lookup_price(db, published_at + timedelta(minutes=window_minutes))
        change_pct = self._change(before.price, after.price)
        absolute_change = (
            abs((after.price or 0.0) - (before.price or 0.0))
            if before.price is not None and after.price is not None
            else None
        )
        volatility = max(before.volatility_score, after.volatility_score)
        provider_confidence = min(before.provider_confidence, after.provider_confidence)
        direction_match = self.calculate_direction_match(
            sentiment_label, self._direction(change_pct), change_pct
        )
        return WindowImpact(
            name=self._window_name(window_minutes),
            minutes=window_minutes,
            price_before=before.price,
            price_after=after.price,
            change_pct=change_pct,
            absolute_change=absolute_change,
            volatility_score=volatility,
            provider_confidence=provider_confidence,
            direction_match=direction_match,
            window_weight=self._freshness_weight(window_minutes),
            degraded=before.degraded or after.degraded,
        )

    def calculate_direction_match(
        self, sentiment_label: str, actual_direction: str, change_pct: float | None
    ) -> str:
        expected = self._expected_direction(sentiment_label)
        if expected == "UNKNOWN" or actual_direction == "UNKNOWN":
            return "unknown"
        if actual_direction == "FLAT":
            return "partial" if expected in {"UP", "DOWN"} and change_pct is not None else "unknown"
        return "true" if expected == actual_direction else "false"

    def calculate_impact_confidence(
        self,
        *,
        btc_relevance_score: float,
        source_credibility_score: float,
        price_strength: float,
        direction_match: str,
        provider_confidence: float,
        freshness_weight: float,
        volatility_adjustment: float,
    ) -> tuple[float, dict[str, float]]:
        sentiment_component = {"true": 1.0, "partial": 0.6, "unknown": 0.45, "false": 0.2}.get(
            direction_match, 0.45
        )
        components = {
            "btc_relevance_component": clamp(btc_relevance_score),
            "source_credibility_component": clamp(source_credibility_score),
            "price_strength_component": clamp(price_strength),
            "sentiment_match_component": sentiment_component,
            "provider_confidence_component": clamp(provider_confidence),
            "freshness_component": clamp(freshness_weight),
            "volatility_component": clamp(volatility_adjustment),
        }
        confidence = 1.0
        for value in components.values():
            confidence *= value
        return clamp(confidence), components

    def build_explanation(
        self, context: dict[str, Any], dominant: WindowImpact, confidence: float, band: str
    ) -> dict[str, object]:
        sentiment = str(context["sentiment_label"]).lower()
        direction = self._direction(dominant.change_pct).lower()
        return {
            "summary": (
                f"{band} confidence correlation analysis: {sentiment} Bitcoin-relevant news coincided "
                f"with {direction} BTC movement in the {dominant.name} window."
            ),
            "title": context.get("title", ""),
            "dominant_window": dominant.name,
            "direction_match": dominant.direction_match,
            "impact_confidence": confidence,
            "price_evidence": {
                "price_at_publish": dominant.price_before,
                "price_after": dominant.price_after,
                "change_pct": dominant.change_pct,
                "provider_confidence": dominant.provider_confidence,
            },
            "safety": "This is correlation-based attribution and not proof of causation or financial advice.",
        }

    def build_limitations(
        self,
        windows: list[WindowImpact],
        provider_confidence: float,
        source_credibility: float,
        volatility_context: float,
    ) -> dict[str, list[str]]:
        limitations = [CORRELATION_LIMITATION]
        if any(w.price_before is None or w.price_after is None for w in windows):
            limitations.append("insufficient_price_data")
        if provider_confidence < float(self.settings.news_impact_min_provider_confidence):
            limitations.append("low_provider_confidence")
        if source_credibility < 0.4:
            limitations.append("low_source_confidence")
        if any(w.degraded for w in windows):
            limitations.append("degraded_price_context")
        if volatility_context >= 0.7:
            limitations.append("high_market_volatility")
        if max((w.minutes for w in windows if w.change_pct is not None), default=0) >= 240:
            limitations.append("delayed_reaction")
        limitations.append("incomplete_market_context")
        return {"limitations": list(dict.fromkeys(limitations))}

    def _calculate(
        self, db: Session, context: dict[str, Any], published_at: datetime
    ) -> NewsPriceImpact:
        windows = [
            self.calculate_price_window(db, published_at, minutes, str(context["sentiment_label"]))
            for minutes in self.windows
        ]
        available = [w for w in windows if w.change_pct is not None]
        dominant = max(
            available, key=lambda w: abs(w.change_pct or 0.0) * w.window_weight, default=windows[0]
        )
        provider_confidence = self._aggregate_provider_confidence(windows)
        volatility_context = max((w.volatility_score for w in windows), default=0.0)
        price_strength = self._price_move_strength(
            dominant.change_pct, volatility_context, dominant.minutes
        )
        volatility_adjustment = self._volatility_adjustment(volatility_context)
        confidence, components = self.calculate_impact_confidence(
            btc_relevance_score=float(context["btc_relevance_score"]),
            source_credibility_score=float(context["source_credibility_score"]),
            price_strength=price_strength,
            direction_match=dominant.direction_match,
            provider_confidence=provider_confidence,
            freshness_weight=dominant.window_weight,
            volatility_adjustment=volatility_adjustment,
        )
        band = self._confidence_band(confidence)
        limitations = self.build_limitations(
            windows,
            provider_confidence,
            float(context["source_credibility_score"]),
            volatility_context,
        )
        if len(limitations["limitations"]) > 2:
            NEWS_IMPACT_DEGRADED_TOTAL.inc()
        explanation = self.build_explanation(context, dominant, confidence, band)
        impact = self._upsert_impact(db, context)
        self._apply_impact_fields(
            impact,
            context,
            windows,
            dominant,
            confidence,
            band,
            provider_confidence,
            volatility_context,
            explanation,
            limitations,
        )
        db.add(impact)
        db.flush()
        db.execute(delete(ImpactWindowSnapshot).where(ImpactWindowSnapshot.impact_id == impact.id))
        db.execute(
            delete(ImpactConfidenceBreakdown).where(
                ImpactConfidenceBreakdown.impact_id == impact.id
            )
        )
        for window in windows:
            db.add(self._window_row(impact.id, window))
        db.add(self._confidence_row(impact.id, components, confidence, explanation))
        NEWS_IMPACT_AVG_CONFIDENCE.set(confidence)
        NEWS_IMPACT_WINDOW_DISTRIBUTION.labels(window=dominant.name).inc()
        logger.info(
            "news_impact_calculated",
            extra={
                "article_id": context.get("article_id"),
                "event_id": context.get("event_id"),
                "provider_confidence": provider_confidence,
                "dominant_window": dominant.name,
                "confidence": confidence,
                "degraded_state": len(limitations["limitations"]) > 2,
            },
        )
        return impact

    def _apply_impact_fields(
        self,
        impact: NewsPriceImpact,
        context: dict[str, Any],
        windows: list[WindowImpact],
        dominant: WindowImpact,
        confidence: float,
        band: str,
        provider_confidence: float,
        volatility_context: float,
        explanation: dict[str, object],
        limitations: dict[str, list[str]],
    ) -> None:
        by_name = {w.name: w for w in windows}
        impact.article_id = context.get("article_id")
        impact.event_id = context.get("event_id")
        impact.price_at_publish = dominant.price_before
        for name, suffix in [("15m", "15m"), ("1h", "1h"), ("4h", "4h"), ("24h", "24h")]:
            window = by_name.get(name)
            if window is not None:
                setattr(impact, f"price_after_{suffix}", window.price_after)
                setattr(impact, f"change_{suffix}_pct", window.change_pct)
                setattr(impact, f"absolute_change_{suffix}", window.absolute_change)
        impact.sentiment_label = str(context["sentiment_label"]).upper()
        impact.expected_direction = self._expected_direction(str(context["sentiment_label"]))
        impact.actual_direction = self._direction(dominant.change_pct)
        impact.direction_match = dominant.direction_match
        impact.btc_relevance_score = float(context["btc_relevance_score"])
        impact.market_impact_score = float(context["market_impact_score"])
        impact.source_credibility_score = float(context["source_credibility_score"])
        impact.provider_confidence = provider_confidence
        impact.impact_confidence_score = confidence
        impact.dominant_window = dominant.name
        impact.volatility_context = volatility_context
        impact.liquidity_context = "provider_degraded" if provider_confidence < 0.5 else "normal"
        impact.impact_band = band
        impact.explanation_json = explanation
        impact.limitations_json = cast(dict[str, object], limitations)
        impact.metadata_json = {
            "engine_version": "news-impact-v1",
            "windows": self.windows,
            "source_count": context.get("source_count", 1),
        }
        impact.calculated_at = utcnow()
        impact.updated_at = utcnow()
        impact.confidence_score = confidence
        impact.confidence_band = band
        impact.confidence_contributions_json = [
            {"factor": key, "value": value}
            for key, value in self._confidence_values(impact).items()
        ]
        impact.degradation_factors_json = limitations["limitations"]
        impact.uncertainty_flags_json = [
            item for item in limitations["limitations"] if item != CORRELATION_LIMITATION
        ]
        impact.freshness_weight = dominant.window_weight
        impact.volatility_context_weight = self._volatility_adjustment(volatility_context)
        impact.event_confirmation_weight = min(
            1.0, 0.5 + max(0, int(context.get("source_count", 1)) - 1) * 0.1
        )
        impact.explanation_summary = str(explanation["summary"])
        impact.limitation = CORRELATION_LIMITATION

    def _upsert_impact(self, db: Session, context: dict[str, Any]) -> NewsPriceImpact:
        article_id = context.get("article_id")
        event_id = context.get("event_id")
        query = db.query(NewsPriceImpact)
        if article_id is not None:
            existing = query.filter(NewsPriceImpact.article_id == article_id).first()
        else:
            existing = query.filter(NewsPriceImpact.event_id == event_id).first()
        return existing if existing is not None else NewsPriceImpact()

    def _window_row(self, impact_id: int, window: WindowImpact) -> ImpactWindowSnapshot:
        return ImpactWindowSnapshot(
            impact_id=impact_id,
            window_name=window.name,
            window_minutes=window.minutes,
            price_before=window.price_before,
            price_after=window.price_after,
            change_pct=window.change_pct,
            absolute_change=window.absolute_change,
            volatility_score=window.volatility_score,
            provider_confidence=window.provider_confidence,
            direction_match=window.direction_match,
            window_weight=window.window_weight,
            degraded=window.degraded,
        )

    def _confidence_row(
        self,
        impact_id: int,
        components: dict[str, float],
        confidence: float,
        explanation: dict[str, object],
    ) -> ImpactConfidenceBreakdown:
        return ImpactConfidenceBreakdown(
            impact_id=impact_id,
            btc_relevance_component=components["btc_relevance_component"],
            source_credibility_component=components["source_credibility_component"],
            price_strength_component=components["price_strength_component"],
            sentiment_match_component=components["sentiment_match_component"],
            provider_confidence_component=components["provider_confidence_component"],
            freshness_component=components["freshness_component"],
            volatility_component=components["volatility_component"],
            final_confidence=confidence,
            explanation_json=explanation,
        )

    def _lookup_price(self, db: Session, timestamp: datetime) -> PriceObservation:
        candle = db.execute(
            select(BTCCandle)
            .where(BTCCandle.open_time <= timestamp, BTCCandle.close_time >= timestamp)
            .order_by(BTCCandle.provider_confidence.desc(), BTCCandle.id.desc())
            .limit(1)
        ).scalar_one_or_none()
        if candle is None:
            tolerance = timedelta(
                minutes=int(self.settings.news_impact_nearest_price_tolerance_minutes)
            )
            nearby_candles = list(
                db.execute(
                    select(BTCCandle)
                    .where(
                        BTCCandle.open_time >= timestamp - tolerance,
                        BTCCandle.open_time <= timestamp + tolerance,
                    )
                    .limit(20)
                ).scalars()
            )
            if nearby_candles:
                candle = min(
                    nearby_candles, key=lambda c: abs((c.open_time - timestamp).total_seconds())
                )
        if candle is not None and candle.close is not None:
            degraded = bool(candle.is_degraded or candle.provider_count <= 1)
            return PriceObservation(
                price=float(candle.close),
                provider_confidence=clamp(float(candle.provider_confidence or 0.0)),
                provider_count=int(candle.provider_count or 0),
                volatility_score=clamp(float(candle.volatility_score or 0.0)),
                source="btc_candles",
                degraded=degraded,
            )
        point = self._nearest_price_point(db, timestamp)
        if point is not None:
            return PriceObservation(
                price=float(point.price_usd),
                provider_confidence=clamp(float(point.provider_confidence or 0.0)),
                provider_count=1,
                volatility_score=0.0,
                source="btc_price_points",
                degraded=True,
            )
        return PriceObservation(
            price=None,
            provider_confidence=0.0,
            provider_count=0,
            volatility_score=0.0,
            source="missing",
            degraded=True,
        )

    def _nearest_price_point(self, db: Session, timestamp: datetime) -> BTCPricePoint | None:
        tolerance = timedelta(
            minutes=int(self.settings.news_impact_nearest_price_tolerance_minutes)
        )
        points = list(
            db.execute(
                select(BTCPricePoint)
                .where(
                    BTCPricePoint.observed_at >= timestamp - tolerance,
                    BTCPricePoint.observed_at <= timestamp + tolerance,
                )
                .limit(50)
            ).scalars()
        )
        if not points:
            return None
        median_points = [point for point in points if point.is_median_selected]
        candidates = median_points or points
        return min(candidates, key=lambda p: abs((p.observed_at - timestamp).total_seconds()))

    def _latest_score(self, db: Session, article_id: int) -> NewsScore | None:
        return (
            db.query(NewsScore)
            .filter(NewsScore.article_id == article_id)
            .order_by(NewsScore.id.desc())
            .first()
        )

    def _article_sentiment(self, article: NewsArticle, score: NewsScore | None) -> str:
        if article.sentiment_label and article.sentiment_label.upper() != "UNKNOWN":
            return article.sentiment_label
        if score and isinstance(score.explanation_json, dict):
            label = score.explanation_json.get("sentiment_label")
            if isinstance(label, str):
                return label
        return "UNKNOWN"

    def _source_credibility(self, article: NewsArticle, score: NewsScore | None) -> float:
        if score is not None and score.source_credibility_score > 0:
            return clamp(float(score.source_credibility_score))
        return clamp(float(article.credibility_score or article.provider_confidence or 0.5))

    def _change(self, price_before: float | None, price_after: float | None) -> float | None:
        if price_before is None or price_after is None or price_before <= 0:
            return None
        return ((price_after - price_before) / price_before) * 100.0

    def _direction(self, change_pct: float | None) -> str:
        if change_pct is None:
            return "UNKNOWN"
        if abs(change_pct) < self.flat_threshold:
            return "FLAT"
        return "UP" if change_pct > 0 else "DOWN"

    def _expected_direction(self, sentiment_label: str) -> str:
        sentiment = sentiment_label.upper()
        if sentiment == "POSITIVE":
            return "UP"
        if sentiment == "NEGATIVE":
            return "DOWN"
        return "UNKNOWN"

    def _price_move_strength(
        self, change_pct: float | None, volatility_context: float, minutes: int
    ) -> float:
        if change_pct is None:
            return 0.0
        timeframe_factor = 1.0 if minutes <= 60 else 0.85 if minutes <= 240 else 0.65
        denominator = max(0.25, 0.75 + volatility_context * 2.0)
        return clamp(abs(change_pct) / denominator * timeframe_factor)

    def _volatility_adjustment(self, volatility_context: float) -> float:
        if volatility_context >= 0.8:
            return 0.6
        if volatility_context >= 0.5:
            return 0.75
        return 1.0

    def _freshness_weight(self, minutes: int) -> float:
        if minutes <= 15:
            return 1.0
        if minutes <= 60:
            return 0.85
        if minutes <= 240:
            return 0.65
        return 0.4

    def _aggregate_provider_confidence(self, windows: list[WindowImpact]) -> float:
        values = [w.provider_confidence for w in windows if w.provider_confidence > 0]
        if not values:
            return 0.0
        return clamp(sum(values) / len(values))

    def _window_name(self, minutes: int) -> str:
        return {15: "15m", 60: "1h", 240: "4h", 1440: "24h"}.get(minutes, f"{minutes}m")

    def _parse_windows(self, raw: str) -> list[int]:
        values: list[int] = []
        for part in raw.split(","):
            try:
                minutes = int(part.strip())
            except ValueError:
                continue
            if minutes > 0:
                values.append(minutes)
        return values or [15, 60, 240, 1440]

    def _confidence_band(self, confidence: float) -> str:
        if confidence < 0.25:
            return "VERY_LOW"
        if confidence < 0.45:
            return "LOW"
        if confidence < 0.65:
            return "MEDIUM"
        if confidence < 0.85:
            return "HIGH"
        return "VERY_HIGH"

    def _confidence_values(self, impact: NewsPriceImpact) -> dict[str, float]:
        return {
            "btc_relevance_score": impact.btc_relevance_score,
            "source_credibility_score": impact.source_credibility_score,
            "provider_confidence": impact.provider_confidence,
            "impact_confidence_score": impact.impact_confidence_score,
        }
