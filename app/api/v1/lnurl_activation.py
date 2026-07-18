"""Safe LNURL successAction activation status routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.lnurl_success_action import LNURLActivationCompleteRequest, LNURLActivationStatusResponse
from app.services.lnurl.activation_service import LNURLActivationService, default_activation_service

router = APIRouter(prefix="/lnurl", tags=["lnurl-activation"])
_service = default_activation_service()


def get_lnurl_activation_service() -> LNURLActivationService:
    return _service


def _safe_error(exc: ValueError) -> HTTPException:
    reason = str(exc) or "activation_not_found"
    generic_not_found = {"activation_not_found"}
    status_code = status.HTTP_404_NOT_FOUND if reason in generic_not_found else status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=status_code, detail={"reason_code": reason})


@router.get("/activations/{activation_reference}", response_model=LNURLActivationStatusResponse)
async def get_activation_status(
    activation_reference: str,
    service: LNURLActivationService = Depends(get_lnurl_activation_service),
) -> LNURLActivationStatusResponse:
    try:
        return await service.get_activation_status(activation_reference)
    except ValueError as exc:
        raise _safe_error(exc) from exc


@router.post("/activations/{activation_reference}/complete", response_model=LNURLActivationStatusResponse)
async def complete_activation(
    activation_reference: str,
    request: LNURLActivationCompleteRequest,
    service: LNURLActivationService = Depends(get_lnurl_activation_service),
) -> LNURLActivationStatusResponse:
    try:
        return await service.complete_activation(
            activation_reference,
            expected_purpose=request.expected_purpose,
            device_key_fingerprint=request.device_key_fingerprint,
            active_pop_session_context=request.active_pop_session_context,
        )
    except ValueError as exc:
        raise _safe_error(exc) from exc


@router.get("/receipts/{activation_reference}", response_model=LNURLActivationStatusResponse)
async def get_receipt_status(
    activation_reference: str,
    service: LNURLActivationService = Depends(get_lnurl_activation_service),
) -> LNURLActivationStatusResponse:
    try:
        return await service.get_activation_status(activation_reference)
    except ValueError as exc:
        raise _safe_error(exc) from exc
