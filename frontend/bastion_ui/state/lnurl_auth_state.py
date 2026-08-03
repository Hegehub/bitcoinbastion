from __future__ import annotations

import reflex as rx

from bastion_ui.auth_errors import safe_auth_error
from bastion_ui.services.lnurl_client import LnurlService
from bastion_ui.state.wallet_auth_state import _error_code


class LnurlAuthState(rx.State):
    """Ephemeral presentation state; raw k1 and linking keys are never retained."""

    phase: str = "idle"
    challenge_id: str = ""
    display_lnurl: str = ""
    auth_domain: str = ""
    action: str = "login"
    expires_at: str = ""
    error: str = ""
    status_contract_available: bool = False

    async def create_challenge(self, origin: str, device_fingerprint: str) -> None:
        self.clear_challenge()
        self.phase = "generating"
        try:
            result = await LnurlService().create_auth_challenge(
                {
                    "action": self.action,
                    "origin": origin,
                    "device_key_fingerprint": device_fingerprint,
                    "requested_scopes": [],
                    "risk_context": {},
                    "client_capabilities": {},
                }
            )
            self.challenge_id = str(result.get("challenge_id", ""))
            self.display_lnurl = str(result.get("lnurl_bech32") or result.get("lnurl") or "")
            self.auth_domain = str(result.get("domain") or result.get("auth_domain") or "")
            self.expires_at = str(result.get("expires_at", ""))
            self.phase = "waiting_for_wallet"
        except Exception as exc:
            self.phase = "error"
            self.error = safe_auth_error(_error_code(exc)).message

    def clear_challenge(self) -> None:
        self.challenge_id = ""
        self.display_lnurl = ""
        self.auth_domain = ""
        self.expires_at = ""
        self.error = ""

    def expire_challenge(self) -> None:
        self.clear_challenge()
        self.phase = "expired"

    def consumed(self) -> None:
        self.clear_challenge()
        self.phase = "already_used"
