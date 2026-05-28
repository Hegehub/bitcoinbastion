from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.attribution_context_snapshot import AttributionContextSnapshot
from app.db.models.attribution_replay_log import AttributionReplayLog
from app.db.models.btc_candle import BTCCandle
from app.db.models.candle_attribution import CandleAttribution
from app.db.models.candle_attribution_candidate import CandleAttributionCandidate
from app.db.models.news_event import NewsEvent
from app.db.models.news_price_impact import NewsPriceImpact
from app.db.models.time_utils import utcnow
from app.services.intelligence.candle_attribution.metrics import (
    ATTRIBUTION_CANDIDATES_TOTAL,
    ATTRIBUTION_CONFIDENCE_AVG,
    ATTRIBUTION_RUNTIME_MS,
    CANDLES_PROCESSED_TOTAL,
    LOW_CONFIDENCE_ATTRIBUTIONS_TOTAL,
    PROVIDER_DISAGREEMENT_TOTAL,
)

logger = logging.getLogger(__name__)

CORRELATION_LIMITATION = "Correlation is not proof of causation."
ENGINE_VERSION = "production-candle-attribution-v2"
SUPPORTED_EVENT_TYPES = {
    "institutional_etf",
    "macro_liquidity",
    "regulatory",
    "security_shock",
    "exchange_event",
    "mining_event",
    "lightning_event",
    "bitcoin_core",
    "liquidation",
    "market_structure",
    "onchain_activity",
    "treasury_adoption",
    "custody_event",
    "sovereignty_event",
}
PATTERN_LIBRARY = {
    "institutional_etf": "ETF inflow shock",
    "regulatory": "SEC shock",
    "macro_liquidity": "Fed liquidity",
    "security_shock": "exchange exploit",
    "liquidation": "liquidation cascade",
    "mining_event": "miner capitulation",
    "treasury_adoption": "treasury adoption",
    "sovereignty_event": "sovereignty event",
}


@dataclass(frozen=True)
class CandidateScore:
    event: NewsEvent
    rank: int
    raw_score: float
    normalized_score: float
    confidence_score: float
    confidence_band: str
    time_distance_seconds: int
    event_before_candle_seconds: int
    event_inside_candle: bool
    event_after_candle_seconds: int
    freshness_weight: float
    direction_match: bool
    sentiment_direction_match: str
    candle_direction: str
    historical_similarity_score: float
    pattern_match_score: float
    volatility_weight: float
    impact_confidence: float
    attribution_type: str
    category: str
    ranking_features: dict[str, Any]
    limitations: list[str]


