from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models.btc_candle import BTCCandle
from app.db.models.candle_attribution import CandleAttribution
from app.db.models.news_event import NewsEvent
from app.db.models.historical_similarity_result import HistoricalSimilarityResult
from app.services.intelligence.candle_attribution.metrics import (
    ATTRIBUTION_CANDIDATES_TOTAL,
    ATTRIBUTION_CONFIDENCE_DISTRIBUTION,
    ATTRIBUTION_GENERATED_TOTAL,
    ATTRIBUTION_PROCESSING_SECONDS,
)

CORRELATION_LIMITATION = "Correlation-based attribution. Not proof of causation."
NO_CAUSATION_LIMITATION = "Correlation is not proof of causation."
WINDOWS_BEFORE_SECONDS = (15 * 60, 30 * 60, 60 * 60, 4 * 60 * 60)
WINDOW_AFTER_SECONDS = 15 * 60
DEFAULT_WEIGHTS: dict[str, float] = {
    "time_proximity": 0.17,
    "btc_relevance": 0.15,
    "market_impact": 0.14,
    "source_credibility": 0.11,
    "event_confidence": 0.11,
    "direction_match": 0.12,
    "historical_pattern_support": 0.08,
    "provider_confidence": 0.08,
    "source_health_confidence": 0.04,
}


@dataclass(frozen=True)
class AttributionScore:
    event: NewsEvent
    rank: int
    score: float
    confidence_band: str
    direction_match: str
    time_distance_seconds: int
    event_before_candle_seconds: int
    event_inside_candle: bool
    event_after_candle_seconds: int
    factor_scores: dict[str, float]
    factor_contributions: dict[str, float]
    explanation: dict[str, Any]
    limitations: list[str]


