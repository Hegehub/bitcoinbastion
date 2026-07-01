from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.attribution_replay_log import AttributionReplayLog
from app.db.models.btc_candle import BTCCandle
from app.db.models.candle_attribution import CandleAttribution
from app.db.models.news_event import NewsEvent
from app.db.models.time_utils import utcnow
from app.services.intelligence.candle_attribution.candidate_finder import CandidateEventFinder
from app.services.intelligence.candle_attribution.explanation import CandleExplanationBuilder
from app.services.intelligence.candle_attribution.metrics import (
    CANDLE_ATTRIBUTION_CANDIDATES_TOTAL,
    CANDLE_ATTRIBUTION_CONFIDENCE_AVG,
    CANDLE_ATTRIBUTION_DURATION_SECONDS,
    CANDLE_ATTRIBUTION_FAILURES_TOTAL,
    CANDLE_ATTRIBUTION_RUNS_TOTAL,
)
from app.services.intelligence.candle_attribution.scoring import (
    AttributionScoringService,
    ScoredCandidate,
)

logger = logging.getLogger(__name__)
ENGINE_VERSION = "candle-attribution-v1"


class CandleAttributionEngine:
    """Retrospective, evidence-first candidate attribution for BTC candles."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.finder = CandidateEventFinder()
        self.scorer = AttributionScoringService()
        self.explainer = CandleExplanationBuilder()

    def attribute_candle(self, candle_id: int) -> list[CandleAttribution]:
        candle = self.db.get(BTCCandle, candle_id)
        if candle is None:
            return []
        return self.attribute_candle_object(candle)

    def attribute_candle_object(self, candle: BTCCandle) -> list[CandleAttribution]:
        CANDLE_ATTRIBUTION_RUNS_TOTAL.inc()
        with CANDLE_ATTRIBUTION_DURATION_SECONDS.time():
            try:
                candidates = self.find_candidate_events(candle)
                CANDLE_ATTRIBUTION_CANDIDATES_TOTAL.inc(len(candidates))
                scored = [self.score_candidate(candle, event) for event in candidates]
                ranked = self.rank_candidates(scored)
                rows = self.persist_attributions(candle, ranked)
                if self.settings.attribution_enable_replay:
                    self.generate_replay_log(candle, ranked)
                if rows:
                    avg = sum(row.confidence_score for row in rows) / len(rows)
                    CANDLE_ATTRIBUTION_CONFIDENCE_AVG.set(avg)
                logger.info(
                    "candle_attribution_completed",
                    extra={
                        "candle_id": candle.id,
                        "candidate_count": len(candidates),
                        "persisted_count": len(rows),
                    },
                )
                return rows
            except Exception:
                CANDLE_ATTRIBUTION_FAILURES_TOTAL.inc()
                logger.exception("candle_attribution_failed", extra={"candle_id": candle.id})
                raise

    def find_candidate_events(self, candle: BTCCandle) -> list[NewsEvent]:
        return self.finder.find_candidates(self.db, candle)

    def score_candidate(self, candle: BTCCandle, event: NewsEvent) -> ScoredCandidate:
        return self.scorer.score_candidate(candle, event)

    def rank_candidates(self, scored: list[ScoredCandidate]) -> list[ScoredCandidate]:
        limit = int(self.settings.attribution_top_candidates)
        ordered = sorted(
            scored,
            key=lambda item: (item.confidence_score, item.event.btc_relevance_score, item.event.id),
            reverse=True,
        )
        ranked: list[ScoredCandidate] = []
        for idx, item in enumerate(ordered[:limit], start=1):
            ranked.append(ScoredCandidate(**{**item.__dict__, "rank": idx}))
        return ranked

    def build_explanation(
        self, candle: BTCCandle, candidate: ScoredCandidate, candidate_count: int
    ) -> tuple[str, dict[str, object], dict[str, object]]:
        return self.explainer.build(candle, candidate, candidate_count)

    def persist_attributions(
        self, candle: BTCCandle, ranked: list[ScoredCandidate]
    ) -> list[CandleAttribution]:
        self.db.execute(delete(CandleAttribution).where(CandleAttribution.candle_id == candle.id))
        rows: list[CandleAttribution] = []
        for item in ranked:
            summary, explanation, limitations = self.build_explanation(candle, item, len(ranked))
            row = CandleAttribution(
                candle_id=candle.id,
                event_id=item.event.id,
                article_id=item.article_id,
                timeframe=candle.timeframe,
                candle_open_time=candle.open_time,
                candle_close_time=candle.close_time,
                attribution_type=item.attribution_type,
                candidate_category=item.candidate_category,
                time_distance_seconds=item.time_distance_seconds,
                time_distance_weight=item.time_distance_weight,
                price_move_pct=item.price_move_pct,
                direction_match=item.direction_match,
                event_score=item.event_score,
                impact_score=item.impact_score,
                confidence_score=item.confidence_score,
                provider_confidence=item.provider_confidence,
                source_confidence=item.source_confidence,
                rank=item.rank,
                window_used=item.window_used,
                dominant_window=item.dominant_window,
                summary_text=summary,
                explanation_json=explanation,
                limitations_json=limitations,
            )
            self.db.add(row)
            rows.append(row)
        self.db.flush()
        return rows

    def generate_replay_log(
        self, candle: BTCCandle, ranked: list[ScoredCandidate]
    ) -> AttributionReplayLog:
        ranking_snapshot = [self._ranking_entry(item) for item in ranked]
        if ranked:
            _, explanation_snapshot, _ = self.build_explanation(candle, ranked[0], len(ranked))
        else:
            explanation_snapshot = self.explainer.build_empty(candle)
        replay_input: dict[str, Any] = {
            "engine_version": ENGINE_VERSION,
            "candle_id": candle.id,
            "timeframe": candle.timeframe,
            "open_time": candle.open_time.isoformat(),
            "close_time": candle.close_time.isoformat(),
            "ranking_snapshot": ranking_snapshot,
        }
        input_hash = hashlib.sha256(
            json.dumps(replay_input, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        before_seconds = int(self.settings.attribution_window_before_minutes) * 60
        after_seconds = int(self.settings.attribution_window_after_minutes) * 60
        row = AttributionReplayLog(
            candle_id=candle.id,
            engine_version=ENGINE_VERSION,
            input_hash=input_hash,
            candidate_event_count=len(ranked),
            timeline_window_before_seconds=before_seconds,
            timeline_window_after_seconds=after_seconds,
            ranking_snapshot_json=ranking_snapshot,
            explanation_snapshot_json=explanation_snapshot,
            created_at=utcnow(),
        )
        self.db.add(row)
        self.db.flush()
        return row

    def _ranking_entry(self, item: ScoredCandidate) -> dict[str, object]:
        return {
            "rank": item.rank,
            "event_id": item.event.id,
            "article_id": item.article_id,
            "title": item.event.canonical_title,
            "candidate_category": item.candidate_category,
            "attribution_type": item.attribution_type,
            "confidence_score": item.confidence_score,
            "time_distance_seconds": item.time_distance_seconds,
            "direction_match": item.direction_match,
        }
