from __future__ import annotations

from typing import Any

from bastion_ui.services.api_client import api_get, normalize_api_error


async def load_preview(path: str) -> dict[str, Any]:
    try:
        result = await api_get(path)
        return result if isinstance(result, dict) else {"items": result}
    except Exception as exc:
        return {"degraded": True, "error": normalize_api_error(exc)}
