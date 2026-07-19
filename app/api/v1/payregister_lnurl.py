"""PayRegister LNURL static QR/NFC API and protocol callbacks."""
from __future__ import annotations

from typing import Any
from dataclasses import asdict

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.schemas.payregister_lnurl import PayRegisterLNURLCheckoutCreate, PayRegisterLNURLStaticEndpointCreate, PayRegisterLNURLStaticEndpointUpdate
from app.services.lnurl.pay_callback_service import LNURLInvoiceProviderUnavailable, UnconfiguredLightningInvoiceProvider
from app.services.payregister.lnurl.callback import PayRegisterLNURLCallbackService
from app.services.payregister.lnurl.errors import PayRegisterLNURLError
from app.services.payregister.lnurl.payment_context import PayRegisterLNULEndpointMode
from app.services.payregister.lnurl.receipt import PayRegisterLNURLReceiptService
from app.services.payregister.lnurl.static_endpoint import get_default_payregister_lnurl_service

router = APIRouter(prefix="/payregister", tags=["PayRegister LNURL"])


def _cors(body: dict[str, Any], status_code: int = 200) -> JSONResponse:
    return JSONResponse(body, status_code=status_code, headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "no-store"})


def _endpoint_response(endpoint: Any) -> dict[str, Any]:
    return {
        "endpoint_id": endpoint.endpoint_id,
        "public_alias": endpoint.public_alias,
        "endpoint_mode": endpoint.endpoint_mode.value,
        "enabled": endpoint.enabled,
        "status": endpoint.status.value,
        "min_sendable_msat": endpoint.min_sendable_msat,
        "max_sendable_msat": endpoint.max_sendable_msat,
        "display_label": endpoint.display_label,
        "merchant_description": endpoint.merchant_description,
        "created_at": endpoint.created_at.isoformat(),
        "updated_at": endpoint.updated_at.isoformat(),
    }


@router.post("/lnurl/endpoints")
def create_endpoint(payload: PayRegisterLNURLStaticEndpointCreate) -> dict[str, Any]:
    service = get_default_payregister_lnurl_service()
    endpoint = service.create_static_endpoint(
        public_alias=payload.public_alias,
        endpoint_mode=PayRegisterLNULEndpointMode(payload.endpoint_mode),
        merchant_workspace_hash=payload.merchant_workspace_hash,
        store_hash=payload.store_hash,
        terminal_hash=payload.terminal_hash,
        min_sendable_msat=payload.min_sendable_msat,
        max_sendable_msat=payload.max_sendable_msat,
        display_label=payload.display_label,
        merchant_description=payload.merchant_description,
        comment_allowed=payload.comment_allowed,
    )
    return _endpoint_response(endpoint)


@router.get("/lnurl/endpoints")
def list_endpoints() -> dict[str, Any]:
    service = get_default_payregister_lnurl_service()
    return {"items": [_endpoint_response(endpoint) for endpoint in service.repository.list_endpoints()]}


@router.get("/lnurl/endpoints/{endpoint_id}")
def get_endpoint(endpoint_id: str) -> dict[str, Any]:
    service = get_default_payregister_lnurl_service()
    return _endpoint_response(service._endpoint(endpoint_id))


@router.patch("/lnurl/endpoints/{endpoint_id}")
def patch_endpoint(endpoint_id: str, payload: PayRegisterLNURLStaticEndpointUpdate) -> dict[str, Any]:
    service = get_default_payregister_lnurl_service()
    endpoint = service._endpoint(endpoint_id)
    from dataclasses import replace
    updated = replace(endpoint, display_label=payload.display_label or endpoint.display_label, merchant_description=payload.merchant_description or endpoint.merchant_description)
    service.repository.update_endpoint(updated)
    return _endpoint_response(updated)


@router.post("/lnurl/endpoints/{endpoint_id}/activate")
def activate_endpoint(endpoint_id: str) -> dict[str, Any]:
    return _endpoint_response(get_default_payregister_lnurl_service().activate_static_endpoint(endpoint_id))


