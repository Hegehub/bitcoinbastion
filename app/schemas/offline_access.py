"""Secret-free service/API contracts for Offline Validity Pack v1."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class OfflinePackIssueRequest(BaseModel):
    profile: str
    principal_reference: str
    device_binding_reference: str
    entitlement_reference: str
    access_certificate_reference: str | None = None
    requested_scopes: list[str] = Field(default_factory=list)
    requested_metric_groups: list[str] = Field(default_factory=list)
    requested_expires_at: datetime
    intent_signature_reference: str
    step_up_reference: str | None = None
    model_config = {"extra": "forbid"}


class OfflinePackIssueResponse(BaseModel):
    pack_fingerprint: str
    export_pack: dict[str, Any]
    expires_at: datetime
    warning: str


class OfflinePackVerificationRequest(BaseModel):
    pack: dict[str, Any]
    device_binding_reference: str
    principal_reference: str
    entitlement_reference: str
    certificate_reference: str | None = None
    model_config = {"extra": "forbid"}


class OfflinePackVerificationResponse(BaseModel):
    valid: bool
    decision: str
    reason_code: str
    restrictions: list[str] = Field(default_factory=list)


class OfflineOperationRequest(BaseModel):
    operation: str
    object_type: str
    value_amount: int = Field(default=0, ge=0)
    local_operation_count: int = Field(default=0, ge=0)
    queued_event_count: int = Field(default=0, ge=0)
    model_config = {"extra": "forbid"}


class OfflineOperationDecision(BaseModel):
    allowed: bool
    decision: str
    reason_code: str


class OfflinePackReconcileRequest(BaseModel):
    pack_fingerprint: str
    events: list[dict[str, Any]]
    event_chain_root: str
    model_config = {"extra": "forbid"}


class OfflinePackReconcileResponse(BaseModel):
    outcome: str
    event_count: int
    event_chain_root: str


class OfflinePackRevokeRequest(BaseModel):
    reason_code: str
    intent_signature_reference: str
    model_config = {"extra": "forbid"}


class OfflinePackListResponse(BaseModel):
    packs: list[dict[str, Any]]
