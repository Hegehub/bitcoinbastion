from __future__ import annotations

from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

from app.core.config import get_settings


def _api_base_url() -> str:
    settings = get_settings()
    return settings.bot_api_base_url.rstrip("/")


def _auth_headers() -> dict[str, str]:
    token = get_settings().bot_api_bearer_token.strip()
    return {"Authorization": f"Bearer {token}"} if token else {}


@retry(stop=stop_after_attempt(3), wait=wait_fixed(0.2), reraise=True)
async def _request_with_retry(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.request(method, f"{_api_base_url()}{path}", json=payload, headers=_auth_headers())
        response.raise_for_status()
        return response.json()


async def _get(path: str) -> dict[str, Any]:
    return await _request_with_retry("GET", path)


async def _post(path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return await _request_with_retry("POST", path, payload)


def _first_line(text: str, *, max_len: int = 180) -> str:
    one_line = " ".join(text.split())
    return one_line if len(one_line) <= max_len else one_line[: max_len - 1] + "…"


def _failure_message(action: str, *, auth_required: bool = False) -> str:
    if auth_required:
        return f"Failed to {action} (check BOT_API_BASE_URL, BOT_API_BEARER_TOKEN, and permissions)."
    return f"Failed to {action} (check BOT_API_BASE_URL/API availability)."


def format_latest_news(envelope: dict[str, Any]) -> str:
    items = envelope.get("data", {}).get("items", [])
    if not items:
        return "No recent news items found."

    lines = ["Latest news:"]
    for idx, item in enumerate(items[:3], start=1):
        title = _first_line(str(item.get("title", "Untitled")))
        lines.append(f"{idx}. {title}")
    return "\n".join(lines)


def format_top_signals(envelope: dict[str, Any]) -> str:
    items = envelope.get("data", {}).get("items", [])
    if not items:
        return "No top signals available right now."

    lines = ["Top signals:"]
    for idx, item in enumerate(items[:3], start=1):
        signal_type = item.get("signal_type", "signal")
        confidence = item.get("confidence", 0)
        lines.append(f"{idx}. {signal_type} (confidence: {confidence})")
    return "\n".join(lines)


def format_fee_recommendation(envelope: dict[str, Any]) -> str:
    data = envelope.get("data", {})
    fee_rate = data.get("suggested_fee_rate_sat_vb", "n/a")
    rationale = _first_line(str(data.get("rationale", "No rationale.")), max_len=120)
    return f"Fee recommendation: {fee_rate} sat/vB. {rationale}"


def format_wallet_health(envelope: dict[str, Any]) -> str:
    data = envelope.get("data", {})
    score = data.get("health_score", "n/a")
    recommendations = data.get("recommendations", [])
    top_recommendation = recommendations[0] if recommendations else "No recommendations."
    return f"Wallet health score: {score}. {top_recommendation}"


def format_status(envelope: dict[str, Any]) -> str:
    status = envelope.get("status", "unknown")
    details = envelope.get("details", {})
    db = details.get("db", "unknown")
    redis = details.get("redis", "unknown")
    return f"System status: {status}. DB: {db}. Redis: {redis}."


def format_watchlist(envelope: dict[str, Any]) -> str:
    items = envelope.get("data", {}).get("items", [])
    if not items:
        return "Watchlist is empty."

    lines = ["Watchlist:"]
    for idx, item in enumerate(items[:5], start=1):
        name = item.get("name", "unknown")
        watch_type = item.get("watch_type", "watch")
        lines.append(f"{idx}. {name} ({watch_type})")
    return "\n".join(lines)


def format_admin_jobs(envelope: dict[str, Any]) -> str:
    jobs = envelope.get("data", [])
    if not jobs:
        return "No admin jobs registered."
    top = ", ".join(jobs[:8])
    return f"Admin jobs: {top}"


def format_recovery_refresh(envelope: dict[str, Any]) -> str:
    data = envelope.get("data", {})
    scanned = data.get("scanned", 0)
    updated = data.get("updated", 0)
    drifted = data.get("drifted", 0)
    return f"Provenance refresh done. scanned={scanned}, updated={updated}, drifted={drifted}."


async def latest_news_message() -> str:
    try:
        payload = await _get("/api/v1/news/latest?limit=3")
    except httpx.HTTPError:
        return _failure_message("load latest news")
    return format_latest_news(payload)


async def top_signals_message() -> str:
    try:
        payload = await _get("/api/v1/signals/top?limit=3")
    except httpx.HTTPError:
        return _failure_message("load top signals")
    return format_top_signals(payload)


async def digest_message() -> str:
    latest = await latest_news_message()
    top = await top_signals_message()
    return f"Daily digest:\n\n{latest}\n\n{top}"


async def fee_recommendation_message() -> str:
    try:
        payload = await _post(
            "/api/v1/fees/recommendation",
            {"mempool_congestion": 0.5, "target_blocks": 2},
        )
    except httpx.HTTPError:
        return _failure_message("load fee recommendation")
    return format_fee_recommendation(payload)


async def wallet_health_message() -> str:
    try:
        payload = await _post(
            "/api/v1/wallet/health",
            {"utxo_count": 12, "largest_utxo_share": 0.42, "avg_fee_rate_sat_vb": 18.0},
        )
    except httpx.HTTPError:
        return _failure_message("load wallet health")
    return format_wallet_health(payload)


async def status_message() -> str:
    try:
        payload = await _get("/api/v1/health/ready")
    except httpx.HTTPError:
        return _failure_message("load system status")
    return format_status(payload)


async def watchlist_message() -> str:
    try:
        payload = await _get("/api/v1/entities/watchlist?limit=5")
    except httpx.HTTPError:
        return _failure_message("load watchlist", auth_required=True)
    return format_watchlist(payload)


async def admin_jobs_message() -> str:
    try:
        payload = await _get("/api/v1/admin/jobs")
    except httpx.HTTPError:
        return _failure_message("load admin jobs", auth_required=True)
    return format_admin_jobs(payload)


async def admin_sources_refresh_message() -> str:
    try:
        await _post("/api/v1/news/sources/reputation/refresh")
    except httpx.HTTPError:
        return _failure_message("refresh source reputation")
    return "Source reputation refresh triggered."


async def admin_refresh_message() -> str:
    try:
        payload = await _post("/api/v1/entities/provenance/refresh?limit=200")
    except httpx.HTTPError:
        return _failure_message("run provenance refresh", auth_required=True)
    return format_recovery_refresh(payload)


async def admin_publish_message() -> str:
    try:
        payload = await _post("/api/v1/admin/jobs/retry", {"task_name": "delivery.publish"})
    except httpx.HTTPError:
        return _failure_message("queue delivery.publish", auth_required=True)
    task_id = payload.get("data", {}).get("task_id", "unknown")
    return f"Queued delivery.publish task: {task_id}."


async def admin_reprocess_message() -> str:
    try:
        payload = await _post("/api/v1/admin/jobs/retry", {"task_name": "ingestion.news"})
    except httpx.HTTPError:
        return _failure_message("queue ingestion.news", auth_required=True)
    task_id = payload.get("data", {}).get("task_id", "unknown")
    return f"Queued ingestion.news task: {task_id}."