class CandleAttributionRankingEngine:
    """Evidence-based correlation ranking for NewsEvent -> BTC candle attribution."""

    def __init__(self, db: Session, weights: dict[str, float] | None = None) -> None:
        self.db = db
        self.weights = weights or DEFAULT_WEIGHTS

    def rank_candidate_events(self, candle: BTCCandle, limit: int = 5) -> list[AttributionScore]:
        started = time.perf_counter()
        try:
            events = self.discover_candidate_events(candle)
            ATTRIBUTION_CANDIDATES_TOTAL.inc(len(events))
            scored = [self.score_candidate(candle, event) for event in events]
            ranked: list[AttributionScore] = []
            for item in sorted(scored, key=lambda row: (-row.score, row.time_distance_seconds, row.event.id))[:limit]:
                ranked.append(
                    AttributionScore(
                        event=item.event,
                        rank=len(ranked) + 1,
                        score=item.score,
                        confidence_band=item.confidence_band,
                        direction_match=item.direction_match,
                        time_distance_seconds=item.time_distance_seconds,
                        event_before_candle_seconds=item.event_before_candle_seconds,
                        event_inside_candle=item.event_inside_candle,
                        event_after_candle_seconds=item.event_after_candle_seconds,
                        factor_scores=item.factor_scores,
                        factor_contributions=item.factor_contributions,
                        explanation={**item.explanation, "rank": len(ranked) + 1},
                        limitations=item.limitations,
                    )
                )
            return ranked
        finally:
            ATTRIBUTION_PROCESSING_SECONDS.observe(time.perf_counter() - started)

    def attribute_candle(self, candle_id: int, limit: int = 5) -> dict[str, Any]:
        candle = self.db.get(BTCCandle, candle_id)
        if candle is None:
            return {
                "candle": None,
                "candidate_events": [],
                "ranking": [],
                "confidence": 0.0,
                "summary": "Candle not found.",
                "limitations": [CORRELATION_LIMITATION],
            }
        ranked = self.rank_candidate_events(candle, limit=limit)
        rows = self.persist_rankings(candle, ranked)
        return self.response_payload(candle, rows)

    def discover_candidate_events(self, candle: BTCCandle) -> list[NewsEvent]:
        start = candle.open_time - timedelta(seconds=max(WINDOWS_BEFORE_SECONDS))
        end = candle.close_time + timedelta(seconds=WINDOW_AFTER_SECONDS)
        stmt = (
            select(NewsEvent)
            .where(NewsEvent.first_seen_at >= start)
            .where(NewsEvent.first_seen_at <= end)
            .order_by(NewsEvent.first_seen_at.asc(), NewsEvent.id.asc())
        )
        return list(self.db.execute(stmt).scalars())

    def score_candidate(self, candle: BTCCandle, event: NewsEvent) -> AttributionScore:
        distance = self._distance(candle, event.first_seen_at)
        direction = self.direction_match(candle, event)
        factor_scores = {
            "time_proximity": self._time_weight(distance["time_distance_seconds"]),
            "btc_relevance": self._clamp(event.btc_relevance_score),
            "market_impact": self._clamp(event.market_impact_score),
            "source_credibility": self._source_credibility(event),
            "event_confidence": self._clamp(event.event_confidence),
            "direction_match": self._direction_weight(direction),
            "historical_pattern_support": self._historical_support(event),
            "provider_confidence": self._provider_confidence(candle, event),
            "source_health_confidence": self._source_health_confidence(event),
        }
        base = (
            factor_scores["time_proximity"]
            * factor_scores["btc_relevance"]
            * factor_scores["market_impact"]
            * factor_scores["direction_match"]
            * factor_scores["provider_confidence"]
        )
        adjusted = base
        adjusted *= 0.85 + (0.30 * factor_scores["historical_pattern_support"])
        adjusted *= 0.80 + (0.25 * factor_scores["source_health_confidence"])
        adjusted *= 0.80 + (0.25 * factor_scores["event_confidence"])
        weighted = sum(factor_scores[name] * self.weights[name] for name in self.weights)
        final_score = self._clamp((adjusted * 0.55) + (weighted * 0.45))
        contributions = {name: round(factor_scores[name] * self.weights[name], 6) for name in self.weights}
        limitations = self.limitations(candle, event, direction, factor_scores)
        explanation = self.explanation(candle, event, direction, factor_scores, contributions, final_score)
        return AttributionScore(
            event=event,
            rank=0,
            score=final_score,
            confidence_band=self.confidence_band(final_score),
            direction_match=direction,
            time_distance_seconds=distance["time_distance_seconds"],
            event_before_candle_seconds=distance["event_before_candle_seconds"],
            event_inside_candle=bool(distance["event_inside_candle"]),
            event_after_candle_seconds=distance["event_after_candle_seconds"],
            factor_scores=factor_scores,
            factor_contributions=contributions,
            explanation=explanation,
            limitations=limitations,
        )

    def persist_rankings(self, candle: BTCCandle, ranked: list[AttributionScore]) -> list[CandleAttribution]:
        self.db.execute(delete(CandleAttribution).where(CandleAttribution.candle_id == candle.id))
        rows: list[CandleAttribution] = []
        for item in ranked:
            row = CandleAttribution(
                candle_id=candle.id,
                event_id=item.event.id,
                article_id=item.event.primary_article_id,
                timeframe=candle.timeframe,
                candle_open_time=candle.open_time,
                candle_close_time=candle.close_time,
                attribution_type="correlation_candidate",
                candidate_category=item.event.event_type,
                candidate_rank=item.rank,
                rank=item.rank,
                time_distance_seconds=item.time_distance_seconds,
                event_before_candle_seconds=item.event_before_candle_seconds,
                event_inside_candle=item.event_inside_candle,
                event_after_candle_seconds=item.event_after_candle_seconds,
                time_distance_weight=item.factor_scores["time_proximity"],
                price_move_pct=self._price_move_pct(candle),
                candle_direction=self._candle_direction(candle),
                direction_match=item.direction_match in {"strong_match", "weak_match"},
                sentiment_direction_match=item.direction_match,
                btc_relevance_score=item.factor_scores["btc_relevance"],
                market_impact_score=item.factor_scores["market_impact"],
                source_credibility_score=item.factor_scores["source_credibility"],
                provider_confidence=item.factor_scores["provider_confidence"],
                event_confidence=item.factor_scores["event_confidence"],
                impact_confidence=item.factor_scores["market_impact"],
                historical_similarity_score=item.factor_scores["historical_pattern_support"],
                pattern_match_score=item.factor_scores["historical_pattern_support"],
                freshness_weight=item.factor_scores["time_proximity"],
                volatility_weight=max(0.0, 1.0 - float(candle.volatility_score or 0.0)),
                event_score=item.factor_scores["event_confidence"],
                impact_score=item.factor_scores["market_impact"],
                confidence_score=item.score,
                confidence_band=item.confidence_band,
                source_confidence=item.factor_scores["source_health_confidence"],
                is_primary_candidate=item.rank == 1,
                window_used=self._window_label(candle, item.event.first_seen_at),
                dominant_window=self._window_label(candle, item.event.first_seen_at),
                summary_text=item.explanation["summary"],
                explanation_json=item.explanation,
                limitations_json={"limitations": item.limitations},
                evidence_refs_json={
                    "factor_scores": item.factor_scores,
                    "factor_contributions": item.factor_contributions,
                    "candidate_event_id": item.event.id,
                    "candle_id": candle.id,
                    "time_distance_seconds": item.time_distance_seconds,
                    "direction_match": item.direction_match,
                },
            )
            self.db.add(row)
            rows.append(row)
            ATTRIBUTION_CONFIDENCE_DISTRIBUTION.observe(item.score)
        self.db.flush()
        ATTRIBUTION_GENERATED_TOTAL.inc(len(rows))
        return rows

    def response_payload(self, candle: BTCCandle, rows: list[CandleAttribution]) -> dict[str, Any]:
        candidate_events = [self._row_payload(row) for row in rows]
        limitations = self._combined_limitations(rows)
        return {
            "candle": {
                "id": candle.id,
                "timeframe": candle.timeframe,
                "open_time": candle.open_time,
                "close_time": candle.close_time,
                "price_move_pct": round(self._price_move_pct(candle), 6),
                "direction": self._candle_direction(candle),
                "provider_confidence": candle.provider_confidence,
            },
            "candidate_events": candidate_events,
            "ranking": candidate_events,
            "confidence": candidate_events[0]["confidence"] if candidate_events else 0.0,
            "summary": self.generate_candle_summary(rows),
            "limitations": limitations,
        }

    def generate_candle_summary(self, rows: list[CandleAttribution]) -> str:
        if not rows:
            return "No dominant explanatory event was identified with high confidence."
        top = rows[0]
        if len(rows) == 1:
            return f"This candle has one ranked event that may have been one of the contributing factors: {top.summary_text}"
        factors = [row.candidate_category for row in rows[:3]]
        return f"Likely combination of {', '.join(factors)} context; top candidate confidence is {top.confidence_score:.2f}."

    def direction_match(self, candle: BTCCandle, event: NewsEvent) -> str:
        candle_direction = self._candle_direction(candle)
        sentiment = str(event.event_sentiment or "UNKNOWN").upper()
        if sentiment in {"NEUTRAL", "UNKNOWN"} or candle_direction == "flat":
            return "neutral"
        if sentiment == "POSITIVE" and candle_direction == "green":
            return "strong_match"
        if sentiment == "NEGATIVE" and candle_direction == "red":
            return "strong_match"
        if sentiment == "POSITIVE" and candle_direction == "red":
            return "contradictory"
        if sentiment == "NEGATIVE" and candle_direction == "green":
            return "contradictory"
        return "weak_match"

    def confidence_band(self, score: float) -> str:
        if score < 0.45:
            return "LOW"
        if score < 0.70:
            return "MEDIUM"
        return "HIGH"

    def explanation(
        self,
        candle: BTCCandle,
        event: NewsEvent,
        direction: str,
        factors: dict[str, float],
        contributions: dict[str, float],
        score: float,
    ) -> dict[str, Any]:
        minutes = round(self._distance(candle, event.first_seen_at)["time_distance_seconds"] / 60.0, 2)
        return {
            "summary": (
                f"This {event.event_type} event occurred {minutes} minutes from the candle window, "
                f"has Bitcoin relevance {factors['btc_relevance']:.2f}, and direction assessment is {direction}. "
                "It may have been one of the contributing factors, but this is correlation-based attribution only."
            ),
            "factor_scores": factors,
            "factor_contributions": contributions,
            "attribution_score": score,
            "direction_match": direction,
            "event_title": event.canonical_title,
        }

    def limitations(self, candle: BTCCandle, event: NewsEvent, direction: str, factors: dict[str, float]) -> list[str]:
        limitations = [CORRELATION_LIMITATION, NO_CAUSATION_LIMITATION]
        if factors["source_credibility"] < 0.5 or factors["source_health_confidence"] < 0.5:
            limitations.append("low source confidence")
        if factors["provider_confidence"] < 0.55 or candle.is_degraded:
            limitations.append("provider degradation")
        if factors["historical_pattern_support"] < 0.25:
            limitations.append("weak historical support")
        if factors["btc_relevance"] < 0.5 or factors["market_impact"] < 0.5:
            limitations.append("insufficient evidence")
        if direction == "contradictory":
            limitations.append("event sentiment contradicted the candle direction")
        return limitations

    def _row_payload(self, row: CandleAttribution) -> dict[str, Any]:
        return {
            "event_id": row.event_id,
            "article_id": row.article_id,
            "rank": row.rank,
            "confidence": row.confidence_score,
            "confidence_band": row.confidence_band,
            "direction_match": row.sentiment_direction_match,
            "time_distance_seconds": row.time_distance_seconds,
            "summary": row.summary_text,
            "explanation": row.explanation_json,
            "limitations": self._row_limitations(row),
        }

    def _combined_limitations(self, rows: list[CandleAttribution]) -> list[str]:
        output: list[str] = []
        for row in rows:
            for value in self._row_limitations(row):
                if value not in output:
                    output.append(str(value))
        return output or [CORRELATION_LIMITATION, NO_CAUSATION_LIMITATION]

    def _row_limitations(self, row: CandleAttribution) -> list[str]:
        if not isinstance(row.limitations_json, dict):
            return []
        values = row.limitations_json.get("limitations", [])
        if not isinstance(values, list):
            return []
        return [str(value) for value in values]

    def _distance(self, candle: BTCCandle, event_time: datetime) -> dict[str, int | bool]:
        if candle.open_time <= event_time <= candle.close_time:
            return {
                "time_distance_seconds": 0,
                "event_before_candle_seconds": 0,
                "event_inside_candle": True,
                "event_after_candle_seconds": 0,
            }
        if event_time < candle.open_time:
            seconds = int((candle.open_time - event_time).total_seconds())
            return {
                "time_distance_seconds": seconds,
                "event_before_candle_seconds": seconds,
                "event_inside_candle": False,
                "event_after_candle_seconds": 0,
            }
        seconds = int((event_time - candle.close_time).total_seconds())
        return {
            "time_distance_seconds": seconds,
            "event_before_candle_seconds": 0,
            "event_inside_candle": False,
            "event_after_candle_seconds": seconds,
        }

    def _time_weight(self, distance_seconds: int) -> float:
        if distance_seconds == 0:
            return 1.0
        return self._clamp(1.0 / (1.0 + (distance_seconds / (60 * 60))))

    def _source_credibility(self, event: NewsEvent) -> float:
        count_score = min(float(event.source_count or 0) / 3.0, 1.0)
        return self._clamp((count_score * 0.6) + (float(event.provider_confidence or 0.0) * 0.4))

    def _source_health_confidence(self, event: NewsEvent) -> float:
        return self._clamp((min(float(event.article_count or 0) / 3.0, 1.0) * 0.5) + (float(event.cluster_confidence or 0.0) * 0.5))

    def _provider_confidence(self, candle: BTCCandle, event: NewsEvent) -> float:
        return self._clamp(min(float(candle.provider_confidence or 0.0), float(event.provider_confidence or 0.0) or 1.0))

    def _historical_support(self, event: NewsEvent) -> float:
        rows = (
            self.db.query(HistoricalSimilarityResult)
            .filter(
                (HistoricalSimilarityResult.reference_event_id == event.id)
                | (HistoricalSimilarityResult.candidate_event_id == event.id)
                | (HistoricalSimilarityResult.matched_event_id == event.id)
            )
            .order_by(HistoricalSimilarityResult.similarity_score.desc())
            .limit(3)
            .all()
        )
        if not rows:
            return 0.35 if event.is_high_impact else 0.15
        return self._clamp(sum(float(row.similarity_score or 0.0) for row in rows) / len(rows))

    def _direction_weight(self, direction: str) -> float:
        return {
            "strong_match": 1.0,
            "weak_match": 0.72,
            "neutral": 0.55,
            "contradictory": 0.28,
        }[direction]

    def _candle_direction(self, candle: BTCCandle) -> str:
        move = self._price_move_pct(candle)
        if move > 0.05:
            return "green"
        if move < -0.05:
            return "red"
        return "flat"

    def _price_move_pct(self, candle: BTCCandle) -> float:
        if not candle.open or not candle.close or candle.open <= 0:
            return 0.0
        return ((float(candle.close) - float(candle.open)) / float(candle.open)) * 100.0

    def _window_label(self, candle: BTCCandle, event_time: datetime) -> str:
        if candle.open_time <= event_time <= candle.close_time:
            return "inside_candle"
        if event_time > candle.close_time:
            return "after_15m"
        distance = int((candle.open_time - event_time).total_seconds())
        for seconds in WINDOWS_BEFORE_SECONDS:
            if distance <= seconds:
                return f"before_{seconds // 60}m"
        return "before_4h"

    def _clamp(self, value: float | None) -> float:
        return max(0.0, min(float(value or 0.0), 1.0))
