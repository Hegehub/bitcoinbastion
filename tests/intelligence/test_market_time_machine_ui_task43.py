from __future__ import annotations

from app.main import app
from app.web.view_models.market import MARKER_CANONICAL_TYPES, build_market_dto
from tests.intelligence.test_market_time_machine_web_task41 import _client_with_db, _seed


def test_task43_market_pages_render_unified_time_machine_ui() -> None:
    client, SessionLocal = _client_with_db()
    with SessionLocal() as session:
        _seed(session)
    try:
        for path in [
            "/market",
            "/market/timeline",
            "/market/candles",
            "/market/events",
            "/market/news",
            "/market/narratives",
            "/market/shock-index",
        ]:
            response = client.get(path)
            assert response.status_code == 200
            assert "Market Time Machine" in response.text
            assert "Correlation is not proof of causation." in response.text
            assert "provider_health_visible" in response.text
        response = client.get("/market")
        assert "BTC Candlestick Chart" in response.text
        assert "Timeline Controls" in response.text
        assert "Provider Health Summary" in response.text
        assert "Current Shock Index" in response.text
        assert "aria-label=\"BTC candlestick chart with news markers\"" in response.text
        assert "@media (max-width: 820px)" in response.text
    finally:
        app.dependency_overrides.clear()


def test_task43_frontend_contract_dtos_and_marker_rendering() -> None:
    client, SessionLocal = _client_with_db()
    with SessionLocal() as session:
        _seed(session)
        dto = build_market_dto(__import__("app.web.market_time_machine_service", fromlist=["MarketTimeMachineWebService"]).MarketTimeMachineWebService(session).dashboard(timeframe="1h"), selected_timeframe="1h", db=session)
        assert set(["chart_data", "marker_data", "selected_candle", "selected_event", "historical_matches", "evidence_summary", "shock_index", "narrative_summary", "provider_health"]).issubset(dto)
        assert dto["chart_data"]["supports"] == ["zoom", "pan", "hover", "candle_selection", "marker_rendering", "responsive_resize"]
        assert dto["marker_data"][0]["canonical_type"] in set(MARKER_CANONICAL_TYPES.values())
        assert dto["selected_candle"]["safety_flags"]["correlation_not_causation"] is True
        assert dto["evidence_summary"]["operator_review_status"] == "display_only"
        assert dto["shock_index"]["bands"] == ["0-20 Quiet", "20-50 Active", "50-75 High Impact", "75-100 Shock Regime"]
    try:
        payload = client.get("/web/market-time-machine?timeframe=1h").json()
        assert "chart_data" in payload
        assert payload["marker_data"][0]["icon"] in {"🟢", "🔴", "🟡", "⚠️", "🏛", "🏦", "⛏", "⚡"}
        assert client.post("/web/market-time-machine/marker-click?marker_type=regulatory_event").json()["status"] == "recorded"
        assert client.post("/web/market-time-machine/candle-click?timeframe=1h").json()["status"] == "recorded"
        assert client.post("/web/market-time-machine/evidence-view").json()["status"] == "recorded"
        assert client.post("/web/market-time-machine/replay-open?entity_type=event").json()["status"] == "recorded"
    finally:
        app.dependency_overrides.clear()
