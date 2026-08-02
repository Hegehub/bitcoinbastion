"""Thin production HTTP adapter for the Bastion LNURL service layer.

Bastion API operations use the project envelope. Wallet callback operations use
raw LNURL protocol JSON and narrowly scoped public CORS. No route treats LNURL
proof, payment metadata, or a Lightning Address as unrestricted authorization.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Any, Protocol

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.api.response_envelope import ok
from app.api.wallet_auth_dependencies import require_wallet_policy
from app.core.exceptions import AppError
from app.schemas.lnurl import (
    LNURLApiAuthChallengeRequest,
    LNURLApiAuthSessionRequest,
    LNURLApiAuthStepUpRequest,
    LNURLApiPaySubscriptionRequest,
    LNURLApiWithdrawRequest,
)

router = APIRouter(prefix="/lnurl")

LNURL_PROTOCOL_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
}
GENERIC_AUTH_ERROR = "Authentication request could not be verified."
GENERIC_PAY_ERROR = "Payment request could not be completed."
GENERIC_WITHDRAW_ERROR = "Withdraw request could not be completed."

# Compatibility injection point retained for existing tests/deployments. There
# is deliberately no process-local production default.
_DEFAULT_WITHDRAW_REQUEST_SERVICE: Any | None = None
_DEFAULT_WITHDRAW_CALLBACK_VERIFIER: Any | None = None


def get_withdraw_callback_verifier() -> Any | None:
    return _DEFAULT_WITHDRAW_CALLBACK_VERIFIER


class LNURLApiBackend(Protocol):
    async def create_auth_challenge(self, request: LNURLApiAuthChallengeRequest) -> Mapping[str, Any]: ...
    async def auth_callback(self, *, k1: str, key: str, sig: str, action: str | None) -> Mapping[str, Any]: ...
    async def create_auth_session(self, request: LNURLApiAuthSessionRequest) -> Mapping[str, Any]: ...
    async def create_auth_step_up(self, context: Any, request: LNURLApiAuthStepUpRequest) -> Mapping[str, Any]: ...
    async def create_subscription(self, request: LNURLApiPaySubscriptionRequest) -> Mapping[str, Any]: ...
    async def pay_callback(self, payment_id: str, *, amount_msat: int, comment: str | None, payerdata: str | None) -> Mapping[str, Any]: ...
    async def verify_payment(self, payment_id: str) -> Mapping[str, Any]: ...
    async def create_withdraw(self, context: Any, request: LNURLApiWithdrawRequest) -> Mapping[str, Any]: ...
    async def withdraw_callback(self, withdraw_id: str, *, k1: str, pr: str) -> Mapping[str, Any]: ...


class UnconfiguredLNURLApiBackend:
    """No process-local security-state fallback is permitted in production."""

    def __getattr__(self, _name: str) -> Any:
        async def unavailable(*_args: Any, **_kwargs: Any) -> Mapping[str, Any]:
            raise AppError(
                message="LNURL service composition is unavailable.",
                status_code=503,
                code="lnurl_policy_denied",
            )

        return unavailable


def get_lnurl_api_backend() -> LNURLApiBackend:
    return UnconfiguredLNURLApiBackend()  # type: ignore[return-value]


@router.post(
    "/auth/challenges",
    tags=["LNURL Auth"],
    summary="Create a server-generated, single-use LNURL-auth challenge",
    description="Bastion generates k1. LNURL-auth proves Lightning wallet control only; it does not grant protected API access.",
)
async def create_lnurl_auth_challenge(
    payload: LNURLApiAuthChallengeRequest,
    backend: Annotated[LNURLApiBackend, Depends(get_lnurl_api_backend)],
) -> Mapping[str, Any]:
    return _envelope(await _bastion_call(backend.create_auth_challenge(payload)))


@router.get(
    "/auth/callback",
    tags=["LNURL Auth"],
    summary="LNURL-auth wallet callback (raw LNURL protocol response)",
)
async def lnurl_auth_callback(
    backend: Annotated[LNURLApiBackend, Depends(get_lnurl_api_backend)],
    k1: str = Query(..., min_length=64, max_length=64, pattern=r"^[0-9a-fA-F]{64}$"),
    key: str = Query(..., min_length=66, max_length=66, pattern=r"^(02|03)[0-9a-fA-F]{64}$"),
    sig: str = Query(..., min_length=4, max_length=160, pattern=r"^[0-9a-fA-F]+$"),
    action: str | None = None,
) -> JSONResponse:
    try:
        result = await backend.auth_callback(k1=k1.lower(), key=key.lower(), sig=sig.lower(), action=action)
        payload = dict(result)
        if payload.get("status") != "OK":
            payload = {"status": "ERROR", "reason": GENERIC_AUTH_ERROR}
    except Exception:
        payload = {"status": "ERROR", "reason": GENERIC_AUTH_ERROR}
    return _protocol(payload)


@router.post("/auth/sessions", tags=["LNURL Auth"], summary="Create a Device-bound PoP Session from a completed LNURL-auth attempt")
async def create_lnurl_auth_session(payload: LNURLApiAuthSessionRequest, backend: Annotated[LNURLApiBackend, Depends(get_lnurl_api_backend)]) -> Mapping[str, Any]:
    return _envelope(await _bastion_call(backend.create_auth_session(payload)))


@router.post("/auth/step-up", tags=["LNURL Auth"], summary="Create an action-bound LNURL-auth Human Intent step-up")
async def create_lnurl_auth_step_up(payload: LNURLApiAuthStepUpRequest, context: Annotated[Any, Depends(require_wallet_policy)], backend: Annotated[LNURLApiBackend, Depends(get_lnurl_api_backend)]) -> Mapping[str, Any]:
    return _envelope(await _bastion_call(backend.create_auth_step_up(context, payload)))


@router.post("/pay/subscriptions", tags=["LNURL Pay"], summary="Create an LNURL-pay subscription request; payment is not authentication")
async def create_lnurl_subscription(payload: LNURLApiPaySubscriptionRequest, backend: Annotated[LNURLApiBackend, Depends(get_lnurl_api_backend)]) -> Mapping[str, Any]:
    return _envelope(await _bastion_call(backend.create_subscription(payload)))


@router.get("/pay/callback/{payment_id}", tags=["LNURL Pay"], summary="Generate an invoice (raw LNURL-pay response); invoice creation is not settlement")
async def lnurl_pay_callback(payment_id: str, backend: Annotated[LNURLApiBackend, Depends(get_lnurl_api_backend)], amount: int = Query(..., gt=0), comment: str | None = Query(default=None, max_length=1000), payerdata: str | None = Query(default=None, max_length=4096)) -> JSONResponse:
    try:
        result = await backend.pay_callback(payment_id, amount_msat=amount, comment=comment, payerdata=payerdata)
        payload = dict(result)
        if "pr" not in payload:
            payload = {"status": "ERROR", "reason": GENERIC_PAY_ERROR}
    except Exception:
        payload = {"status": "ERROR", "reason": GENERIC_PAY_ERROR}
    return _protocol(payload)


@router.get("/pay/verify/{payment_id}", tags=["LNURL Pay"], summary="Verify trusted settlement state and idempotently bind Payment Proof/Entitlement")
async def verify_lnurl_payment(payment_id: str, backend: Annotated[LNURLApiBackend, Depends(get_lnurl_api_backend)]) -> JSONResponse:
    try:
        return _protocol(dict(await backend.verify_payment(payment_id)))
    except Exception:
        return _protocol({"status": "ERROR", "reason": GENERIC_PAY_ERROR})


@router.post("/withdraw/requests", tags=["LNURL Withdraw"], summary="Create a Policy-gated, short-lived LNURL-withdraw capability")
async def create_lnurl_withdraw(payload: LNURLApiWithdrawRequest, context: Annotated[Any, Depends(require_wallet_policy)], backend: Annotated[LNURLApiBackend, Depends(get_lnurl_api_backend)]) -> Mapping[str, Any]:
    return _envelope(await _bastion_call(backend.create_withdraw(context, payload)))


@router.get("/withdraw/callback/{withdraw_id}", tags=["LNURL Withdraw"], summary="Submit a wallet invoice to a single-use withdraw capability")
async def lnurl_withdraw_callback(withdraw_id: str, backend: Annotated[LNURLApiBackend, Depends(get_lnurl_api_backend)], k1: str = Query(..., min_length=64, max_length=64, pattern=r"^[0-9a-fA-F]{64}$"), pr: str = Query(..., min_length=1, max_length=4096)) -> JSONResponse:
    try:
        legacy_verifier = get_withdraw_callback_verifier()
        if legacy_verifier is not None:
            verified = await legacy_verifier.verify_callback(withdraw_id=withdraw_id, k1=k1.lower(), pr=pr)
            result = dict(verified.lnurl_response())
        else:
            result = dict(await backend.withdraw_callback(withdraw_id, k1=k1.lower(), pr=pr))
        if result.get("status") != "OK":
            result = {"status": "ERROR", "reason": GENERIC_WITHDRAW_ERROR}
    except Exception:
        result = {"status": "ERROR", "reason": GENERIC_WITHDRAW_ERROR}
    return _protocol(result)


async def _bastion_call(awaitable: Any) -> Mapping[str, Any]:
    try:
        return dict(await awaitable)
    except AppError:
        raise
    except Exception as exc:
        code = getattr(exc, "code", None) or getattr(exc, "reason_code", None) or "lnurl_policy_denied"
        raise AppError(message="LNURL request could not be completed.", status_code=403, code=str(code)) from exc


def _envelope(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    return ok(dict(payload)).model_dump(mode="json")


def _protocol(payload: Mapping[str, Any]) -> JSONResponse:
    return JSONResponse(dict(payload), headers=LNURL_PROTOCOL_HEADERS)


__all__ = ["LNURL_PROTOCOL_HEADERS", "get_lnurl_api_backend", "get_withdraw_callback_verifier", "router"]
