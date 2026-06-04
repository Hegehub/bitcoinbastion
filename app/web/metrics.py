from prometheus_client import Counter, Gauge

MARKET_DASHBOARD_VIEWS_TOTAL = Counter(
    "market_dashboard_views_total", "Total Market Time Machine dashboard views."
)
MARKET_TIMELINE_REQUESTS_TOTAL = Counter(
    "market_timeline_requests_total", "Total market timeline page or DTO requests.", ["surface"]
)
MARKET_MARKER_CLICKS_TOTAL = Counter(
    "market_marker_clicks_total", "Total market marker open events recorded by bounded action."
)
MARKET_CANDLE_OPEN_TOTAL = Counter(
    "market_candle_open_total", "Total candle attribution views."
)
MARKET_EVIDENCE_OPEN_TOTAL = Counter(
    "market_evidence_open_total", "Total evidence panel or page views."
)
MARKET_REPLAY_OPEN_TOTAL = Counter(
    "market_replay_open_total", "Total replay open actions."
)

TIMELINE_REQUESTS_TOTAL = Counter(
    "timeline_requests_total", "Total Market Timeline API and web requests.", ["surface"]
)
TIMELINE_RENDER_FAILURES_TOTAL = Counter(
    "timeline_render_failures_total", "Total Market Timeline render failures.", ["surface"]
)
CHART_MARKER_COUNT = Gauge(
    "chart_marker_count", "Number of chart markers emitted for the latest bounded request.", ["surface"]
)
TIMELINE_FILTER_USAGE_TOTAL = Counter(
    "timeline_filter_usage_total", "Total timeline filter usage by bounded filter name.", ["filter"]
)
EVIDENCE_PANEL_REQUESTS_TOTAL = Counter(
    "evidence_panel_requests_total", "Total evidence panel requests.", ["surface"]
)
SIMILARITY_PANEL_REQUESTS_TOTAL = Counter(
    "similarity_panel_requests_total", "Total similarity panel requests.", ["surface"]
)


MARKET_DASHBOARD_REQUESTS_TOTAL = Counter(
    "market_dashboard_requests_total", "Total Market Intelligence dashboard requests.", ["surface"]
)
MARKET_EVIDENCE_VIEWS_TOTAL = Counter(
    "market_evidence_views_total", "Total Market Intelligence evidence view requests.", ["surface"]
)
MARKET_REPLAY_VIEWS_TOTAL = Counter(
    "market_replay_views_total", "Total Market Intelligence replay view requests.", ["surface"]
)
MARKET_SIGNAL_VIEWS_TOTAL = Counter(
    "market_signal_views_total", "Total Market Intelligence signal view requests.", ["surface"]
)
MARKET_NARRATIVE_VIEWS_TOTAL = Counter(
    "market_narrative_views_total", "Total Market Intelligence narrative view requests.", ["surface"]
)

MARKET_UI_PAGE_VIEWS_TOTAL = Counter(
    "market_ui_page_views_total", "Total Market Time Machine UI page views.", ["page"]
)
MARKET_UI_MARKER_CLICKS_TOTAL = Counter(
    "market_ui_marker_clicks_total", "Total Market Time Machine marker clicks.", ["marker_type"]
)
MARKET_UI_CANDLE_CLICKS_TOTAL = Counter(
    "market_ui_candle_clicks_total", "Total Market Time Machine candle clicks.", ["timeframe"]
)
MARKET_UI_REPLAY_REQUESTS_TOTAL = Counter(
    "market_ui_replay_requests_total", "Total Market Time Machine replay requests.", ["entity_type"]
)
MARKET_UI_EVIDENCE_VIEWS_TOTAL = Counter(
    "market_ui_evidence_views_total", "Total Market Time Machine evidence views.", ["surface"]
)

BOUNDED_FILTER_LABELS = {
    "all",
    "positive",
    "negative",
    "security",
    "regulatory",
    "institutional",
    "mining",
    "lightning",
    "macro",
    "high_confidence",
    "operator_reviewed",
}

def bounded_filter_label(value: str) -> str:
    return value if value in BOUNDED_FILTER_LABELS else "other"


def bounded_marker_type(value: str) -> str:
    allowed = {"positive_news", "negative_news", "uncertain_news", "security_shock", "regulatory_event", "institutional_event", "macro_event", "bitcoin_core_event", "lightning_event", "mining_event", "lightning_or_core_event"}
    return value if value in allowed else "other"


def bounded_timeframe(value: str) -> str:
    return value if value in {"1m", "5m", "15m", "1h", "4h", "1d"} else "other"


def bounded_entity_type(value: str) -> str:
    return value if value in {"candle", "event", "evidence_packet", "timeline"} else "other"
