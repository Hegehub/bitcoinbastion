from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

from bastion_ui.access_client import AccessApiClient


@dataclass(frozen=True)
class LnurlApiClient(AccessApiClient):
    """Frontend adapter for implemented Bastion-side LNURL orchestration routes."""

    def create_auth_challenge(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/v1/lnurl/auth/challenges", payload)

    def create_auth_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/v1/lnurl/auth/sessions", payload)

    def auth_step_up(self, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        return self._post("/v1/lnurl/auth/step-up", payload, headers=headers)

    def create_subscription(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/v1/lnurl/pay/subscriptions", payload)

    def verify_payment(self, payment_id: str) -> dict[str, Any]:
        return self._get(f"/v1/lnurl/pay/verify/{quote(payment_id, safe='')}", raw_protocol=True)

    def create_withdraw(self, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        return self._post("/v1/lnurl/withdraw/requests", payload, headers=headers)

    @staticmethod
    def auth_status_supported() -> bool:
        return False

    @staticmethod
    def withdraw_status_supported() -> bool:
        return False
