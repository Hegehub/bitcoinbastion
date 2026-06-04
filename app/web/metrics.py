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
