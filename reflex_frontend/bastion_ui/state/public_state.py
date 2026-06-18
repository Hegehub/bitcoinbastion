from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.services.errors import BastionApiError
from bastion_ui.services.public_client import get_features, get_landing


class PublicState(rx.State):
    loading: bool = False
    error_message: str = ""
    stale: bool = True
    landing: dict[str, Any] = {}
    features: list[dict[str, Any]] = []

    async def load_public_landing(self) -> None:
        self.loading = True
        try:
            data = await get_landing()
            self.landing = data if isinstance(data, dict) else {}
            feature_data = await get_features()
            self.features = feature_data if isinstance(feature_data, list) else []
            self.error_message = ""
            self.stale = False
        except BastionApiError as exc:
            self.error_message = exc.public_message
            self.stale = True
        finally:
            self.loading = False
