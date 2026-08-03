from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.services.lnurl_client import LnurlService


class LnurlWithdrawState(rx.State):
    phase: str = "policy_check"
    amount_msat: int = 0
    purpose: str = ""
    policy_status: str = "unknown"
    display_lnurl: str = ""
    expires_at: str = ""
    error: str = ""

    async def create_withdraw(
        self, payload: dict[str, Any], signed_headers: dict[str, str]
    ) -> None:
        """Never publishes a withdraw LNURL until backend returns policy_approved=true."""
        self.display_lnurl = ""
        self.phase = "policy_check"
        try:
            result = await LnurlService().create_withdraw(payload, signed_headers)
            if result.get("policy_approved") is not True:
                self.policy_status = "denied"
                self.phase = "denied"
                self.error = "This payout is not permitted by the current access policy."
                return
            self.policy_status = "approved"
            self.display_lnurl = str(result.get("lnurl") or result.get("lnurl_bech32") or "")
            self.expires_at = str(result.get("expires_at", ""))
            self.phase = "waiting_for_invoice"
        except Exception:
            self.phase = "failed"
            self.error = (
                "Withdraw approval is unavailable. No payout was assumed or initiated locally."
            )
