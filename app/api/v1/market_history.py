"""Strict historical Market read API."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.schemas.market_history import (
    BrowserSafeMarketSourceOut,
    MarketAttributionOut,
    MarketNarrativeOut,
    MarketReplayCaptureOut,
    MarketTimelinePageOut,
)
from app.services.intelligence.market_history_service import MarketHistoryService

router = APIRouter(prefix="/market/history", tags=["market-history"])


@router.get(
    "/timeline", response_model=MarketTimelinePageOut, operation_id="market_history_timeline"
)
def timeline(
    limit: int = Query(50, ge=1, le=200),
    before_sequence: int | None = Query(None, ge=1),
    db: Session = Depends(db_session),
) -> MarketTimelinePageOut:
    return MarketHistoryService(db).timeline(limit=limit, before_sequence=before_sequence)


@router.get(
    "/replay/event/{event_id}",
    response_model=MarketReplayCaptureOut,
    operation_id="market_history_replay_event",
)
def replay_event(event_id: int, db: Session = Depends(db_session)) -> MarketReplayCaptureOut:
    capture = MarketHistoryService(db).capture_for_event(event_id)
    if capture is None:
        raise HTTPException(status_code=404, detail="historical event not found")
    return capture


@router.get(
    "/attributions",
    response_model=tuple[MarketAttributionOut, ...],
    operation_id="market_history_attributions",
)
def attributions(
    limit: int = Query(50, ge=1, le=200), db: Session = Depends(db_session)
) -> tuple[MarketAttributionOut, ...]:
    return MarketHistoryService(db).attributions(limit)


@router.get(
    "/narratives",
    response_model=tuple[MarketNarrativeOut, ...],
    operation_id="market_history_narratives",
)
def narratives(
    limit: int = Query(50, ge=1, le=200), db: Session = Depends(db_session)
) -> tuple[MarketNarrativeOut, ...]:
    return MarketHistoryService(db).narratives(limit)


@router.get(
    "/sources",
    response_model=tuple[BrowserSafeMarketSourceOut, ...],
    operation_id="market_history_sources",
)
def sources(
    limit: int = Query(50, ge=1, le=200), db: Session = Depends(db_session)
) -> tuple[BrowserSafeMarketSourceOut, ...]:
    return MarketHistoryService(db).sources(limit)
