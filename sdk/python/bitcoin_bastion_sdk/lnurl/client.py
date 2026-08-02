from __future__ import annotations

from datetime import datetime
from typing import Any, cast

from bitcoin_bastion_sdk.lnurl.types import LNURLAuthChallenge, LNURLPayment, LNURLPaymentState
from bitcoin_bastion_sdk.safety import assert_safe


class LNURLClient:
    def __init__(self, transport: Any) -> None:
        self._transport = transport

    def create_auth_challenge(self, **payload: Any) -> LNURLAuthChallenge:
        assert_safe(payload)
        result = self._transport.request("POST", "/lnurl/auth/challenges", json=payload)
        return LNURLAuthChallenge(
            challenge_id=str(result["challenge_id"]),
            lnurl=str(result["lnurl"]),
            action=str(result["action"]),
            auth_domain=str(result["auth_domain"]),
            expires_at=datetime.fromisoformat(str(result["expires_at"]).replace("Z", "+00:00")),
            k1=result.get("k1"),
        )

    def create_session(self, **payload: Any) -> Any:
        return self._transport.request("POST", "/lnurl/auth/sessions", json=payload)

    def step_up(self, **payload: Any) -> Any:
        return self._transport.request("POST", "/lnurl/auth/step-up", json=payload, require_auth=True)

    def create_subscription_payment(self, *, plan: str, **payload: Any) -> LNURLPayment:
        request = {"plan": plan, **payload}
        assert_safe(request)
        result = self._transport.request("POST", "/lnurl/pay/subscriptions", json=request)
        return _payment(result, default_state="created")

    def request_invoice(
        self, payment_id: str, *, amount_msat: int, comment: str | None = None
    ) -> Any:
        params: dict[str, object] = {"amount": amount_msat}
        if comment is not None:
            params["comment"] = comment
        return self._transport.request("GET", f"/lnurl/pay/callback/{payment_id}", params=params)

    def verify_payment(self, payment_id: str) -> LNURLPayment:
        result = self._transport.request("GET", f"/lnurl/pay/verify/{payment_id}")
        return _payment(result, default_state="pending")

    def request_withdraw(self, **payload: Any) -> Any:
        assert_safe(payload)
        return self._transport.request("POST", "/lnurl/withdraw/requests", json=payload, require_auth=True)


def _payment(payload: dict[str, Any], *, default_state: str) -> LNURLPayment:
    state = LNURLPaymentState(str(payload.get("status", default_state)))
    return LNURLPayment(
        payment_id=str(payload["payment_id"]),
        state=state,
        lnurl=payload.get("lnurl"),
        min_sendable_msat=payload.get("min_sendable"),
        max_sendable_msat=payload.get("max_sendable"),
        entitlement_active=bool(payload.get("entitlement_active", False)),
    )


class AsyncLNURLClient:
    def __init__(self, transport: Any) -> None:
        self._transport = transport

    async def create_auth_challenge(self, **payload: Any) -> dict[str, Any]:
        assert_safe(payload)
        return cast(
            dict[str, Any],
            await self._transport.request("POST", "/lnurl/auth/challenges", json=payload),
        )

    async def create_session(self, **payload: Any) -> Any:
        return await self._transport.request("POST", "/lnurl/auth/sessions", json=payload)

    async def create_subscription_payment(self, *, plan: str, **payload: Any) -> LNURLPayment:
        result = await self._transport.request(
            "POST", "/lnurl/pay/subscriptions", json={"plan": plan, **payload}
        )
        return _payment(result, default_state="created")

    async def verify_payment(self, payment_id: str) -> LNURLPayment:
        result = await self._transport.request("GET", f"/lnurl/pay/verify/{payment_id}")
        return _payment(result, default_state="pending")
