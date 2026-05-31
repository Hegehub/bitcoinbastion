from datetime import datetime
from typing import Any, cast

from fastapi import APIRouter, Depends
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.db.models.intelligence_timeline import IntelligenceTimelineEvent
from app.services.intelligence.timeline_service import TimelineService

router = APIRouter(prefix="/intelligence/timeline", tags=["intelligence-timeline"])
svc = TimelineService()


def _row(r: IntelligenceTimelineEvent) -> dict[str, Any]:
    return {"id": r.id, "event_type": r.event_type, "title": r.title, "summary": r.summary, "event_time": r.event_time, "importance": r.importance, "visibility": r.visibility, "confidence_score": r.confidence_score, "provider_confidence": r.provider_confidence, "related_article_id": r.related_article_id, "related_event_id": r.related_event_id, "related_signal_id": r.related_signal_id, "related_candle_id": r.related_candle_id, "evidence_refs_json": r.evidence_refs_json, "limitations_json": r.limitations_json}


@router.get("")
def get_timeline(db: Session = Depends(db_session), event_type: str | None = None, limit: int = 100) -> dict[str, object]:
    try:
        return {"data": [_row(r) for r in svc.get_timeline(db, limit=limit, event_type=event_type)]}
    except OperationalError:
        return {"data": []}


@router.get("/latest")
def get_latest(db: Session = Depends(db_session), limit: int = 20) -> dict[str, object]:
    try:
        return {"data": [_row(r) for r in svc.get_latest(db, limit=limit)]}
    except OperationalError:
        return {"data": []}


@router.get("/window")
def get_window(start: str, end: str, db: Session = Depends(db_session), limit: int = 500) -> dict[str, object]:
    try:
        return {"data": [_row(r) for r in svc.get_window(db, datetime.fromisoformat(start), datetime.fromisoformat(end), limit=limit)]}
    except OperationalError:
        return {"data": []}


@router.get("/context/{timeline_event_id}")
def get_context(timeline_event_id: int, db: Session = Depends(db_session)) -> dict[str, object]:
    try:
        ctx = svc.get_event_context(db, timeline_event_id)
    except OperationalError:
        return {"data": {"event": None, "related": []}}
    event = ctx["event"]
    related = cast(list[object], ctx["related"])
    return {"data": {"event": _row(event) if isinstance(event, IntelligenceTimelineEvent) else None, "related": [_row(r) for r in related if isinstance(r, IntelligenceTimelineEvent)]}}


@router.get("/narratives/current")
def current_narratives(limit: int = 20, db: Session = Depends(db_session)) -> dict[str, object]:
    from app.db.models.news_narrative_tag import NewsNarrativeTag
    rows = db.query(NewsNarrativeTag).order_by(NewsNarrativeTag.id.desc()).limit(limit).all()
    return {"data": [{"tag": r.tag, "confidence": r.confidence, "created_at": str(r.created_at)} for r in rows]}


@router.get("/news-impacts/high-confidence")
def high_confidence_news_impacts(limit: int = 50, db: Session = Depends(db_session)) -> dict[str, object]:
    from app.db.models.news_price_impact import NewsPriceImpact
    rows = db.query(NewsPriceImpact).filter(NewsPriceImpact.confidence_score >= 0.65).order_by(NewsPriceImpact.id.desc()).limit(limit).all()
    return {"data": [{"article_id": r.article_id, "event_id": r.event_id, "impact_confidence": r.confidence_score, "impact_band": r.confidence_band} for r in rows]}

@router.get("/news-impacts/recent")
def recent_news_impacts(limit: int = 50, db: Session = Depends(db_session)) -> dict[str, object]:
    from app.db.models.news_price_impact import NewsPriceImpact
    rows = db.query(NewsPriceImpact).order_by(NewsPriceImpact.id.desc()).limit(limit).all()
    return {"data": [{"article_id": r.article_id, "event_id": r.event_id, "impact_confidence": r.confidence_score, "impact_band": r.confidence_band} for r in rows]}
