"""Pydantic schemas for Access metric catalog and entitlement responses."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.domain.access.plans import PlanCode


class MetricDefinition(BaseModel):
    name: str = Field(description="Stable metric name.")
    group_code: str = Field(description="Metric group code containing this metric.")
    description: str = Field(default="", description="Human-readable metric description.")
    cost: int | None = Field(default=None, ge=0, description="Base metric credit cost when included.")


class MetricGroup(BaseModel):
    code: str = Field(description="Stable metric group code.")
    name: str = Field(description="Human-facing group name.")
    metrics: list[MetricDefinition] = Field(description="Metrics in this group.")
    scopes: list[str] = Field(description="Scopes associated with this metric group.")
    locked: bool = Field(default=False, description="Whether this group is locked for the current plan.")


class PlanLimits(BaseModel):
    requests_per_minute: int | None = Field(default=None, ge=0)
    requests_per_day: int | None = Field(default=None, ge=0)
    daily_metric_credits: int | None = Field(default=None, ge=0)
    monthly_metric_credits: int | None = Field(default=None, ge=0)
    max_history_days: int | None = Field(default=None, ge=0)
    min_interval: str | None = None
    websocket_streams: int | None = Field(default=None, ge=0)
    child_api_keys: int | str | None = None
    delegated_passes: bool | str | int
    offline_validity_pack: bool | str
    batch_query: bool | None = None


class LockedMetricGroup(BaseModel):
    group_code: str
    required_plan: PlanCode
    reason: str = "upgrade_required"


class MetricCatalogResponse(BaseModel):
    plan: PlanCode
    available_metric_groups: list[str]
    locked_metric_groups: list[LockedMetricGroup]
    limits: PlanLimits
    daily_metric_credits: int | None
    monthly_metric_credits: int | None
    max_history_days: int | None
    min_interval: str | None
    websocket_streams: int | None
    child_api_keys: int | str | None
    delegated_passes: bool | str | int
    offline_validity_pack: bool | str
    batch_query: bool | None = None
    metric_groups: list[MetricGroup] = Field(default_factory=list)


class MetricCostEstimateRequest(BaseModel):
    metrics: list[str] = Field(min_length=1)
    history_days: int | None = Field(default=None, ge=0)
    interval: str | None = None


class MetricCostEstimateResponse(BaseModel):
    metrics: list[str]
    estimated_cost: int = Field(ge=0)
    history_days: int | None = None
    interval: str | None = None


class SubscriptionEntitlementOverlay(BaseModel):
    plan_code: PlanCode
    plan_name: str
    positioning: str
    metric_groups: list[str]
    allowed_scopes: list[str]
    limits: PlanLimits
    issuer_signature: dict[str, Any] | None = None


class SubscriptionEntitlementResponse(BaseModel):
    plan_code: PlanCode
    status: str
    valid_from: Any
    valid_until: Any
    grace_until: Any | None = None
    metric_groups: list[str]
    scopes: list[str]
    limits: dict[str, Any]
    crypto_epoch: int
    issuer_key_id: str | None = None
    created_at: Any
    locked_metric_groups: list[dict[str, Any]] = Field(default_factory=list)


class AccessPaymentIntentCreate(BaseModel):
    plan_code: PlanCode
    payment_method: str = Field(default="manual", description="Payment provider method such as manual, btcpay, or bitcoin_lightning.")
    amount_sats: int | None = Field(default=None, gt=0)
    metadata: dict[str, Any] | None = None
    return_url: str | None = None


class AccessPaymentIntentResponse(BaseModel):
    payment_intent_id: int
    status: str
    provider: str | None = None
    payment_method: str
    amount_sats: int
    plan_code: PlanCode
    checkout_url: str | None = None
    expires_at: Any | None = None
    certificate_available: bool = False


class AccessPaymentIntentStatusResponse(AccessPaymentIntentResponse):
    pass


class AccessCertificateIssueRequest(BaseModel):
    payment_intent_id: int
    device_public_key: str
    device_class: str = "unknown"
    device_key_fingerprint: str | None = None
    device_attestation: dict[str, Any] | None = None
    requested_origin: str | None = None
    subscription_period_days: int = Field(default=30, ge=1, le=3660)


class AccessCertificateIssueResponse(BaseModel):
    raw_access_pass: str | None = Field(default=None, description="Returned once at issuance only; never use as bearer auth.")
    access_certificate: dict[str, Any]
    certificate_fingerprint: str
    plan_code: PlanCode
    expires_at: Any
    save_warning: str
    subscription_entitlement: SubscriptionEntitlementResponse | None = None
    recovery_setup_recommended: bool = True


class AccessMeResponse(BaseModel):
    certificate_fingerprint: str
    plan_code: str
    entitlement_status: str
    active_scopes: list[str]
    device_status: str
    session_expires_at: Any
    access_integrity_summary: dict[str, Any]
    recovery_status_summary: dict[str, Any]


class AccessLimitsResponse(BaseModel):
    plan_code: str
    limits: dict[str, Any]
    offline_validity_status: bool | str | None = None


class AccessLockdownScope(StrEnum):
    CURRENT_PASS = "current_pass"
    CURRENT_WORKSPACE = "current_workspace"
    ALL_LINKED_DEVICES = "all_linked_devices"
    BUSINESS_WORKSPACE = "business_workspace"
    ENTERPRISE_WORKSPACE = "enterprise_workspace"


class AccessLockdownRequest(BaseModel):
    reason: str | None = None
    scope: AccessLockdownScope = AccessLockdownScope.CURRENT_PASS
    confirmation_intent_signature: str | None = None
    recovery_mode: bool = True

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def _reject_seed_material(self) -> "AccessLockdownRequest":
        payload = self.model_dump(mode="json")
        for key, value in payload.items():
            lowered_key = str(key).lower()
            lowered_value = str(value).lower()
            if any(part in lowered_key or part in lowered_value for part in ("bitcoin_seed", "wallet_seed", "seed_phrase", "private_key", "recovery_phrase", "raw_pass", "session_token")):
                raise ValueError("lockdown_secret_material_forbidden")
        return self


class AccessLockdownResponse(BaseModel):
    status: str
    lockdown_id: str
    affected_sessions: int
    affected_child_api_keys: int
    affected_delegated_passes: int
    affected_devices: int
    affected_offline_packs: int
    recovery_only: bool
    audit_event_hash: str
    created_at: Any


class AccessChallengeCreate(BaseModel):
    certificate_fingerprint: str
    origin: str
    requested_scopes: list[str] = Field(min_length=1)
    device_key_fingerprint: str | None = None


class AccessChallengeResponse(BaseModel):
    challenge_id: str
    challenge_hash: str
    challenge_payload: dict[str, Any]
    expires_at: Any
    status: str


class AccessSessionCreate(BaseModel):
    certificate_fingerprint: str
    challenge_id: str
    origin: str
    device_key_fingerprint: str
    challenge_signature: str
    client_session_public_key: str | None = None
    requested_scopes: list[str] | None = None


class AccessSessionResponse(BaseModel):
    session_token: str
    session_hash_fingerprint: str
    certificate_fingerprint: str
    device_key_fingerprint: str
    plan_code: PlanCode
    scopes: list[str]
    expires_at: Any
    policy_mode: str
    requires_request_signing: bool

class ChildApiKeyCreate(BaseModel):
    name: str
    description: str | None = None
    scopes: list[str] = Field(min_length=1)
    denied_scopes: list[str] = Field(default_factory=list)
    metric_entitlements: dict[str, Any] = Field(default_factory=dict)
    limits: dict[str, Any] = Field(default_factory=dict)
    expires_at: datetime
    requires_request_signing: bool = True
    can_delegate: bool = False

    model_config = {"extra": "forbid"}


class ChildApiKeyCreateResponse(BaseModel):
    key_id: str
    raw_child_api_key: str
    scopes: list[str]
    limits: dict[str, Any]
    expires_at: Any
    warning: str = "Store this key now. It will not be shown again."


class ChildApiKeyPublic(BaseModel):
    key_id: str
    name: str | None = None
    scopes: list[str]
    denied_scopes: list[str] = Field(default_factory=list)
    limits: dict[str, Any] = Field(default_factory=dict)
    status: str
    created_at: Any
    expires_at: Any
    last_used_at: Any | None = None
    requires_request_signing: bool = True
    can_delegate: bool = False


class DelegatedPassCreate(BaseModel):
    name: str
    delegated_to_label: str | None = None
    scopes: list[str] = Field(min_length=1)
    denied_scopes: list[str] = Field(default_factory=list)
    metric_entitlements: dict[str, Any] = Field(default_factory=dict)
    constraints: dict[str, Any] = Field(default_factory=dict)
    valid_from: datetime | None = None
    expires_at: datetime
    can_create_child_keys: bool = False
    can_delegate: bool = False

    model_config = {"extra": "forbid"}


class DelegatedPassCreateResponse(BaseModel):
    delegated_pass_id: str
    raw_delegated_pass: str
    scopes: list[str]
    constraints: dict[str, Any]
    expires_at: Any
    warning: str = "Store this delegated pass now. It will not be shown again."


class DelegatedPassPublic(BaseModel):
    delegated_pass_id: str
    name: str | None = None
    delegated_to_label: str | None = None
    scopes: list[str]
    constraints: dict[str, Any] = Field(default_factory=dict)
    status: str
    valid_from: Any
    expires_at: Any
    last_used_at: Any | None = None
    can_create_child_keys: bool = False
    can_delegate: bool = False

class RecoverySafetyWarning(BaseModel):
    message: str = Field(description="Bastion recovery safety warning; never a Bitcoin wallet seed.")


class RecoverySetupRequest(BaseModel):
    pass_lookup_hash: str
    certificate_fingerprint: str | None = None
    plan_code: PlanCode

    model_config = {"extra": "forbid"}


class RecoverySetupResponse(BaseModel):
    recovery_factor_id: str
    bastion_recovery_phrase: list[str]
    word_count: int
    warning: str
    display_once: bool = True


class RecoveryStartRequest(BaseModel):
    pass_lookup_hash: str
    declared_plan_code: PlanCode
    certificate_fingerprint: str | None = None
    new_device_key_fingerprint: str | None = None
    recovery_reason: str = "device_recovery"

    model_config = {"extra": "forbid"}


class RecoveryStartResponse(BaseModel):
    recovery_attempt_id: str
    required_factors: list[str]
    allowed_factors: list[str]
    threshold: int
    cooldown_until: Any
    safety_warnings: list[str]
    status: str


class RecoveryFactorSubmitRequest(BaseModel):
    recovery_attempt_id: str
    factor_type: str
    recovery_factor: str

    model_config = {"extra": "forbid"}


class RecoveryFactorSubmitResponse(BaseModel):
    recovery_attempt_id: str
    status: str
    verified_factors: list[str]
    threshold: int
    decision: str
    reason: str


class RecoveryStatusResponse(BaseModel):
    recovery_attempt_id: str
    status: str
    threshold: int
    verified_factor_count: int
    missing_factor_count: int
    decision: str
    reason: str
    cooldown_until: Any | None = None


class RecoveryCompleteRequest(BaseModel):
    recovery_attempt_id: str
    new_device_public_key: str | None = None
    new_device_key_fingerprint: str | None = None
    revoke_old_sessions: bool = True

    model_config = {"extra": "forbid"}


class RecoveryCompleteResponse(BaseModel):
    recovery_attempt_id: str
    status: str
    certificate_fingerprint: str | None = None
    device_key_fingerprint: str | None = None
    old_sessions_revoked: int
    safety_warnings: list[str]


class RecoveryRotateRequest(BaseModel):
    pass_lookup_hash: str
    certificate_fingerprint: str | None = None
    plan_code: PlanCode

    model_config = {"extra": "forbid"}


class RecoveryRotateResponse(RecoverySetupResponse):
    pass


class RecoveryCancelRequest(BaseModel):
    recovery_attempt_id: str

    model_config = {"extra": "forbid"}


__all__ = [
    "AccessPaymentIntentCreate",
    "AccessPaymentIntentResponse",
    "AccessPaymentIntentStatusResponse",
    "AccessCertificateIssueRequest",
    "AccessCertificateIssueResponse",
    "AccessMeResponse",
    "AccessLimitsResponse",
    "AccessLockdownRequest",
    "AccessLockdownResponse",
    "AccessLockdownScope",
    "AccessChallengeCreate",
    "AccessChallengeResponse",
    "AccessSessionCreate",
    "AccessSessionResponse",
    "EntitlementLimitsResponse",
    "EntitlementAssuranceResponse",
    "WalletSubscriptionEntitlementResponse",
    "EffectiveEntitlementResponse",
    "EntitlementUpgradeRequest",
    "EntitlementDowngradeRequest",
    "EntitlementHistoryResponse",
    "ChildApiKeyCreate",
    "ChildApiKeyCreateResponse",
    "ChildApiKeyPublic",
    "DelegatedPassCreate",
    "DelegatedPassCreateResponse",
    "DelegatedPassPublic",
    "LockedMetricGroup",
    "MetricCatalogResponse",
    "MetricCostEstimateRequest",
    "MetricCostEstimateResponse",
    "MetricDefinition",
    "MetricGroup",
    "PlanLimits",
    "SubscriptionEntitlementOverlay",
    "RecoverySafetyWarning",
    "RecoverySetupRequest",
    "RecoverySetupResponse",
    "RecoveryStartRequest",
    "RecoveryStartResponse",
    "RecoveryFactorSubmitRequest",
    "RecoveryFactorSubmitResponse",
    "RecoveryStatusResponse",
    "RecoveryCompleteRequest",
    "RecoveryCompleteResponse",
    "RecoveryRotateRequest",
    "RecoveryRotateResponse",
    "RecoveryCancelRequest",
    "SubscriptionEntitlementResponse",
]


class EntitlementLimitsResponse(BaseModel):
    requests_per_minute: int | None = None
    requests_per_day: int | None = None
    daily_metric_credits: int | None = None
    monthly_metric_credits: int | None = None
    history_days: int | None = None
    minimum_interval_seconds: int | None = None
    child_api_keys: int | None = None
    delegated_passes: int | str | None = None
    concurrent_sessions: int | None = None


class EntitlementAssuranceResponse(BaseModel):
    minimum_proof_strength: str
    high_risk_step_up_required: bool
    access_certificate_required: bool
    hardware_wallet_required: bool
    quorum_policy: dict[str, Any] | None = None
    sovereign_mode: bool = False


class WalletSubscriptionEntitlementResponse(BaseModel):
    type: str = "bastion_wallet_subscription_entitlement"
    version: int = 2
    entitlement_id_hash: str
    subject_type: str
    principal_hash: str
    parent_entitlement_hash: str | None = None
    workspace_id_hash: str | None = None
    plan_code: PlanCode
    status: str
    wallet_bound: bool
    payment_method: str
    payment_proof_hash: str | None = None
    metric_groups: list[str]
    scopes: list[str]
    limits: EntitlementLimitsResponse
    assurance: EntitlementAssuranceResponse
    valid_from: datetime
    valid_until: datetime
    grace_until: datetime | None = None
    schema_epoch: int
    policy_epoch: int
    crypto_epoch: int
    issuer_key_id: str
    issuer_signatures: list[dict[str, Any]]


class EffectiveEntitlementResponse(BaseModel):
    entitlement_id_hash: str
    subject_type: str
    principal_hash: str
    plan_code: PlanCode
    status: str
    scopes: list[str]
    metric_groups: list[str]
    limits: EntitlementLimitsResponse
    assurance: EntitlementAssuranceResponse
    requires_step_up: bool
    policy_decision: str
    reason_codes: list[str]


class EntitlementUpgradeRequest(BaseModel):
    entitlement_id_hash: str
    target_plan_code: PlanCode
    payment_proof_hash: str | None = None
    human_intent_signature_hash: str | None = None


class EntitlementDowngradeRequest(BaseModel):
    entitlement_id_hash: str
    target_plan_code: PlanCode
    effective_at: datetime | None = None


class EntitlementHistoryResponse(BaseModel):
    entitlements: list[WalletSubscriptionEntitlementResponse]
