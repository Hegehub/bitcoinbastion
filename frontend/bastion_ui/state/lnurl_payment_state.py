from __future__ import annotations

import reflex as rx

from bastion_ui.auth_errors import safe_auth_error
from bastion_ui.services.lnurl_client import LnurlService
from bastion_ui.state.wallet_auth_state import _error_code


class LnurlPaymentState(rx.State):
    payment_id: str = ""
    plan: str = ""
    display_lnurl: str = ""
    amount_msat: int = 0
    expires_at: str = ""
    invoice_state: str = "not_issued"
    settlement_state: str = "not_settled"
    entitlement_state: str = "inactive"
    comment_allowed: int = 0
    error: str = ""

    async def create_payment(self) -> None:
        self.invoice_state = "creating"
        self.settlement_state = "not_settled"
        self.entitlement_state = "inactive"
        try:
            result = await LnurlService().create_subscription_payment(
                {
                    "plan_code": self.plan,
                    "duration_days": 30,
                    "comment_allowed": self.comment_allowed,
                    "payerdata_auth_requested": True,
                    "success_action_requested": True,
                }
            )
            self.payment_id = str(result.get("payment_id", ""))
            self.display_lnurl = str(result.get("lnurl") or result.get("lnurl_bech32") or "")
            self.expires_at = str(result.get("expires_at", ""))
            self.invoice_state = "payment_request_created"
        except Exception as exc:
            self.invoice_state = "failed"
            self.error = safe_auth_error(_error_code(exc)).message

    async def verify_payment(self) -> None:
        self.settlement_state = "verifying"
        try:
            result = await LnurlService().verify_payment(self.payment_id)
            settled = result.get("settled") is True
            self.settlement_state = "settled" if settled else "payment_pending"
            entitlement = result.get("entitlement_reference") or result.get("entitlement_hash")
            self.entitlement_state = "active" if settled and entitlement else "inactive"
        except Exception as exc:
            self.settlement_state = "failed"
            self.entitlement_state = "inactive"
            self.error = safe_auth_error(_error_code(exc)).message
