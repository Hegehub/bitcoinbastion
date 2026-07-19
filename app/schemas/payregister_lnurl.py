"""OpenAPI-safe PayRegister LNURL schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class PayRegisterLNURLStaticEndpointCreate(BaseModel):
    public_alias: str = Field(description="Public non-secret static QR/NFC alias.")
    endpoint_mode: Literal["terminal_checkout", "store_open_amount", "fixed_product", "checkout_rotating"]
    merchant_workspace_hash: str
    store_hash: str
    terminal_hash: str | None = None
    min_sendable_msat: int = 1000
    max_sendable_msat: int = 100_000_000
    display_label: str = "PayRegister payment"
    merchant_description: str | None = None
    comment_allowed: int = 0


class PayRegisterLNURLStaticEndpointUpdate(BaseModel):
    display_label: str | None = None
    merchant_description: str | None = None


class PayRegisterLNURLStaticEndpointResponse(BaseModel):
    endpoint_id: str
    public_alias: str
    endpoint_mode: str
    enabled: bool
    status: str
    min_sendable_msat: int
    max_sendable_msat: int
    display_label: str
    merchant_description: str | None
    created_at: datetime
    updated_at: datetime


class PayRegisterLNURLCheckoutCreate(BaseModel):
    amount_msat: int | None = None
    description: str
    order_reference: str | None = None
    context_version: int | None = None
    ttl_seconds: int | None = None


class PayRegisterLNURLCheckoutResponse(BaseModel):
    payment_context_id: str
    status: str
    context_version: int
    min_sendable_msat: int
    max_sendable_msat: int
    metadata_hash: str
    expires_at: datetime


class PayRegisterLNURLQRResponse(BaseModel):
    raw_discovery_url: str
    lnurl: str
    public_alias: str
    endpoint_mode: str
    expires_at: datetime | None
    display_label: str
    safe_merchant_description: str | None


class PayRegisterLNURLNFCResponse(BaseModel):
    lnurl_text: str
    https_url: str
    ndef_records: tuple[dict[str, str], ...]
    public_alias: str
    endpoint_mode: str
    expires_at: datetime | None


class PayRegisterLNURLPayRequestResponse(BaseModel):
    tag: Literal["payRequest"]
    callback: str
    maxSendable: int
    minSendable: int
    metadata: str
    commentAllowed: int | None = None
    payerData: dict[str, Any] | None = None


class PayRegisterLNURLCallbackResponse(BaseModel):
    pr: str
    routes: list[Any]
    disposable: bool
    successAction: dict[str, Any] | None = None
    verify: str | None = None


class PayRegisterLNURLPaymentStatusResponse(BaseModel):
    payment_context_id: str
    status: str
    settled_at: datetime | None = None
    receipt_id: str | None = None


class PayRegisterReceiptResponse(BaseModel):
    receipt_id: str
    amount_msat: int
    settled_at: datetime
    metadata_hash: str
    payment_proof_fingerprint: str
    refund_status: str

class PayRegisterShiftOpenRequest(BaseModel):
    workspace_hash: str = Field(description="Workspace-scoped hash; never a raw workspace database ID.")
    store_hash: str
    terminal_hash: str
    role_binding_hash: str
    opening_device_fingerprint: str
    role: Literal["cashier", "senior_cashier", "shift_supervisor", "store_manager"] = "cashier"
    ttl_seconds: int = 28_800


class PayRegisterShiftResponse(BaseModel):
    shift_hash: str
    workspace_hash: str
    store_hash: str
    terminal_hash: str
    role_binding_hash: str
    status: str
    opened_at: datetime
    expires_at: datetime
    policy_hash: str


class PayRegisterShiftCloseRequest(BaseModel):
    shift_ref: str = Field(description="Shift hash or opaque shift reference.")


class PayRegisterPaymentContextCreate(BaseModel):
    amount_msat: int
    order_reference: str | None = None
    merchant_invoice_reference: str | None = None
    payment_purpose: str = "merchant_sale"
    customer_visible_description: str | None = None


class PayRegisterPaymentContextResponse(BaseModel):
    context_hash: str
    metadata_hash: str
    amount_msat: int
    currency: str
    payment_purpose: str
    expires_at: datetime


class PayRegisterShiftSummaryResponse(BaseModel):
    shift_hash: str
    status: str
    closed_at: datetime | None = None
    payment_count: int = 0
    receipt_count: int = 0