class CandleAttributionEngine:
    """Production candle attribution engine.

    The engine ranks nearby market/news events as possible contributors to a
    BTC candle. It persists evidence and uncertainty metadata, but it never
    claims proof of causation.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.window_config = self._load_json_setting(
            self.settings.attribution_window_config_json,
            {
                "15m": {"before": 45, "after": 15},
                "1h": {"before": 240, "after": 60},
                "4h": {"before": 720, "after": 240},
                "1d": {"before": 2880, "after": 720},
            },
        )
        self.weights = self._load_json_setting(
            self.settings.attribution_ranking_weights_json,
            {
                "btc_relevance_score": 0.18,
                "market_impact_score": 0.16,
                "source_credibility_score": 0.12,
                "impact_confidence": 0.12,
                "historical_similarity_score": 0.08,
                "pattern_match_score": 0.08,
                "provider_confidence": 0.10,
                "time_distance": 0.08,
                "direction_match": 0.05,
                "volatility_weight": 0.03,
            },
        )

    def attribute_candle(self, candle_id: int) -> list[CandleAttribution]:
        candle = self.db.get(BTCCandle, candle_id)
        if candle is None:
            return []
        return self.attribute_candle_object(candle)

    def attribute_candle_object(self, candle: BTCCandle) -> list[CandleAttribution]:
        start = time.perf_counter()
        try:
            candidates = self.find_candidate_events(candle)
            scored = self.rank_candidates(candle, candidates)
            rows = self.persist_attributions(candle, scored)
            self.generate_replay_log(candle, scored, rows)
            CANDLES_PROCESSED_TOTAL.inc()
            if scored:
                average_confidence = sum(item.confidence_score for item in scored[: self.settings.attribution_top_candidates]) / min(
                    len(scored), self.settings.attribution_top_candidates
                )
                ATTRIBUTION_CONFIDENCE_AVG.set(average_confidence)
            logger.info(
                "candle_attribution_completed",
                extra={
                    "candle_id": candle.id,
                    "candidate_count": len(candidates),
                    "attribution_count": len(rows),
                    "provider_confidence": candle.provider_confidence,
                },
            )
            return rows
        finally:
            ATTRIBUTION_RUNTIME_MS.observe((time.perf_counter() - start) * 1000.0)

    def find_candidate_events(self, candle: BTCCandle) -> list[NewsEvent]:
        window = self._window_for_timeframe(candle.timeframe)
        start = candle.open_time - timedelta(minutes=int(window["before"]))
        end = candle.close_time + timedelta(minutes=int(window["after"]))
        stmt = (
            select(NewsEvent)
            .where(NewsEvent.first_seen_at <= end)
            .where(NewsEvent.last_seen_at >= start)
            .order_by(NewsEvent.first_seen_at.asc(), NewsEvent.id.asc())
        )
        events = list(self.db.execute(stmt).scalars())
        ATTRIBUTION_CANDIDATES_TOTAL.inc(len(events))
        return events

    def rank_candidates(self, candle: BTCCandle, events: list[NewsEvent]) -> list[CandidateScore]:
        raw_scores = [self.score_candidate(candle, event, 0) for event in events]
        max_raw = max((item.raw_score for item in raw_scores), default=1.0) or 1.0
        ranked: list[CandidateScore] = []
        for item in sorted(raw_scores, key=lambda row: (-row.raw_score, row.event.first_seen_at, row.event.id)):
            normalized = self._clamp(item.raw_score / max_raw)
            confidence = self._clamp(min(item.raw_score, self.settings.attribution_max_confidence))
            ranked.append(
                CandidateScore(
                    event=item.event,
                    rank=len(ranked) + 1,
                    raw_score=item.raw_score,
                    normalized_score=normalized,
                    confidence_score=confidence,
                    confidence_band=self.confidence_band(confidence),
                    time_distance_seconds=item.time_distance_seconds,
                    event_before_candle_seconds=item.event_before_candle_seconds,
                    event_inside_candle=item.event_inside_candle,
                    event_after_candle_seconds=item.event_after_candle_seconds,
                    freshness_weight=item.freshness_weight,
                    direction_match=item.direction_match,
                    sentiment_direction_match=item.sentiment_direction_match,
                    candle_direction=item.candle_direction,
                    historical_similarity_score=item.historical_similarity_score,
                    pattern_match_score=item.pattern_match_score,
                    volatility_weight=item.volatility_weight,
                    impact_confidence=item.impact_confidence,
                    attribution_type=item.attribution_type,
                    category=item.category,
                    ranking_features={**item.ranking_features, "normalized_score": normalized, "rank": len(ranked) + 1},
                    limitations=item.limitations,
                )
            )
        return ranked

    def score_candidate(self, candle: BTCCandle, event: NewsEvent, rank: int = 0) -> CandidateScore:
        distance = self._time_distance(candle, event.first_seen_at)
        event_type = self._event_type(event)
        candle_direction = self._candle_direction(candle)
        sentiment_match = self._sentiment_direction_match(str(event.event_sentiment), candle_direction)
        direction_weight = self._direction_weight(sentiment_match)
        source_credibility = self._source_credibility(event)
        impact_confidence = self._impact_confidence(event)
        historical_similarity = self._historical_similarity(event)
        pattern_match = self._pattern_score(event_type)
        volatility_weight = self._volatility_weight(candle)
        provider_confidence = self._clamp(min(float(candle.provider_confidence or 0.0), float(event.provider_confidence or 0.0) or 1.0))
        freshness_weight = self._time_decay(distance["time_distance_seconds"])
        factors = {
            "btc_relevance_score": self._clamp(event.btc_relevance_score),
            "market_impact_score": self._clamp(event.market_impact_score),
            "source_credibility_score": source_credibility,
            "impact_confidence": impact_confidence,
            "historical_similarity_score": historical_similarity,
            "pattern_match_score": pattern_match,
            "provider_confidence": provider_confidence,
            "time_distance": freshness_weight,
            "direction_match": direction_weight,
            "volatility_weight": volatility_weight,
        }
        raw_score = self._weighted_score(factors)
        limitations = self.build_limitations(candle, event, distance["time_distance_seconds"], sentiment_match, provider_confidence)
        ranking_features = {
            "engine_version": ENGINE_VERSION,
            "event_type": event_type,
            "factors": factors,
            "weights": self.weights,
            "contributions": {name: factors[name] * float(self.weights.get(name, 0.0)) for name in factors},
            "time_windows": self._window_for_timeframe(candle.timeframe),
            "direction_logic": {
                "sentiment": event.event_sentiment,
                "candle_direction": candle_direction,
                "match": sentiment_match,
                "direction_weight": direction_weight,
            },
            "confidence_adjustments": limitations,
        }
        return CandidateScore(
            event=event,
            rank=rank,
            raw_score=raw_score,
            normalized_score=raw_score,
            confidence_score=raw_score,
            confidence_band=self.confidence_band(raw_score),
            time_distance_seconds=distance["time_distance_seconds"],
            event_before_candle_seconds=distance["event_before_candle_seconds"],
            event_inside_candle=bool(distance["event_inside_candle"]),
            event_after_candle_seconds=distance["event_after_candle_seconds"],
            freshness_weight=freshness_weight,
            direction_match=sentiment_match in {"match", "partial"},
            sentiment_direction_match=sentiment_match,
            candle_direction=candle_direction,
            historical_similarity_score=historical_similarity,
            pattern_match_score=pattern_match,
            volatility_weight=volatility_weight,
            impact_confidence=impact_confidence,
            attribution_type=self._attribution_type(event_type),
            category=event_type.upper(),
            ranking_features=ranking_features,
            limitations=limitations,
        )

    def persist_attributions(self, candle: BTCCandle, scored: list[CandidateScore]) -> list[CandleAttribution]:
        self.db.execute(delete(CandleAttribution).where(CandleAttribution.candle_id == candle.id))
        self.db.execute(delete(CandleAttributionCandidate).where(CandleAttributionCandidate.candle_id == candle.id))
        self.db.execute(delete(AttributionContextSnapshot).where(AttributionContextSnapshot.candle_id == candle.id))
        for item in scored:
            self.db.add(
                CandleAttributionCandidate(
                    candle_id=candle.id,
                    candidate_type=item.attribution_type.lower(),
                    event_id=item.event.id,
                    article_id=item.event.primary_article_id,
                    raw_score=item.raw_score,
                    normalized_score=item.normalized_score,
                    ranking_features_json=item.ranking_features,
                    rejection_reason="" if item.rank <= self.settings.attribution_top_candidates else "below_top_candidate_limit",
                )
            )
        top = scored[: self.settings.attribution_top_candidates]
        rows: list[CandleAttribution] = []
        for item in top:
            if item.confidence_score < self.settings.attribution_low_confidence_threshold:
                LOW_CONFIDENCE_ATTRIBUTIONS_TOTAL.inc()
            if "Provider disagreement reduced attribution certainty." in item.limitations:
                PROVIDER_DISAGREEMENT_TOTAL.inc()
            explanation = self.build_explanation(candle, item, len(scored))
            row = CandleAttribution(
                candle_id=candle.id,
                event_id=item.event.id,
                article_id=item.event.primary_article_id,
                timeframe=candle.timeframe,
                candle_open_time=candle.open_time,
                candle_close_time=candle.close_time,
                attribution_type=item.attribution_type,
                candidate_category=item.category,
                candidate_rank=item.rank,
                time_distance_seconds=item.time_distance_seconds,
                event_before_candle_seconds=item.event_before_candle_seconds,
                event_inside_candle=item.event_inside_candle,
                event_after_candle_seconds=item.event_after_candle_seconds,
                time_distance_weight=item.freshness_weight,
                price_move_pct=self._price_move_pct(candle),
                candle_direction=item.candle_direction,
                direction_match=item.direction_match,
                sentiment_direction_match=item.sentiment_direction_match,
                btc_relevance_score=self._clamp(item.event.btc_relevance_score),
                market_impact_score=self._clamp(item.event.market_impact_score),
                source_credibility_score=self._source_credibility(item.event),
                provider_confidence=item.ranking_features["factors"]["provider_confidence"],
                event_confidence=self._clamp(item.event.event_confidence),
                impact_confidence=item.impact_confidence,
                historical_similarity_score=item.historical_similarity_score,
                pattern_match_score=item.pattern_match_score,
                freshness_weight=item.freshness_weight,
                volatility_weight=item.volatility_weight,
                event_score=self._clamp(item.event.event_confidence),
                impact_score=self._clamp(item.event.market_impact_score),
                confidence_score=item.confidence_score,
                confidence_band=item.confidence_band,
                source_confidence=self._source_credibility(item.event),
                rank=item.rank,
                is_primary_candidate=item.rank == 1,
                window_used=str(self._window_for_timeframe(candle.timeframe)),
                dominant_window=self._dominant_window(item.time_distance_seconds),
                summary_text=explanation["summary"],
                explanation_json=explanation,
                limitations_json={"limitations": item.limitations},
                evidence_refs_json=self.generate_replayable_evidence(candle, item),
            )
            self.db.add(row)
            rows.append(row)
        self.db.add(self._context_snapshot(candle, scored))
        self.db.flush()
        return rows

    def explain_candle(self, candle_id: int) -> dict[str, Any]:
        candle = self.db.get(BTCCandle, candle_id)
        if candle is None:
            return {"error": "candle_not_found", "limitations": [CORRELATION_LIMITATION]}
        rows = (
            self.db.query(CandleAttribution)
            .filter(CandleAttribution.candle_id == candle_id)
            .order_by(CandleAttribution.rank.asc())
            .all()
        )
        if not rows:
            rows = self.attribute_candle_object(candle)
        candidate_events = [self._row_payload(row) for row in rows]
        summary = rows[0].summary_text if rows else "No attribution candidates were identified for this candle."
        limitations = rows[0].limitations_json.get("limitations", [CORRELATION_LIMITATION]) if rows else [CORRELATION_LIMITATION]
        return {
            "candle": {
                "id": candle.id,
                "timeframe": candle.timeframe,
                "open_time": candle.open_time,
                "close_time": candle.close_time,
                "price_change_pct": round(self._price_move_pct(candle), 6),
                "direction": self._candle_direction(candle),
                "volatility_context": candle.volatility_score,
                "provider_confidence": candle.provider_confidence,
                "chart_marker": {"has_attribution": bool(rows), "primary_confidence": rows[0].confidence_score if rows else 0.0},
            },
            "ranked_candidate_events": candidate_events,
            "summary": summary,
            "limitations": limitations,
            "similar_historical_cases": [],
            "side_panel": {"primary_candidate": candidate_events[0] if candidate_events else None, "candidate_count": len(candidate_events)},
            "evidence_drawer": {"items": [row.evidence_refs_json for row in rows]},
        }

    def review_attribution(
        self,
        attribution_id: int,
        status: str,
        operator_note: str = "",
        confidence_override: float | None = None,
    ) -> CandleAttribution | None:
        row = self.db.get(CandleAttribution, attribution_id)
        if row is None:
            return None
        normalized_status = status.strip().lower()
        row.is_operator_reviewed = True
        row.operator_review_status = normalized_status
        row.operator_note = operator_note
        row.is_operator_approved = normalized_status == "approved"
        if normalized_status in {"rejected", "false_attribution"}:
            row.is_operator_approved = False
        if confidence_override is not None:
            row.confidence_score = self._clamp(confidence_override)
            row.confidence_band = self.confidence_band(row.confidence_score)
        elif normalized_status == "downgraded":
            row.confidence_score = self._clamp(row.confidence_score * 0.5)
            row.confidence_band = self.confidence_band(row.confidence_score)
        row.updated_at = utcnow()
        self.db.flush()
        return row

    def generate_replay_log(
        self, candle: BTCCandle, scored: list[CandidateScore], rows: list[CandleAttribution]
    ) -> AttributionReplayLog | None:
        if not self.settings.attribution_enable_replay:
            return None
        window = self._window_for_timeframe(candle.timeframe)
        ranking_snapshot = [item.ranking_features for item in scored]
        explanation_snapshot = {
            "summary": rows[0].summary_text if rows else "No candidates found.",
            "limitations": rows[0].limitations_json.get("limitations", [CORRELATION_LIMITATION]) if rows else [CORRELATION_LIMITATION],
        }
        input_hash = hashlib.sha256(json.dumps(ranking_snapshot, sort_keys=True, default=str).encode()).hexdigest()
        replay = AttributionReplayLog(
            candle_id=candle.id,
            engine_version=ENGINE_VERSION,
            input_hash=input_hash,
            candidate_event_count=len(scored),
            timeline_window_before_seconds=int(window["before"]) * 60,
            timeline_window_after_seconds=int(window["after"]) * 60,
            ranking_snapshot_json={"rankings": ranking_snapshot},
            explanation_snapshot_json=explanation_snapshot,
            created_at=utcnow(),
        )
        self.db.add(replay)
        return replay

    def build_explanation(self, candle: BTCCandle, candidate: CandidateScore, candidate_count: int) -> dict[str, Any]:
        title = candidate.event.canonical_title
        direction_phrase = "matched" if candidate.direction_match else "did not fully match"
        minutes = round(candidate.time_distance_seconds / 60.0, 2)
        summary = (
            f"{title} may have contributed to the {candle.timeframe} BTC candle context; "
            f"the event was {minutes} minutes from candle formation and {direction_phrase} candle direction."
        )
        return {
            "summary": summary,
            "candidate_count": candidate_count,
            "top_candidate": {
                "event_id": candidate.event.id,
                "title": title,
                "confidence": candidate.confidence_score,
                "rank": candidate.rank,
            },
            "reasoning": [
                "Candidate was selected from the configured candle attribution window.",
                "Weighted ranking combined BTC relevance, market impact, source credibility, impact confidence, time decay, and direction logic.",
                "The attribution is correlation-oriented and remains subject to operator review.",
            ],
            "limitations": candidate.limitations,
            "ui": {
                "chart_marker_label": candidate.category,
                "modal_title": title,
                "side_panel_section": "possible_contributors",
                "evidence_drawer_enabled": True,
            },
        }

    def build_limitations(
        self,
        candle: BTCCandle,
        event: NewsEvent,
        distance_seconds: int,
        sentiment_match: str,
        provider_confidence: float,
    ) -> list[str]:
        limitations = [CORRELATION_LIMITATION]
        if provider_confidence < 0.5:
            limitations.append("Low provider confidence reduced attribution certainty.")
        if float(candle.provider_disagreement_score or 0.0) > 0.25:
            limitations.append("Provider disagreement reduced attribution certainty.")
        if abs(self._price_move_pct(candle)) < self.settings.market_flat_threshold_pct:
            limitations.append("Weak candle movement reduced attribution confidence.")
        if sentiment_match == "mismatch":
            limitations.append("News sentiment and candle direction were conflicting.")
        if distance_seconds > self._window_for_timeframe(candle.timeframe)["before"] * 60:
            limitations.append("Attribution confidence reduced due to delayed market reaction.")
        if event.source_count <= 1:
            limitations.append("Single-source event confirmation limits confidence.")
        if candle.is_degraded:
            limitations.append("Degraded market data reduced attribution certainty.")
        return limitations

    def generate_replayable_evidence(self, candle: BTCCandle, candidate: CandidateScore) -> dict[str, Any]:
        return {
            "candidate_selection": {
                "event_id": candidate.event.id,
                "event_type": candidate.category,
                "candidate_rank": candidate.rank,
                "window": self._window_for_timeframe(candle.timeframe),
            },
            "score_contributions": candidate.ranking_features.get("contributions", {}),
            "provider_health": {
                "provider_count": candle.provider_count,
                "provider_confidence": candle.provider_confidence,
                "provider_disagreement_score": candle.provider_disagreement_score,
                "is_degraded": candle.is_degraded,
            },
            "time_windows": {
                "time_distance_seconds": candidate.time_distance_seconds,
                "event_before_candle_seconds": candidate.event_before_candle_seconds,
                "event_inside_candle": candidate.event_inside_candle,
                "event_after_candle_seconds": candidate.event_after_candle_seconds,
            },
            "ranking_features": candidate.ranking_features,
            "direction_logic": candidate.ranking_features.get("direction_logic", {}),
            "confidence_adjustments": candidate.ranking_features.get("confidence_adjustments", []),
            "limitations": candidate.limitations,
        }

    def confidence_band(self, value: float) -> str:
        score = self._clamp(value)
        if score < 0.45:
            return "LOW"
        if score < 0.65:
            return "MEDIUM"
        if score < 0.85:
            return "HIGH"
        return "VERY_HIGH"

    def _context_snapshot(self, candle: BTCCandle, scored: list[CandidateScore]) -> AttributionContextSnapshot:
        news_confidence = 0.0
        if scored:
            news_confidence = sum(float(item.event.provider_confidence or 0.0) for item in scored) / len(scored)
        return AttributionContextSnapshot(
            candle_id=candle.id,
            market_volatility=float(candle.volatility_score or 0.0),
            market_regime=candle.market_regime or "unknown",
            provider_health={
                "provider_count": candle.provider_count,
                "provider_confidence": candle.provider_confidence,
                "provider_disagreement_score": candle.provider_disagreement_score,
                "is_degraded": candle.is_degraded,
            },
            active_news_count=len(scored),
            macro_event_count=sum(1 for item in scored if item.event.is_macro_related),
            security_event_count=sum(1 for item in scored if item.event.is_security_related),
            institutional_event_count=sum(1 for item in scored if item.event.is_institutional_related),
            price_provider_confidence=float(candle.provider_confidence or 0.0),
            news_provider_confidence=news_confidence,
            timeline_snapshot_json={"candidates": [self._candidate_payload(item) for item in scored]},
        )

    def _row_payload(self, row: CandleAttribution) -> dict[str, Any]:
        title = ""
        if isinstance(row.explanation_json, dict):
            top_candidate = row.explanation_json.get("top_candidate", {})
            if isinstance(top_candidate, dict):
                title = str(top_candidate.get("title", ""))
        return {
            "id": row.id,
            "rank": row.rank,
            "candidate_rank": row.candidate_rank,
            "event_id": row.event_id,
            "article_id": row.article_id,
            "title": title,
            "category": row.candidate_category,
            "confidence": row.confidence_score,
            "confidence_band": row.confidence_band,
            "time_distance_minutes": round(row.time_distance_seconds / 60.0, 4),
            "direction_match": row.direction_match,
            "sentiment_direction_match": row.sentiment_direction_match,
            "is_primary_candidate": row.is_primary_candidate,
            "operator_review_status": row.operator_review_status,
            "summary": row.summary_text,
            "evidence_refs": row.evidence_refs_json,
        }

    def _candidate_payload(self, item: CandidateScore) -> dict[str, Any]:
        return {
            "rank": item.rank,
            "event_id": item.event.id,
            "title": item.event.canonical_title,
            "category": item.category,
            "confidence": item.confidence_score,
            "confidence_band": item.confidence_band,
            "time_distance_seconds": item.time_distance_seconds,
        }

    def _window_for_timeframe(self, timeframe: str) -> dict[str, int]:
        config = self.window_config.get(timeframe) or self.window_config.get(timeframe.lower())
        if isinstance(config, dict) and "before" in config and "after" in config:
            return {"before": int(config["before"]), "after": int(config["after"])}
        return {
            "before": int(self.settings.attribution_window_before_minutes),
            "after": int(self.settings.attribution_window_after_minutes),
        }

    def _time_distance(self, candle: BTCCandle, event_time: datetime) -> dict[str, Any]:
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

    def _time_decay(self, seconds: int) -> float:
        half_life = max(float(self.settings.attribution_time_decay_half_life_minutes), 1.0)
        minutes = max(seconds / 60.0, 0.0)
        return self._clamp(0.5 ** (minutes / half_life))

    def _weighted_score(self, factors: dict[str, float]) -> float:
        total_weight = sum(float(self.weights.get(name, 0.0)) for name in factors) or 1.0
        weighted = sum(factors[name] * float(self.weights.get(name, 0.0)) for name in factors)
        return self._clamp(weighted / total_weight)

    def _source_credibility(self, event: NewsEvent) -> float:
        return self._clamp(max(float(event.cluster_confidence or 0.0), float(event.event_confidence or 0.0), 0.35))

    def _impact_confidence(self, event: NewsEvent) -> float:
        impact = (
            self.db.query(NewsPriceImpact)
            .filter(NewsPriceImpact.event_id == event.id)
            .order_by(NewsPriceImpact.id.desc())
            .first()
        )
        if impact:
            return self._clamp(impact.impact_confidence_score or impact.confidence_score or 0.0)
        return self._clamp(event.event_confidence or event.market_impact_score or 0.0)

    def _historical_similarity(self, event: NewsEvent) -> float:
        metadata = event.metadata_json if isinstance(event.metadata_json, dict) else {}
        value = metadata.get("historical_similarity_score")
        if isinstance(value, int | float):
            return self._clamp(float(value))
        return 0.5

    def _pattern_score(self, event_type: str) -> float:
        return 0.7 if event_type in PATTERN_LIBRARY else 0.5

    def _volatility_weight(self, candle: BTCCandle) -> float:
        volatility = self._clamp(float(candle.volatility_score or 0.0))
        return self._clamp(max(0.5, 1.0 - (volatility * 0.5)))

    def _event_type(self, event: NewsEvent) -> str:
        raw = (event.event_type or event.event_category or "unknown").lower()
        if raw in SUPPORTED_EVENT_TYPES:
            return raw
        if event.is_institutional_related:
            return "institutional_etf"
        if event.is_macro_related:
            return "macro_liquidity"
        if event.is_regulatory_related:
            return "regulatory"
        if event.is_security_related:
            return "security_shock"
        return "unknown"

    def _attribution_type(self, event_type: str) -> str:
        mapping = {
            "institutional_etf": "INSTITUTIONAL_EVENT",
            "macro_liquidity": "MACRO_EVENT",
            "regulatory": "REGULATORY_EVENT",
            "security_shock": "SECURITY_EVENT",
        }
        return mapping.get(event_type, "NEWS_EVENT")

    def _sentiment_direction_match(self, sentiment: str, candle_direction: str) -> str:
        normalized = sentiment.upper()
        if normalized == "POSITIVE" and candle_direction == "UP":
            return "match"
        if normalized == "NEGATIVE" and candle_direction == "DOWN":
            return "match"
        if normalized in {"NEUTRAL", "MIXED", "UNCERTAIN", "UNKNOWN"}:
            return "partial" if candle_direction in {"UP", "DOWN", "FLAT"} else "unknown"
        if candle_direction == "FLAT":
            return "partial"
        return "mismatch"

    def _direction_weight(self, match: str) -> float:
        weights = {"match": 1.0, "partial": 0.65, "unknown": 0.5, "mismatch": 0.35}
        return weights.get(match, 0.5)

    def _candle_direction(self, candle: BTCCandle) -> str:
        move = self._price_move_pct(candle)
        threshold = float(self.settings.market_flat_threshold_pct)
        if abs(move) < threshold:
            return "FLAT"
        return "UP" if move > 0 else "DOWN"

    def _price_move_pct(self, candle: BTCCandle) -> float:
        if not candle.open or not candle.close or candle.open <= 0:
            return 0.0
        return ((float(candle.close) - float(candle.open)) / float(candle.open)) * 100.0

    def _dominant_window(self, seconds: int) -> str:
        if seconds <= 15 * 60:
            return "15m"
        if seconds <= 60 * 60:
            return "1h"
        if seconds <= 4 * 60 * 60:
            return "4h"
        return "delayed"

    def _load_json_setting(self, value: str, fallback: dict[str, Any]) -> dict[str, Any]:
        try:
            parsed = json.loads(value) if value else fallback
        except json.JSONDecodeError:
            return fallback
        return parsed if isinstance(parsed, dict) else fallback

    def _clamp(self, value: float | int | None) -> float:
        if value is None:
            return 0.0
        return max(0.0, min(1.0, float(value)))
