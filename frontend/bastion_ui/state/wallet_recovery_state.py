from __future__ import annotations

import reflex as rx

from bastion_ui.services.wallet_auth_client import WalletAuthService


class WalletRecoveryState(rx.State):
    recovery_id: str = ""
    status: str = "idle"
    required_factors: list[str] = []
    completed_factors: list[str] = []
    cooldown_until: str = ""
    error: str = ""

    async def start(
        self, principal_reference: str, profile: str, new_device_public_key: str
    ) -> None:
        self.status = "starting"
        try:
            result = await WalletAuthService().start_recovery(
                {
                    "principal_reference": principal_reference,
                    "recovery_profile": profile,
                    "requested_action": "recovery_start",
                    "new_device_public_key": new_device_public_key,
                }
            )
            self.recovery_id = str(result.get("recovery_id", result.get("recovery_attempt_id", "")))
            self.status = str(result.get("status", "pending_factors"))
            self.required_factors = [str(item) for item in result.get("required_factors", [])]
            self.cooldown_until = str(result.get("cooldown_until", ""))
        except Exception:
            self.status = "error"
            self.error = "Recovery could not be started. No access state was changed locally."
