from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.schemas.market_time_machine_web import MarketTimelineDTO
from app.web.market_time_machine_service import FILTERS, SAFETY_LIMITATIONS, TIMEFRAMES, MarketTimeMachineWebService
from app.web.metrics import (
    CHART_MARKER_COUNT,
    EVIDENCE_PANEL_REQUESTS_TOTAL,
    MARKET_CANDLE_OPEN_TOTAL,
    MARKET_DASHBOARD_REQUESTS_TOTAL,
    MARKET_DASHBOARD_VIEWS_TOTAL,
    MARKET_EVIDENCE_OPEN_TOTAL,
    MARKET_EVIDENCE_VIEWS_TOTAL,
    MARKET_MARKER_CLICKS_TOTAL,
    MARKET_NARRATIVE_VIEWS_TOTAL,
    MARKET_REPLAY_OPEN_TOTAL,
    MARKET_REPLAY_VIEWS_TOTAL,
    MARKET_SIGNAL_VIEWS_TOTAL,
    MARKET_TIMELINE_REQUESTS_TOTAL,
    MARKET_UI_CANDLE_CLICKS_TOTAL,
    MARKET_UI_EVIDENCE_VIEWS_TOTAL,
    MARKET_UI_MARKER_CLICKS_TOTAL,
    MARKET_UI_PAGE_VIEWS_TOTAL,
    MARKET_UI_REPLAY_REQUESTS_TOTAL,
    TIMELINE_FILTER_USAGE_TOTAL,
    TIMELINE_RENDER_FAILURES_TOTAL,
    TIMELINE_REQUESTS_TOTAL,
    bounded_entity_type,
    bounded_filter_label,
    bounded_marker_type,
    bounded_timeframe,
)
from app.web.view_models.market import build_market_dto, page_frame

router = APIRouter(tags=["market-intelligence-web"])
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

MARKET_SECTIONS = {"timeline", "time-machine", "signals", "evidence", "narratives", "sources"}
LEGACY_SECTION_ALIASES = {"candles": "time-machine", "events": "timeline", "news": "timeline", "shock-index": "timeline"}


def _safe_context(request: Request, **extra: object) -> dict[str, object]:
    base: dict[str, object] = {
        "request": request,
        "safety_limitations": SAFETY_LIMITATIONS,
        "timeframes": TIMEFRAMES,
        "timeline_filters": FILTERS,
        "market_sections": ["Timeline", "Market Time Machine", "Narratives", "Signals", "Evidence", "Sources"],
    }
    base.update(extra)
    return base


def _service_payload(service: MarketTimeMachineWebService, *, timeframe: str, sort: str = "name") -> tuple[MarketTimelineDTO, dict[str, object]]:
    dto = service.dashboard(timeframe=timeframe)
    payload = service.landing_payload(timeframe=timeframe)
    payload["source_summary"] = service.source_summary(sort=sort)
    return dto, payload


def _dashboard_context(
    request: Request,
    db: Session,
    timeframe: str,
    date: str | None = None,
    *,
    sort: str = "name",
) -> dict[str, object]:
    selected_timeframe = timeframe if timeframe in TIMEFRAMES else "1h"
    service = MarketTimeMachineWebService(db)
    dto, payload = _service_payload(service, timeframe=selected_timeframe, sort=sort)
    CHART_MARKER_COUNT.labels(surface="html").set(float(len(dto.chart_markers)))
    return _safe_context(
        request,
        dto=dto,
        market_vm=build_market_dto(dto, selected_timeframe=selected_timeframe, selected_date=date, api_payload=payload),
        selected_timeframe=selected_timeframe,
    )


@router.get("/market", response_class=HTMLResponse)
def market_dashboard(
    request: Request,
    timeframe: str = Query(default="1h"),
    date: str | None = Query(default=None),
    db: Session = Depends(db_session),
) -> HTMLResponse:
    MARKET_DASHBOARD_VIEWS_TOTAL.inc()
    MARKET_DASHBOARD_REQUESTS_TOTAL.labels(surface="html").inc()
    MARKET_UI_PAGE_VIEWS_TOTAL.labels(page="dashboard").inc()
    try:
        context = _dashboard_context(request, db, timeframe, date)
    except OperationalError:
        TIMELINE_RENDER_FAILURES_TOTAL.labels(surface="market").inc()
        context = _safe_context(request, dto=None, market_vm=None, selected_timeframe=timeframe if timeframe in TIMEFRAMES else "1h")
    return templates.TemplateResponse(request, "market/dashboard.html", context)