@router.post("/lnurl/endpoints/{endpoint_id}/suspend")
def suspend_endpoint(endpoint_id: str) -> dict[str, Any]:
    return _endpoint_response(get_default_payregister_lnurl_service().suspend_static_endpoint(endpoint_id))


@router.post("/lnurl/endpoints/{endpoint_id}/rotate-alias")
def rotate_alias(endpoint_id: str, new_public_alias: str = Query(...)) -> dict[str, Any]:
    return _endpoint_response(get_default_payregister_lnurl_service().rotate_public_alias(endpoint_id, new_public_alias))


@router.post("/lnurl/endpoints/{endpoint_id}/checkout")
def publish_checkout(endpoint_id: str, payload: PayRegisterLNURLCheckoutCreate) -> dict[str, Any]:
    context = get_default_payregister_lnurl_service().publish_checkout_context(
        endpoint_id=endpoint_id,
        amount_msat=payload.amount_msat,
        description=payload.description,
        order_reference=payload.order_reference,
        context_version=payload.context_version,
        ttl_seconds=payload.ttl_seconds,
    )
    return {"payment_context_id": context.payment_context_id, "status": context.status.value, "context_version": context.context_version, "min_sendable_msat": context.min_sendable_msat, "max_sendable_msat": context.max_sendable_msat, "metadata_hash": context.metadata_hash, "expires_at": context.expires_at.isoformat()}


@router.get("/lnurl/endpoints/{endpoint_id}/qr")
def qr(endpoint_id: str) -> dict[str, Any]:
    return asdict(get_default_payregister_lnurl_service().build_qr_payload(endpoint_id))


@router.get("/lnurl/endpoints/{endpoint_id}/nfc")
def nfc(endpoint_id: str) -> dict[str, Any]:
    return asdict(get_default_payregister_lnurl_service().build_nfc_payload(endpoint_id))


@router.get("/lnurl/pay/callback/{payment_context_reference}")
async def callback(payment_context_reference: str, amount: int = Query(...), comment: str | None = None) -> JSONResponse:
    service = get_default_payregister_lnurl_service()
    callback_service = PayRegisterLNURLCallbackService(endpoint_service=service, invoice_provider=UnconfiguredLightningInvoiceProvider())
    try:
        result = await callback_service.create_invoice(payment_context_reference=payment_context_reference, amount_msat=amount, comment=comment)
        return _cors(result.to_lnurl_response())
    except (PayRegisterLNURLError, LNURLInvoiceProviderUnavailable):
        return _cors({"status": "ERROR", "reason": "Payment endpoint temporarily unavailable"}, status_code=200)


@router.get("/lnurl/pay/verify/{payment_context_reference}")
def verify(payment_context_reference: str) -> dict[str, Any]:
    context = get_default_payregister_lnurl_service().repository.get_context(payment_context_reference)
    return {"payment_context_id": payment_context_reference, "status": context.status.value if context else "unavailable", "settled_at": context.settled_at.isoformat() if context and context.settled_at else None, "receipt_id": context.receipt_id if context else None}


@router.get("/receipts/{receipt_reference}")
def receipt(receipt_reference: str) -> dict[str, Any]:
    service = get_default_payregister_lnurl_service()
    receipt_service = PayRegisterLNURLReceiptService(endpoint_service=service)
    for receipt_record in receipt_service.receipts_by_context_id.values():
        if receipt_record.receipt_reference == receipt_reference:
            return {"receipt_id": receipt_record.receipt_id, "amount_msat": receipt_record.amount_msat, "settled_at": receipt_record.settled_at.isoformat(), "metadata_hash": receipt_record.metadata_hash, "payment_proof_fingerprint": receipt_record.payment_proof_fingerprint, "refund_status": receipt_record.refund_status}
    return {"status": "ERROR", "reason": "Receipt unavailable"}
