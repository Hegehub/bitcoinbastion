from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.services.wallet_auth_client import WalletAuthService


class WalletDeviceState(rx.State):
    devices: list[dict[str, Any]] = []
    loading: bool = False
    error: str = ""

    async def load_devices(self, signed_headers: dict[str, str]) -> None:
        """Headers must come from the central PoP signer bridge, never UI fields."""
        self.loading = True
        try:
            result = await WalletAuthService().get_devices(signed_headers)
            items = result.get("items", result.get("devices", []))
            self.devices = items if isinstance(items, list) else []
        except Exception:
            self.error = "Device information is unavailable. Re-authenticate or retry."
        finally:
            self.loading = False