@router.get("/market-time-machine", response_class=HTMLResponse)
@router.get("/market/time-machine", response_class=HTMLResponse)
def market_time_machine(
    request: Request,
    timeframe: str = Query(default="1h"),
    date: str | None = Query(default=None),
    db: Session = Depends(db_session),
) -> HTMLResponse:
    MARKET_DASHBOARD_REQUESTS_TOTAL.labels(surface="time_machine").inc()
    MARKET_UI_PAGE_VIEWS_TOTAL.labels(page="time_machine").inc()
    try:
        context = _dashboard_context(request, db, timeframe, date)
        context["frame"] = page_frame("time-machine")
    except OperationalError:
        TIMELINE_RENDER_FAILURES_TOTAL.labels(surface="time_machine").inc()
        context = _safe_context(request, dto=None, market_vm=None, frame=page_frame("time-machine"), selected_timeframe=timeframe if timeframe in TIMEFRAMES else "1h")
    return templates.TemplateResponse(request, "market/time_machine.html", context)


@router.get("/market/{section}", response_class=HTMLResponse)
def market_section(
    request: Request,
    section: str,
    timeframe: str = Query(default="1h"),
    date: str | None = Query(default=None),
    status: str = Query(default="all"),
    sort: str = Query(default="name"),
    db: Session = Depends(db_session),
) -> HTMLResponse:
    section = LEGACY_SECTION_ALIASES.get(section, section)
    if section not in MARKET_SECTIONS:
        section = "timeline"
    _record_section_metric(section)
    try:
        context = _dashboard_context(request, db, timeframe, date, sort=sort)
        context["frame"] = page_frame(section)
        context["selected_status"] = status
        context["selected_sort"] = sort
    except OperationalError:
        TIMELINE_RENDER_FAILURES_TOTAL.labels(surface=section).inc()
        context = _safe_context(request, dto=None, market_vm=None, frame=page_frame(section), selected_timeframe=timeframe if timeframe in TIMEFRAMES else "1h")
    return templates.TemplateResponse(request, "market/section.html", context)


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
        dto = MarketTimeMachineWebService(db).timeline(filter_name=filter, page=page, page_size=page_size, sort=sort, window=window)
    except OperationalError:
        TIMELINE_RENDER_FAILURES_TOTAL.labels(surface="timeline").inc()
        dto = None
    return templates.TemplateResponse(request, "market_timeline.html", _safe_context(request, dto=dto, selected_filter=filter, selected_window=window, sort=sort))


@router.get("/evidence/{packet_id}", response_class=HTMLResponse)
def evidence_viewer(request: Request, packet_id: int, db: Session = Depends(db_session)) -> HTMLResponse:
    MARKET_EVIDENCE_OPEN_TOTAL.inc()
    MARKET_EVIDENCE_VIEWS_TOTAL.labels(surface="html").inc()
    MARKET_UI_EVIDENCE_VIEWS_TOTAL.labels(surface="html").inc()
    EVIDENCE_PANEL_REQUESTS_TOTAL.labels(surface="html").inc()
    try:
        service = MarketTimeMachineWebService(db)
        dto = service.evidence_panel(packet_id)
        replay = service.replay_summary("evidence_packet", packet_id)
    except OperationalError:
        dto = None
        replay = None
    return templates.TemplateResponse(request, "evidence_viewer.html", _safe_context(request, packet_id=packet_id, dto=dto, replay=replay))


@router.get("/candles/{candle_id}", response_class=HTMLResponse)
def candle_attribution_view(request: Request, candle_id: int, db: Session = Depends(db_session)) -> HTMLResponse:
    MARKET_CANDLE_OPEN_TOTAL.inc()
    try:
        dto = MarketTimeMachineWebService(db).candle_attribution(candle_id)
    except OperationalError:
        dto = None
    return templates.TemplateResponse(request, "candle_attribution.html", _safe_context(request, candle_id=candle_id, dto=dto))


