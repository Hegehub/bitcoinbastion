from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.db.models.attribution_replay_log import AttributionReplayLog
from app.db.models.btc_candle import BTCCandle
from app.db.models.candle_attribution import CandleAttribution
from app.db.models.candle_attribution_candidate import CandleAttributionCandidate
from app.db.models.pattern_occurrence import PatternOccurrence
from app.services.intelligence.candle_attribution_engine import CandleAttributionEngine
from app.services.intelligence.candle_attribution_ranking import CandleAttributionRankingEngine
from app.services.intelligence.historical_similarity.historical_similarity_service import (
    HistoricalSimilarityService as PackagedHistoricalSimilarityService,
)
from app.services.intelligence.market_memory.engine import (
    HistoricalSimilarityEngine as MarketMemoryHistoricalSimilarityEngine,
)
from app.services.intelligence.market_memory.review import OperatorReviewService
from app.services.intelligence.market_memory.safety import MARKET_MEMORY_SAFETY_LIMITATIONS
from app.services.intelligence.historical_similarity_foundation import (
    HistoricalReactionService as FoundationHistoricalReactionService,
    HistoricalSimilarityService as FoundationHistoricalSimilarityService,
)
from app.services.intelligence.market_memory_service import MarketMemoryService
from app.services.intelligence.narrative_memory_service import NarrativeMemoryService
from app.services.intelligence.narrative_heatmap import (
    NarrativeHeatmapService,
    NarrativeRotationService,
    NARRATIVE_LIMITATION,
    NARRATIVE_SAFETY,
)
from app.web.market_time_machine_service import SAFETY_LIMITATIONS, MarketTimeMachineWebService
from app.web.metrics import EVIDENCE_PANEL_REQUESTS_TOTAL, SIMILARITY_PANEL_REQUESTS_TOTAL
from app.services.intelligence.historical_similarity_service import (
    CORRELATION_LIMITATION,
    HISTORICAL_OUTCOME_LIMITATION,
    PAST_PERFORMANCE_LIMITATION,
    HistoricalSimilarityService,
)

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


def _candle_payload(candle: BTCCandle | None) -> dict[str, object] | None:
    if candle is None:
        return None
    price_change_pct = 0.0
    if candle.open and candle.close and candle.open > 0:
        price_change_pct = ((candle.close - candle.open) / candle.open) * 100.0
    return {
        "id": candle.id,
        "timeframe": candle.timeframe,
        "open_time": candle.open_time,
        "close_time": candle.close_time,
        "price_change_pct": round(price_change_pct, 6),
        "provider_confidence": candle.provider_confidence,
        "is_degraded": candle.is_degraded,
    }


def _attribution_payload(row: CandleAttribution) -> dict[str, Any]:
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
        "attribution_type": row.attribution_type,
        "confidence": row.confidence_score,
        "confidence_band": row.confidence_band,
        "time_distance_minutes": round(row.time_distance_seconds / 60.0, 4),
        "direction_match": row.direction_match,
        "sentiment_direction_match": row.sentiment_direction_match,
        "is_primary_candidate": row.is_primary_candidate,
        "operator_review_status": row.operator_review_status,
        "summary": row.summary_text,
        "explanation": row.explanation_json,
        "limitations": row.limitations_json,
        "evidence_refs": row.evidence_refs_json,
    }


def _market_memory_safety(limitations: list[object]) -> list[str]:
    output = [str(item) for item in limitations]
    for item in MARKET_MEMORY_SAFETY_LIMITATIONS:
        if item not in output:
            output.append(item)
    return output


def _similarity_unavailable_payload() -> dict[str, object]:
    return {
        "data": [],
        "limitations": [
            CORRELATION_LIMITATION,
            HISTORICAL_OUTCOME_LIMITATION,
            PAST_PERFORMANCE_LIMITATION,
            "Historical similarity storage is unavailable in this environment.",
        ],
    }


