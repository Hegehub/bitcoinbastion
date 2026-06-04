from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.web.market_time_machine_service import FILTERS, SAFETY_LIMITATIONS, TIMEFRAMES, MarketTimeMachineWebService
from app.web.metrics import (
    CHART_MARKER_COUNT,
    EVIDENCE_PANEL_REQUESTS_TOTAL,
    MARKET_CANDLE_OPEN_TOTAL,
    MARKET_DASHBOARD_VIEWS_TOTAL,
    MARKET_EVIDENCE_OPEN_TOTAL,
    MARKET_MARKER_CLICKS_TOTAL,
    MARKET_REPLAY_OPEN_TOTAL,
    MARKET_TIMELINE_REQUESTS_TOTAL,
    TIMELINE_FILTER_USAGE_TOTAL,
    TIMELINE_RENDER_FAILURES_TOTAL,
    TIMELINE_REQUESTS_TOTAL,
    bounded_filter_label,
)

router = APIRouter(tags=["market-time-machine-web"])
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def _safe_context(request: Request, **extra: object) -> dict[str, object]:
    base: dict[str, object] = {
        "request": request,
        "safety_limitations": SAFETY_LIMITATIONS,
        "timeframes": TIMEFRAMES,
        "timeline_filters": FILTERS,
    }
    base.update(extra)
    return base


@router.get("/market", response_class=HTMLResponse)
@router.get("/market-time-machine", response_class=HTMLResponse)
def market_time_machine(
    request: Request,
    timeframe: str = Query(default="1h"),
    db: Session = Depends(db_session),
) -> HTMLResponse:
    MARKET_DASHBOARD_VIEWS_TOTAL.inc()
    try:
        dto = MarketTimeMachineWebService(db).dashboard(timeframe=timeframe)
        CHART_MARKER_COUNT.labels(surface="html").set(float(len(dto.chart_markers)))
    except OperationalError:
        TIMELINE_RENDER_FAILURES_TOTAL.labels(surface="market").inc()
        dto = None
    return templates.TemplateResponse(
        request,
        "market_time_machine.html",
        _safe_context(request, dto=dto, selected_timeframe=timeframe if timeframe in TIMEFRAMES else "1h"),
    )


@router.get("/intelligence/timeline", response_class=HTMLResponse)
def market_timeline(
    request: Request,
    filter: str = Query(default="all"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    sort: str = Query(default="desc"),
    window: str = Query(default="24h"),
    db: Session = Depends(db_session),
) -> HTMLResponse:
    MARKET_TIMELINE_REQUESTS_TOTAL.labels(surface="html").inc()
    TIMELINE_REQUESTS_TOTAL.labels(surface="html").inc()
    for item in filter.split(","):
        TIMELINE_FILTER_USAGE_TOTAL.labels(filter=bounded_filter_label(item.strip().lower())).inc()
    try:
        dto = MarketTimeMachineWebService(db).timeline(
            filter_name=filter, page=page, page_size=page_size, sort=sort, window=window
        )
    except OperationalError:
        TIMELINE_RENDER_FAILURES_TOTAL.labels(surface="timeline").inc()
        dto = None
    return templates.TemplateResponse(
        request,
        "market_timeline.html",
        _safe_context(request, dto=dto, selected_filter=filter, selected_window=window, sort=sort),
    )


@router.get("/evidence/{packet_id}", response_class=HTMLResponse)
def evidence_viewer(request: Request, packet_id: int, db: Session = Depends(db_session)) -> HTMLResponse:
    MARKET_EVIDENCE_OPEN_TOTAL.inc()
    EVIDENCE_PANEL_REQUESTS_TOTAL.labels(surface="html").inc()
    try:
        dto = MarketTimeMachineWebService(db).evidence_panel(packet_id)
        replay = MarketTimeMachineWebService(db).replay_summary("evidence_packet", packet_id)
    except OperationalError:
        dto = None
        replay = None
    return templates.TemplateResponse(
        request,
        "evidence_viewer.html",
        _safe_context(request, packet_id=packet_id, dto=dto, replay=replay),
    )


@router.get("/candles/{candle_id}", response_class=HTMLResponse)
def candle_attribution_view(request: Request, candle_id: int, db: Session = Depends(db_session)) -> HTMLResponse:
    MARKET_CANDLE_OPEN_TOTAL.inc()
    try:
        dto = MarketTimeMachineWebService(db).candle_attribution(candle_id)
    except OperationalError:
        dto = None
    return templates.TemplateResponse(
        request,
        "candle_attribution.html",
        _safe_context(request, candle_id=candle_id, dto=dto),
    )


@router.get("/web/market-time-machine")
def web_market_time_machine_dto(timeframe: str = "1h", db: Session = Depends(db_session)) -> dict[str, object]:
    MARKET_TIMELINE_REQUESTS_TOTAL.labels(surface="dto").inc()
    TIMELINE_REQUESTS_TOTAL.labels(surface="dto").inc()
    try:
        dto = MarketTimeMachineWebService(db).dashboard(timeframe=timeframe)
        CHART_MARKER_COUNT.labels(surface="dto").set(float(len(dto.chart_markers)))
        return dto.model_dump()
    except OperationalError:
        return {"timeline_items": [], "chart_markers": [], "candles": [], "limitations": SAFETY_LIMITATIONS + ["Data temporarily unavailable."]}


@router.get("/web/timeline")
def web_timeline_dto(
    filter: str = "all",
    page: int = 1,
    page_size: int = 50,
    sort: str = "desc",
    window: str = "24h",
    db: Session = Depends(db_session),
) -> dict[str, object]:
    MARKET_TIMELINE_REQUESTS_TOTAL.labels(surface="dto").inc()
    TIMELINE_REQUESTS_TOTAL.labels(surface="dto").inc()
    for item in filter.split(","):
        TIMELINE_FILTER_USAGE_TOTAL.labels(filter=bounded_filter_label(item.strip().lower())).inc()
    try:
        return MarketTimeMachineWebService(db).timeline(
            filter_name=filter, page=page, page_size=page_size, sort=sort, window=window
        ).model_dump()
    except OperationalError:
        return {"timeline_items": [], "limitations": SAFETY_LIMITATIONS + ["Data temporarily unavailable."]}


@router.get("/web/candle/{candle_id}")
def web_candle_dto(candle_id: int, db: Session = Depends(db_session)) -> dict[str, object]:
    MARKET_CANDLE_OPEN_TOTAL.inc()
    try:
        return MarketTimeMachineWebService(db).candle_attribution(candle_id).model_dump()
    except OperationalError:
        return {"id": candle_id, "limitations": SAFETY_LIMITATIONS + ["Data temporarily unavailable."]}


@router.get("/web/evidence/{packet_id}")
def web_evidence_dto(packet_id: int, db: Session = Depends(db_session)) -> dict[str, object]:
    MARKET_EVIDENCE_OPEN_TOTAL.inc()
    EVIDENCE_PANEL_REQUESTS_TOTAL.labels(surface="dto").inc()
    try:
        return MarketTimeMachineWebService(db).evidence_panel(packet_id).model_dump()
    except OperationalError:
        return {"packet_id": packet_id, "limitations": SAFETY_LIMITATIONS + ["Evidence unavailable."]}


@router.post("/web/market-time-machine/marker-click")
def record_marker_click() -> dict[str, str]:
    MARKET_MARKER_CLICKS_TOTAL.inc()
    return {"status": "recorded"}


@router.post("/web/market-time-machine/replay-open")
def record_replay_open() -> dict[str, str]:
    MARKET_REPLAY_OPEN_TOTAL.inc()
    return {"status": "recorded"}