@router.get("/web/market-time-machine")
def web_market_time_machine_dto(timeframe: str = "1h", db: Session = Depends(db_session)) -> dict[str, object]:
    MARKET_DASHBOARD_REQUESTS_TOTAL.labels(surface="dto").inc()
    MARKET_TIMELINE_REQUESTS_TOTAL.labels(surface="dto").inc()
    TIMELINE_REQUESTS_TOTAL.labels(surface="dto").inc()
    try:
        selected_timeframe = timeframe if timeframe in TIMEFRAMES else "1h"
        service = MarketTimeMachineWebService(db)
        dto, payload = _service_payload(service, timeframe=selected_timeframe)
        CHART_MARKER_COUNT.labels(surface="dto").set(float(len(dto.chart_markers)))
        vm = build_market_dto(dto, selected_timeframe=selected_timeframe, api_payload=payload)
        return {**dto.model_dump(), **vm}
    except OperationalError:
        return {"market_timeline": {}, "timeline_events": [], "chart_data": {"candles": [], "markers": []}, "marker_data": [], "timeline_items": [], "chart_markers": [], "candles": [], "limitations": SAFETY_LIMITATIONS + ["Data temporarily unavailable."]}


@router.get("/web/timeline")
def web_timeline_dto(filter: str = "all", page: int = 1, page_size: int = 50, sort: str = "desc", window: str = "24h", db: Session = Depends(db_session)) -> dict[str, object]:
    MARKET_TIMELINE_REQUESTS_TOTAL.labels(surface="dto").inc()
    TIMELINE_REQUESTS_TOTAL.labels(surface="dto").inc()
    for item in filter.split(","):
        TIMELINE_FILTER_USAGE_TOTAL.labels(filter=bounded_filter_label(item.strip().lower())).inc()
    try:
        return MarketTimeMachineWebService(db).timeline(filter_name=filter, page=page, page_size=page_size, sort=sort, window=window).model_dump()
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
    MARKET_EVIDENCE_VIEWS_TOTAL.labels(surface="dto").inc()
    MARKET_UI_EVIDENCE_VIEWS_TOTAL.labels(surface="dto").inc()
    EVIDENCE_PANEL_REQUESTS_TOTAL.labels(surface="dto").inc()
    try:
        return MarketTimeMachineWebService(db).evidence_panel(packet_id).model_dump()
    except OperationalError:
        return {"packet_id": packet_id, "limitations": SAFETY_LIMITATIONS + ["Evidence unavailable."]}


@router.post("/web/market-time-machine/marker-click")
def record_marker_click(marker_type: str = "uncertain_news") -> dict[str, str]:
    MARKET_MARKER_CLICKS_TOTAL.inc()
    MARKET_UI_MARKER_CLICKS_TOTAL.labels(marker_type=bounded_marker_type(marker_type)).inc()
    return {"status": "recorded"}


@router.post("/web/market-time-machine/candle-click")
def record_candle_click(timeframe: str = "1h") -> dict[str, str]:
    MARKET_UI_CANDLE_CLICKS_TOTAL.labels(timeframe=bounded_timeframe(timeframe)).inc()
    return {"status": "recorded"}


@router.post("/web/market-time-machine/replay-open")
def record_replay_open(entity_type: str = "timeline") -> dict[str, str]:
    MARKET_REPLAY_OPEN_TOTAL.inc()
    MARKET_REPLAY_VIEWS_TOTAL.labels(surface="action").inc()
    MARKET_UI_REPLAY_REQUESTS_TOTAL.labels(entity_type=bounded_entity_type(entity_type)).inc()
    return {"status": "recorded"}


@router.post("/web/market-time-machine/evidence-view")
def record_evidence_view(surface: str = "panel") -> dict[str, str]:
    safe_surface = "panel" if surface == "panel" else "other"
    MARKET_EVIDENCE_VIEWS_TOTAL.labels(surface=safe_surface).inc()
    MARKET_UI_EVIDENCE_VIEWS_TOTAL.labels(surface=safe_surface).inc()
    return {"status": "recorded"}


def _record_section_metric(section: str) -> None:
    MARKET_UI_PAGE_VIEWS_TOTAL.labels(page=section).inc()
    if section == "timeline":
        MARKET_TIMELINE_REQUESTS_TOTAL.labels(surface="html").inc()
    elif section == "signals":
        MARKET_SIGNAL_VIEWS_TOTAL.labels(surface="html").inc()
    elif section == "evidence":
        MARKET_EVIDENCE_VIEWS_TOTAL.labels(surface="html").inc()
    elif section == "narratives":
        MARKET_NARRATIVE_VIEWS_TOTAL.labels(surface="html").inc()