@router.get("/similarity/news/{event_id}")
def get_news_similarity(
    event_id: int, limit: int = 10, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        return {
            "data": HistoricalSimilarityService(db).find_similar_news_events(event_id, limit=limit),
            "limitations": [
                CORRELATION_LIMITATION,
                PAST_PERFORMANCE_LIMITATION,
                HISTORICAL_OUTCOME_LIMITATION,
            ],
        }
    except OperationalError:
        return _similarity_unavailable_payload()


@router.get("/similarity/event/{event_id}")
def get_event_similarity(
    event_id: int, limit: int = 10, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        return {
            "data": HistoricalSimilarityService(db).find_similar_events(event_id, limit=limit),
            "limitations": [
                CORRELATION_LIMITATION,
                PAST_PERFORMANCE_LIMITATION,
                HISTORICAL_OUTCOME_LIMITATION,
            ],
        }
    except OperationalError:
        return _similarity_unavailable_payload()


@router.get("/similarity/candle/{candle_id}")
def get_candle_similarity(
    candle_id: int, limit: int = 10, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        return {
            "data": HistoricalSimilarityService(db).find_similar_candle_events(
                candle_id, limit=limit
            ),
            "limitations": [
                CORRELATION_LIMITATION,
                PAST_PERFORMANCE_LIMITATION,
                HISTORICAL_OUTCOME_LIMITATION,
            ],
        }
    except OperationalError:
        return _similarity_unavailable_payload()


def _pattern_payload(row: object) -> dict[str, object]:
    slug = getattr(row, "slug", getattr(row, "pattern_code", ""))
    name = getattr(row, "name", getattr(row, "display_name", slug))
    return {
        "id": getattr(row, "id", None),
        "slug": slug,
        "pattern_code": slug,
        "name": name,
        "display_name": getattr(row, "display_name", name) or name,
        "category": getattr(row, "category", "unknown"),
        "description": getattr(row, "description", ""),
        "expected_sentiment": getattr(
            row, "expected_sentiment", getattr(row, "default_sentiment", "UNKNOWN")
        ),
        "expected_direction": getattr(row, "expected_direction", "UNKNOWN"),
        "typical_sentiment": getattr(
            row, "typical_sentiment", getattr(row, "expected_sentiment", "UNKNOWN")
        ),
        "typical_direction": getattr(
            row, "typical_direction", getattr(row, "expected_direction", "UNKNOWN")
        ),
        "default_time_window": getattr(
            row, "default_time_window", getattr(row, "typical_impact_window", "1h")
        ),
        "typical_impact_window": getattr(
            row, "typical_impact_window", getattr(row, "expected_reaction_window", "unknown")
        ),
        "historical_reaction_profile": getattr(row, "historical_reaction_profile_json", {}),
        "confidence_rules": getattr(row, "confidence_rules_json", {}),
        "is_active": getattr(row, "is_active", True),
        "created_at": getattr(row, "created_at", None),
        "updated_at": getattr(row, "updated_at", None),
    }


@router.get("/similarity/events/{event_id}")
def get_event_similarity_report(
    event_id: int, limit: int = 10, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        return (
            PackagedHistoricalSimilarityService(db)
            .find_for_event(event_id, limit=limit)
            .model_dump()
        )
    except OperationalError:
        return _similarity_unavailable_payload()


@router.get("/similarity/articles/{article_id}")
def get_article_similarity_report(
    article_id: int, limit: int = 10, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        return (
            PackagedHistoricalSimilarityService(db)
            .find_for_article(article_id, limit=limit)
            .model_dump()
        )
    except OperationalError:
        return _similarity_unavailable_payload()


@router.get("/similarity/signals/{signal_id}")
def get_signal_similarity_report(
    signal_id: int, limit: int = 10, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        return (
            PackagedHistoricalSimilarityService(db)
            .find_for_signal(signal_id, limit=limit)
            .model_dump()
        )
    except OperationalError:
        return _similarity_unavailable_payload()


@router.get("/similarity/{event_id}")
def get_historical_similarity_context(
    event_id: int, limit: int = 10, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        payload = HistoricalSimilarityService(db).build_historical_context(event_id, limit=limit)
        db.commit()
        return payload
    except OperationalError:
        return _similarity_unavailable_payload()


@router.get("/similarity/{event_id}/matches")
def get_historical_similarity_matches(
    event_id: int, limit: int = 10, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        matches = HistoricalSimilarityService(db).find_similar_events(event_id, limit=limit)
        db.commit()
        return {
            "data": matches,
            "historical_matches": matches,
            "limitations": _market_memory_safety([HISTORICAL_OUTCOME_LIMITATION]),
        }
    except OperationalError:
        return _similarity_unavailable_payload()


@router.get("/similar-events/{event_id}")
def get_foundation_similar_events(
    event_id: int, limit: int = 10, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        payload = FoundationHistoricalSimilarityService(db).find_similar_events(
            event_id, limit=limit
        )
        db.commit()
        return payload
    except OperationalError:
        return _similarity_unavailable_payload()


@router.get("/reaction-profile/{event_id}")
def get_foundation_reaction_profile(
    event_id: int, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        service = FoundationHistoricalReactionService(db)
        profile = service.build_reaction_profile(event_id)
        if profile is None:
            raise HTTPException(status_code=404, detail="event_not_found")
        db.commit()
        return {
            "data": service.payload(profile),
            "limitations": [
                "Historical similarity does not imply future performance. Correlation is not proof of causation."
            ],
        }
    except OperationalError:
        return {"data": None, "limitations": ["Reaction profile storage is unavailable."]}


@router.get("/events/{event_id}/similar")
def get_event_market_memory_similarity(
    event_id: int, limit: int = 10, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        payload = MarketMemoryHistoricalSimilarityEngine(db).find_similar_events(
            event_id, limit=limit
        )
        db.commit()
        return payload
    except OperationalError:
        return _similarity_unavailable_payload()


@router.get("/events/{event_id}/memory")
def get_event_market_memory(event_id: int, db: Session = Depends(db_session)) -> dict[str, object]:
    try:
        payload = MarketMemoryService(db).event_memory(event_id)
        raw_limitations = payload.get("limitations", [])
        limitations = raw_limitations if isinstance(raw_limitations, list) else []
        payload["limitations"] = _market_memory_safety(limitations)
        return payload
    except OperationalError:
        return {
            "event_id": event_id,
            "pattern_matches": [],
            "similar_events": [],
            "confidence_history": [],
            "limitations": ["Market memory storage is unavailable."],
        }


@router.get("/patterns")
def list_market_patterns(db: Session = Depends(db_session)) -> dict[str, object]:
    try:
        rows = MarketMemoryService(db).ensure_patterns()
        return {
            "data": [_pattern_payload(row) for row in rows],
            "limitations": _market_memory_safety([HISTORICAL_OUTCOME_LIMITATION]),
        }
    except OperationalError:
        return {"data": [], "limitations": ["Pattern library storage is unavailable."]}


@router.get("/patterns/{pattern_id}/history")
def get_market_pattern_history(
    pattern_id: str, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        return {
            "data": MarketMemoryService(db).retrieve_pattern_history(pattern_id),
            "limitations": _market_memory_safety([HISTORICAL_OUTCOME_LIMITATION]),
        }
    except OperationalError:
        return {"data": [], "limitations": ["Pattern history storage is unavailable."]}


@router.get("/patterns/{pattern_id}/reaction-profile")
def get_market_pattern_reaction_profile(
    pattern_id: str, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        profile = MarketMemoryService(db).retrieve_reaction_profile(pattern_id)
        return {
            "data": (
                MarketMemoryService(db).reaction_profile_payload(profile)
                if profile is not None
                else None
            ),
            "limitations": _market_memory_safety([HISTORICAL_OUTCOME_LIMITATION]),
        }
    except OperationalError:
        return {"data": None, "limitations": ["Pattern reaction-profile storage is unavailable."]}


@router.get("/patterns/{pattern_id}/occurrences")
def get_market_pattern_occurrences(
    pattern_id: str, limit: int = 50, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        pattern = MarketMemoryService(db).get_pattern(pattern_id)
        if pattern is None:
            raise HTTPException(status_code=404, detail="pattern_not_found")
        rows = (
            db.query(PatternOccurrence)
            .filter(PatternOccurrence.pattern_id == pattern.id)
            .order_by(PatternOccurrence.occurred_at.desc(), PatternOccurrence.id.desc())
            .limit(max(0, min(limit, 200)))
            .all()
        )
        return {
            "data": [
                {
                    "id": row.id,
                    "pattern_id": row.pattern_id,
                    "article_id": row.article_id,
                    "event_id": row.event_id,
                    "impact_id": row.impact_id,
                    "attribution_id": row.attribution_id,
                    "signal_id": row.signal_id,
                    "occurred_at": row.occurred_at,
                    "confidence_score": row.confidence_score,
                    "classification_reason": row.classification_reason,
                    "created_at": row.created_at,
                }
                for row in rows
            ],
            "limitations": _market_memory_safety([HISTORICAL_OUTCOME_LIMITATION]),
        }
    except OperationalError:
        return {
            "data": [],
            "limitations": _market_memory_safety(["Pattern occurrence storage is unavailable."]),
        }


@router.get("/patterns/{pattern_id}")
def get_market_pattern(pattern_id: str, db: Session = Depends(db_session)) -> dict[str, object]:
    try:
        row = MarketMemoryService(db).get_pattern(pattern_id)
        if row is None:
            raise HTTPException(status_code=404, detail="pattern_not_found")
        return {
            "data": _pattern_payload(row),
            "limitations": _market_memory_safety([HISTORICAL_OUTCOME_LIMITATION]),
        }
    except OperationalError:
        return {"data": None, "limitations": ["Pattern library storage is unavailable."]}


@router.get("/patterns/{pattern_id}/statistics")
def get_market_pattern_statistics(
    pattern_id: str, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        pattern = MarketMemoryService(db).get_pattern(pattern_id)
        if pattern is None:
            raise HTTPException(status_code=404, detail="pattern_not_found")
        data = HistoricalSimilarityService(db).build_reaction_statistics(pattern.id)
        db.commit()
        return {
            "data": data,
            "reaction_statistics": data,
            "limitations": _market_memory_safety([]),
        }
    except OperationalError:
        return {
            "data": None,
            "limitations": _market_memory_safety(["Pattern statistics storage is unavailable."]),
        }


@router.get("/events/{event_id}/memory/replay")
def get_event_market_memory_replay(
    event_id: int, limit: int = 10, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        payload = MarketMemoryHistoricalSimilarityEngine(db).replay(event_id, limit=limit)
        db.commit()
        return payload
    except OperationalError:
        return {
            "event_analyzed": {"event_id": event_id},
            "candidate_events": [],
            "limitations": _market_memory_safety(["Replay storage is unavailable."]),
        }


@router.post("/events/{event_id}/memory/operator-review")
def create_event_market_memory_operator_review(
    event_id: int, payload: dict[str, object], db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        raw_pattern = payload.get("pattern")
        pattern = raw_pattern if isinstance(raw_pattern, (str, int)) else None
        raw_similar_event_id = payload.get("similar_event_id")
        similar_event_id = raw_similar_event_id if isinstance(raw_similar_event_id, int) else None
        raw_approved = payload.get("approved")
        approved = raw_approved if isinstance(raw_approved, bool) else None
        raw_override_confidence = payload.get("override_confidence")
        override_confidence = (
            float(raw_override_confidence)
            if isinstance(raw_override_confidence, (int, float))
            else None
        )
        row = OperatorReviewService(db).record_review(
            event_id=event_id,
            pattern=pattern,
            similar_event_id=similar_event_id,
            action=str(payload.get("action", "operator_review")),
            approved=approved,
            override_confidence=override_confidence,
            notes=str(payload.get("notes", "")),
            false_similarity=bool(payload.get("false_similarity", False)),
            operator=str(payload.get("operator", "operator")),
        )
        db.commit()
        return {
            "data": OperatorReviewService(db).payload(row),
            "limitations": _market_memory_safety([]),
        }
    except OperationalError:
        return {
            "data": None,
            "limitations": _market_memory_safety(["Operator review storage is unavailable."]),
        }


@router.get("/narratives")
def list_narratives(db: Session = Depends(db_session)) -> dict[str, object]:
    try:
        payload = {
            "data": NarrativeHeatmapService(db).list_narratives(),
            "limitations": [NARRATIVE_LIMITATION, NARRATIVE_SAFETY],
        }
        db.commit()
        return payload
    except OperationalError:
        return {"data": [], "limitations": ["Narrative storage is unavailable."]}


@router.get("/narratives/top")
def get_top_narratives(db: Session = Depends(db_session)) -> dict[str, object]:
    try:
        return NarrativeHeatmapService(db).top()
    except OperationalError:
        return {"data": [], "limitations": ["Narrative snapshot storage is unavailable."]}


@router.get("/narratives/rising")
def get_rising_narratives(db: Session = Depends(db_session)) -> dict[str, object]:
    try:
        return NarrativeHeatmapService(db).rising()
    except OperationalError:
        return {"data": [], "limitations": ["Narrative snapshot storage is unavailable."]}


@router.get("/narratives/falling")
def get_falling_narratives(db: Session = Depends(db_session)) -> dict[str, object]:
    try:
        return NarrativeHeatmapService(db).falling()
    except OperationalError:
        return {"data": [], "limitations": ["Narrative snapshot storage is unavailable."]}


@router.get("/narratives/emerging")
def get_emerging_narratives(db: Session = Depends(db_session)) -> dict[str, object]:
    try:
        return NarrativeHeatmapService(db).emerging()
    except OperationalError:
        return {"data": [], "limitations": ["Narrative snapshot storage is unavailable."]}


@router.get("/narratives/dominant")
def get_dominant_narratives(db: Session = Depends(db_session)) -> dict[str, object]:
    try:
        return NarrativeHeatmapService(db).dominant()
    except OperationalError:
        return {"data": [], "limitations": ["Narrative snapshot storage is unavailable."]}


@router.get("/narratives/heatmap")
def get_narrative_heatmap(
    window: str = "24h", db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        payload = NarrativeHeatmapService(db).build_heatmap(window=window)
        db.commit()
        return payload
    except OperationalError:
        return {
            "top_narratives": [],
            "top_rising_narratives": [],
            "top_falling_narratives": [],
            "highest_impact_narratives": [],
            "dominance_index": {},
            "limitations": ["Narrative heatmap storage is unavailable."],
        }


@router.get("/narratives/dominance")
def get_narrative_dominance(db: Session = Depends(db_session)) -> dict[str, object]:
    try:
        return NarrativeHeatmapService(db).dominance()
    except OperationalError:
        return {
            "data": {},
            "items": [],
            "limitations": ["Narrative dominance storage is unavailable."],
        }


@router.get("/narratives/active")
def get_active_narrative_memory(db: Session = Depends(db_session)) -> dict[str, object]:
    try:
        payload = {
            "data": NarrativeMemoryService(db).track_active_narratives(),
            "limitations": [NARRATIVE_LIMITATION, NARRATIVE_SAFETY, "historical_reference_only"],
        }
        db.commit()
        return payload
    except OperationalError:
        return {"data": [], "limitations": ["Narrative memory storage is unavailable."]}


@router.get("/narratives/memory")
def get_narrative_memory(db: Session = Depends(db_session)) -> dict[str, object]:
    try:
        payload = NarrativeMemoryService(db).build_narrative_snapshot()
        db.commit()
        return payload
    except OperationalError:
        return {"data": [], "limitations": ["Narrative memory storage is unavailable."]}


@router.get("/narratives/history")
def get_narrative_history(
    period: str = "month", limit: int = 20, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        heatmap_history = NarrativeHeatmapService(db).history(period=period, limit=limit)
        memory_history = NarrativeMemoryService(db).history(limit=limit)
        if isinstance(heatmap_history, dict):
            heatmap_history["memory_history"] = memory_history.get("data", [])
            return heatmap_history
        return memory_history
    except OperationalError:
        return {"data": [], "limitations": ["Narrative history storage is unavailable."]}


@router.get("/narratives/rotations")
def get_narrative_rotations(db: Session = Depends(db_session)) -> dict[str, object]:
    try:
        return {
            "data": NarrativeRotationService(db).detect_rotations(),
            "limitations": [NARRATIVE_LIMITATION, NARRATIVE_SAFETY],
        }
    except OperationalError:
        return {"data": [], "limitations": ["Narrative rotation storage is unavailable."]}


@router.get("/narratives/{slug}")
def get_narrative(slug: str, db: Session = Depends(db_session)) -> dict[str, object]:
    try:
        row = NarrativeHeatmapService(db).get_narrative(slug)
        if row is None:
            raise HTTPException(status_code=404, detail="narrative_not_found")
        db.commit()
        return {"data": row, "limitations": [NARRATIVE_LIMITATION, NARRATIVE_SAFETY]}
    except OperationalError:
        return {"data": None, "limitations": ["Narrative storage is unavailable."]}


@router.get("/candles/{candle_id}")
def get_candle_dashboard_dto(
    candle_id: int, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        return MarketTimeMachineWebService(db).candle_api_payload(candle_id)
    except OperationalError:
        return {
            "data": None,
            "limitations": SAFETY_LIMITATIONS + ["Candle storage is unavailable."],
        }


@router.get("/candles/{candle_id}/events")
def get_candle_events_dashboard_dto(
    candle_id: int, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        candle = MarketTimeMachineWebService(db).candle_attribution(candle_id)
        return {
            "data": candle.candidate_events,
            "candidate_news_events": candle.candidate_news_events,
            "candidate_macro_events": candle.candidate_macro_events,
            "candidate_security_events": candle.candidate_security_events,
            "candidate_narrative_events": candle.candidate_narrative_events,
            "confidence_score": candle.confidence,
            "limitations": candle.limitations,
        }
    except OperationalError:
        return {
            "data": [],
            "limitations": SAFETY_LIMITATIONS + ["Candle event storage is unavailable."],
        }


@router.get("/candles/{candle_id}/evidence")
def get_candle_evidence_dashboard_dto(
    candle_id: int, db: Session = Depends(db_session)
) -> dict[str, object]:
    EVIDENCE_PANEL_REQUESTS_TOTAL.labels(surface="api").inc()
    try:
        return MarketTimeMachineWebService(db).evidence_for_candle(candle_id).model_dump()
    except OperationalError:
        return {
            "packet_id": None,
            "limitations": SAFETY_LIMITATIONS + ["Evidence storage is unavailable."],
        }


@router.get("/candles/{candle_id}/similar")
def get_candle_similarity_dashboard_dto(
    candle_id: int, limit: int = 5, db: Session = Depends(db_session)
) -> dict[str, object]:
    SIMILARITY_PANEL_REQUESTS_TOTAL.labels(surface="api").inc()
    try:
        return {
            "data": MarketTimeMachineWebService(db).candle_similarity_preview(
                candle_id, limit=limit
            ),
            "limitations": SAFETY_LIMITATIONS + ["Historical similarity is reference-only."],
        }
    except OperationalError:
        return {
            "data": [],
            "limitations": SAFETY_LIMITATIONS + ["Similarity storage is unavailable."],
        }


@router.get("/events/{event_id}/timeline")
def get_event_timeline_dashboard_dto(
    event_id: int, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        service = MarketTimeMachineWebService(db)
        return {
            "data": service.event_context(event_id),
            "timeline_items": service.timeline_for_event(event_id),
            "chart_markers": [
                item.model_dump()
                for item in service.news_markers(limit=1000)
                if item.event_id == event_id
            ],
            "limitations": SAFETY_LIMITATIONS,
        }
    except OperationalError:
        return {
            "data": None,
            "timeline_items": [],
            "limitations": SAFETY_LIMITATIONS + ["Event timeline storage is unavailable."],
        }


@router.get("/candles/{candle_id}/attribution")
def get_candle_attribution(
    candle_id: int, limit: int = 5, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        candle = db.get(BTCCandle, candle_id)
        if candle is None:
            raise HTTPException(status_code=404, detail="candle_not_found")
        payload = CandleAttributionRankingEngine(db).attribute_candle(candle_id, limit=limit)
        db.commit()
        return payload
    except OperationalError:
        return {
            "candle": None,
            "candidate_events": [],
            "ranking": [],
            "confidence": 0.0,
            "summary": "Attribution storage is unavailable.",
            "limitations": [
                "Correlation is not proof of causation.",
                "Attribution tables are not available in this environment.",
            ],
        }


@router.get("/candles/{candle_id}/top-events")
def get_candle_top_events(
    candle_id: int, limit: int = 5, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        rows = (
            db.query(CandleAttribution)
            .filter(CandleAttribution.candle_id == candle_id)
            .order_by(CandleAttribution.rank.asc())
            .limit(limit)
            .all()
        )
        return {"data": [_attribution_payload(row) for row in rows]}
    except OperationalError:
        return {"data": []}


@router.get("/candles/{candle_id}/replay")
def get_candle_replay(
    candle_id: int, limit: int = 5, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        rows = (
            db.query(AttributionReplayLog)
            .filter(AttributionReplayLog.candle_id == candle_id)
            .order_by(AttributionReplayLog.id.desc())
            .limit(limit)
            .all()
        )
        return {
            "data": [
                {
                    "id": row.id,
                    "candle_id": row.candle_id,
                    "engine_version": row.engine_version,
                    "input_hash": row.input_hash,
                    "candidate_event_count": row.candidate_event_count,
                    "timeline_window_before_seconds": row.timeline_window_before_seconds,
                    "timeline_window_after_seconds": row.timeline_window_after_seconds,
                    "ranking_snapshot": row.ranking_snapshot_json,
                    "explanation_snapshot": row.explanation_snapshot_json,
                    "created_at": row.created_at,
                }
                for row in rows
            ]
        }
    except OperationalError:
        return {"data": []}


@router.get("/candles/{candle_id}/explain")
def explain_candle(candle_id: int, db: Session = Depends(db_session)) -> dict[str, object]:
    try:
        payload = CandleAttributionEngine(db).explain_candle(candle_id)
        if payload.get("error") == "candle_not_found":
            raise HTTPException(status_code=404, detail="candle_not_found")
        return payload
    except OperationalError:
        return {
            "candle": None,
            "ranked_candidate_events": [],
            "summary": "Attribution storage is unavailable.",
            "limitations": [
                "Correlation is not proof of causation.",
                "Attribution tables are not available in this environment.",
            ],
            "side_panel": {"primary_candidate": None, "candidate_count": 0},
            "evidence_drawer": {"items": []},
        }


@router.get("/candles/{candle_id}/context")
def get_candle_context(candle_id: int, db: Session = Depends(db_session)) -> dict[str, object]:
    try:
        row = CandleAttributionEngine(db).get_context_snapshot(candle_id)
        if row is None:
            raise HTTPException(status_code=404, detail="candle_not_found")
        return {
            "data": {
                "id": row.id,
                "candle_id": row.candle_id,
                "volatility_level": row.volatility_level,
                "volume_level": row.volume_level,
                "provider_confidence": row.provider_confidence,
                "market_regime": row.market_regime,
                "news_density": row.news_density,
                "event_density": row.event_density,
                "positive_event_count": row.positive_event_count,
                "negative_event_count": row.negative_event_count,
                "macro_event_count": row.macro_event_count,
                "security_event_count": row.security_event_count,
                "regulatory_event_count": row.regulatory_event_count,
                "institutional_event_count": row.institutional_event_count,
                "summary": row.summary_json,
                "created_at": row.created_at,
            }
        }
    except OperationalError:
        return {"data": None, "limitations": ["Candle context storage is unavailable."]}


@router.get("/candles/{candle_id}/candidates")
def get_candle_candidates(
    candle_id: int, limit: int = 50, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        rows = (
            db.query(CandleAttributionCandidate)
            .filter(CandleAttributionCandidate.candle_id == candle_id)
            .order_by(
                CandleAttributionCandidate.normalized_score.desc(),
                CandleAttributionCandidate.id.asc(),
            )
            .limit(limit)
            .all()
        )
        return {
            "data": [
                {
                    "id": row.id,
                    "candle_id": row.candle_id,
                    "candidate_type": row.candidate_type,
                    "event_id": row.event_id,
                    "article_id": row.article_id,
                    "time_distance_seconds": row.time_distance_seconds,
                    "relevance_score": row.relevance_score,
                    "direction_match_score": row.direction_match_score,
                    "impact_alignment_score": row.impact_alignment_score,
                    "recency_score": row.recency_score,
                    "raw_score": row.raw_score,
                    "normalized_score": row.normalized_score,
                    "metadata": row.metadata_json,
                    "ranking_features": row.ranking_features_json,
                    "rejection_reason": row.rejection_reason,
                    "created_at": row.created_at,
                }
                for row in rows
            ]
        }
    except OperationalError:
        return {"data": []}


@router.patch("/candles/attributions/{attribution_id}/review")
def review_candle_attribution(
    attribution_id: int,
    status: str,
    operator_note: str = "",
    confidence_override: float | None = None,
    db: Session = Depends(db_session),
) -> dict[str, object]:
    try:
        row = CandleAttributionEngine(db).review_attribution(
            attribution_id=attribution_id,
            status=status,
            operator_note=operator_note,
            confidence_override=confidence_override,
        )
        if row is None:
            raise HTTPException(status_code=404, detail="attribution_not_found")
        db.commit()
        return {"data": _attribution_payload(row)}
    except OperationalError:
        return {"data": None, "limitations": ["Attribution storage is unavailable."]}


@router.get("/impact/high-confidence")
def get_high_confidence_impacts(
    limit: int = 50, db: Session = Depends(db_session)
) -> dict[str, object]:
    try:
        from app.db.models.news_price_impact import NewsPriceImpact

        rows = (
            db.query(NewsPriceImpact)
            .filter(NewsPriceImpact.impact_confidence_score >= 0.65)
            .order_by(NewsPriceImpact.impact_confidence_score.desc(), NewsPriceImpact.id.desc())
            .limit(limit)
            .all()
        )
        return {
            "data": [
                {
                    "article_id": row.article_id,
                    "event_id": row.event_id,
                    "impact_confidence": row.impact_confidence_score,
                    "confidence_band": row.impact_band,
                    "dominant_window": row.dominant_window,
                    "provider_confidence": row.provider_confidence,
                    "limitations": row.limitations_json,
                }
                for row in rows
            ]
        }
    except OperationalError:
        return {"data": []}
