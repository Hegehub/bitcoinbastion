"""LNURL protocol endpoints that are not authenticated management APIs."""
from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.services.lnurl.withdraw_callback_verifier import (
    InMemorySensitiveInvoiceStore,
    LNURLWithdrawCallbackVerifier,
    LNURLWithdrawCallbackVerifierConfig,
)
from app.services.lnurl.withdraw_request_service import LNURLWithdrawRequestConfig, LNURLWithdrawRequestService

router = APIRouter(prefix="/lnurl", tags=["LNURL"])

_DEFAULT_WITHDRAW_REQUEST_SERVICE = LNURLWithdrawRequestService(
    config=LNURLWithdrawRequestConfig(enabled=True)
)
_DEFAULT_WITHDRAW_CALLBACK_VERIFIER = LNURLWithdrawCallbackVerifier(
    request_service=_DEFAULT_WITHDRAW_REQUEST_SERVICE,
    invoice_store=InMemorySensitiveInvoiceStore(),
    config=LNURLWithdrawCallbackVerifierConfig(
        server_pepper=_DEFAULT_WITHDRAW_REQUEST_SERVICE.config.server_pepper,
        require_protected_invoice_store=False,
    ),
)


def get_withdraw_callback_verifier() -> LNURLWithdrawCallbackVerifier:
    return _DEFAULT_WITHDRAW_CALLBACK_VERIFIER


@router.get("/withdraw/callback/{withdraw_id}", include_in_schema=True)
async def lnurl_withdraw_callback(
    withdraw_id: str,
    k1: str = Query(..., min_length=64, max_length=64),
    pr: str = Query(..., min_length=1),
) -> JSONResponse:
    verifier = get_withdraw_callback_verifier()
    result = await verifier.verify_callback(withdraw_id=withdraw_id, k1=k1, pr=pr)
    return JSONResponse(
        result.lnurl_response(),
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


__all__ = ["get_withdraw_callback_verifier", "lnurl_withdraw_callback", "router"]
