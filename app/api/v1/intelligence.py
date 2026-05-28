from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.db.models.attribution_replay_log import AttributionReplayLog
from app.db.models.btc_candle import BTCCandle
from app.db.models.candle_attribution import CandleAttribution
from app.db.models.candle_attribution_candidate import CandleAttributionCandidate
from app.services.intelligence.candle_attribution_engine import CandleAttributionEngine

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


@router.get("/candles/{candle_id}/attribution")
def get_candle_attribution(candle_id: int, db: Session = Depends(db_session)) -> dict[str, object]:
    try:
        candle = db.get(BTCCandle, candle_id)
        if candle is None:
            raise HTTPException(status_code=404, detail="candle_not_found")
        rows = CandleAttributionEngine(db).attribute_candle_object(candle)
        if not rows:
            replay = db.query(AttributionReplayLog).filter(AttributionReplayLog.candle_id == candle_id).order_by(AttributionReplayLog.id.desc()).first()
            explanation = replay.explanation_snapshot_json if replay else {"limitations": ["Correlation is not proof of causation."]}
            return {"candle": _candle_payload(candle), "candidate_events": [], "summary": explanation.get("summary", "No candidates found."), "limitations": explanation.get("limitations", [])}
        return {
            "candle": _candle_payload(candle),
            "candidate_events": [_attribution_payload(row) for row in rows],
            "summary": rows[0].summary_text,
            "limitations": rows[0].limitations_json.get("limitations", []) if isinstance(rows[0].limitations_json, dict) else [],
        }
    except OperationalError:
        return {"candle": None, "candidate_events": [], "summary": "Attribution storage is unavailable.", "limitations": ["Correlation is not proof of causation.", "Attribution tables are not available in this environment."]}


@router.get("/candles/{candle_id}/top-events")
def get_candle_top_events(candle_id: int, limit: int = 5, db: Session = Depends(db_session)) -> dict[str, object]:
    try:
        rows = db.query(CandleAttribution).filter(CandleAttribution.candle_id == candle_id).order_by(CandleAttribution.rank.asc()).limit(limit).all()
        return {"data": [_attribution_payload(row) for row in rows]}
    except OperationalError:
        return {"data": []}


@router.get("/candles/{candle_id}/replay")
def get_candle_replay(candle_id: int, limit: int = 5, db: Session = Depends(db_session)) -> dict[str, object]:
    try:
        rows = db.query(AttributionReplayLog).filter(AttributionReplayLog.candle_id == candle_id).order_by(AttributionReplayLog.id.desc()).limit(limit).all()
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
            "limitations": ["Correlation is not proof of causation.", "Attribution tables are not available in this environment."],
            "side_panel": {"primary_candidate": None, "candidate_count": 0},
            "evidence_drawer": {"items": []},
        }


@router.get("/candles/{candle_id}/candidates")
def get_candle_candidates(candle_id: int, limit: int = 50, db: Session = Depends(db_session)) -> dict[str, object]:
    try:
        rows = (
            db.query(CandleAttributionCandidate)
            .filter(CandleAttributionCandidate.candle_id == candle_id)
            .order_by(CandleAttributionCandidate.normalized_score.desc(), CandleAttributionCandidate.id.asc())
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
                    "raw_score": row.raw_score,
                    "normalized_score": row.normalized_score,
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
def get_high_confidence_impacts(limit: int = 50, db: Session = Depends(db_session)) -> dict[str, object]:
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
