from __future__ import annotations

from typing import Any

from bastion_ui.services.api_client import api_get, normalize_api_error


def unavailable(name: str) -> dict[str, Any]:
    return {"status": "unavailable", "preview_mode": True, "degraded": True, "message": f"{name} unavailable; preview state shown."}


async def safe_get(path: str, name: str) -> dict[str, Any]:
    try:
        result = await api_get(path)
        return result if isinstance(result, dict) else {"items": result, "preview_mode": False}
    except Exception as exc:
        fallback = unavailable(name)
        fallback["error"] = normalize_api_error(exc)
        return fallback


async def get_command_center_summary() -> dict[str, Any]:
    return await safe_get("/api/v1/public/status", "command center")


async def get_trace_wow_summary(report_id: str | int) -> dict[str, Any]:
    return await safe_get(f"/api/v1/public/trace/{report_id}/summary", "trace wow summary")


async def get_provider_trust_matrix() -> dict[str, Any]:
    return await safe_get("/api/v1/market/providers/health", "provider trust matrix")


async def get_market_intelligence_preview() -> dict[str, Any]:
    return await safe_get("/api/v1/signals/latest", "market intelligence preview")


async def get_sovereign_grid_preview() -> dict[str, Any]:
    return await safe_get("/api/v1/public/status", "sovereign grid")


async def get_audit_replay_preview() -> dict[str, Any]:
    return unavailable("audit replay")


async def get_api_contract_preview() -> dict[str, Any]:
    return unavailable("api contract preview")
