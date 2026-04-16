from app.bot.handlers.runtime_actions import (
    format_admin_jobs,
    format_fee_recommendation,
    format_latest_news,
    format_recovery_refresh,
    format_status,
    format_top_signals,
    format_wallet_health,
    format_watchlist,
)


def test_format_latest_news_handles_items() -> None:
    payload = {
        "data": {
            "items": [
                {"title": "First headline"},
                {"title": "Second headline"},
            ]
        }
    }

    out = format_latest_news(payload)
    assert "Latest news:" in out
    assert "1. First headline" in out


def test_format_top_signals_handles_items() -> None:
    payload = {"data": {"items": [{"signal_type": "onchain", "confidence": 0.88}]}}

    out = format_top_signals(payload)
    assert "Top signals:" in out
    assert "onchain" in out


def test_format_fee_recommendation_handles_payload() -> None:
    out = format_fee_recommendation({"data": {"suggested_fee_rate_sat_vb": 12, "rationale": "low congestion"}})
    assert "12 sat/vB" in out


def test_format_wallet_health_handles_payload() -> None:
    out = format_wallet_health({"data": {"health_score": 91.5, "recommendations": ["Consolidate UTXOs"]}})
    assert "91.5" in out
    assert "Consolidate UTXOs" in out


def test_format_status_handles_payload() -> None:
    out = format_status({"status": "ready", "details": {"db": "ok", "redis": "ok"}})
    assert "ready" in out
    assert "DB: ok" in out


def test_format_watchlist_handles_payload() -> None:
    payload = {"data": {"items": [{"name": "Entity A", "watch_type": "address"}]}}
    out = format_watchlist(payload)
    assert "Watchlist:" in out
    assert "Entity A" in out


def test_format_admin_jobs_handles_payload() -> None:
    out = format_admin_jobs({"data": ["delivery.publish", "ingestion.news"]})
    assert "Admin jobs:" in out
    assert "delivery.publish" in out


def test_format_recovery_refresh_handles_payload() -> None:
    out = format_recovery_refresh({"data": {"scanned": 10, "updated": 3, "drifted": 2}})
    assert "scanned=10" in out
    assert "updated=3" in out


def test_failure_message_auth_hint() -> None:
    from app.bot.handlers.runtime_actions import _failure_message

    out = _failure_message("load admin jobs", auth_required=True)
    assert "BOT_API_BEARER_TOKEN" in out


def test_auth_headers_include_bearer_token(monkeypatch) -> None:
    import app.bot.handlers.runtime_actions as runtime_actions

    class _S:
        bot_api_bearer_token = "abc123"

    monkeypatch.setattr(runtime_actions, "get_settings", lambda: _S())
    assert runtime_actions._auth_headers() == {"Authorization": "Bearer abc123"}
