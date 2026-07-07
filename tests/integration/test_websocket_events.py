from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_websocket_routes_and_bounded_topics_exist() -> None:
    ws = (ROOT / "app/api/v1/ws.py").read_text(encoding="utf-8")
    for route in [
        "/ws/events",
        "/ws/signals",
        "/ws/news",
        "/ws/onchain",
        "/ws/market",
        "/ws/trace",
        "/ws/treasury",
        "/ws/provider-health",
        "/ws/intelligence-timeline",
    ]:
        assert route in ws
    assert "topics" in ws
    assert "limit_payload" in ws


def test_websocket_sdk_exposes_event_subscriptions() -> None:
    sdk = (ROOT / "sdk/python/bitcoin_bastion_sdk/websocket.py").read_text(encoding="utf-8")
    assert "/ws/events" in sdk
    assert "subscribe_events" in sdk
    assert "provider-health" in sdk
