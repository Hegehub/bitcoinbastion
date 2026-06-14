from __future__ import annotations

from typing import Any, cast

from bastion_ui.services.api_client import api_get


async def get_json(path: str) -> dict[str, Any]:
    return cast(dict[str, Any], await api_get(path))
