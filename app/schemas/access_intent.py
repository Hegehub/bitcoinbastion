"""Schemas for Bastion Human Intent Signature manifests."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class HumanIntentAction(StrEnum):
    CREATE_API_KEY = "create_api_key"
    INCREASE_SCOPE = "increase_scope"
    EXPORT_DATA = "export_data"
    CREATE_DELEGATED_PASS = "create_delegated_pass"
    ENABLE_PAYREGISTER_ADMIN = "enable_payregister_admin"
    TREASURY_POLICY_CHANGE = "treasury_policy_change"
    RECOVERY_CHANGE = "recovery_change"
    DEVICE_ADD = "device_add"
    LOCKDOWN_DISABLE = "lockdown_disable"
    BUSINESS_ROLE_ASSIGNMENT = "business_role_assignment"
    ENTERPRISE_POLICY_CHANGE = "enterprise_policy_change"
    SUBSCRIPTION_UPGRADE_WITH_NEW_PERMISSIONS = "subscription_upgrade_with_new_permissions"
    CREATE_OFFLINE_VALIDITY_PACK = "create_offline_validity_pack"
    ROTATE_RECOVERY_SEED = "rotate_recovery_seed"
    ROTATE_ISSUER_BOUND_DEVICE = "rotate_issuer_bound_device"
    DISABLE_STEP_UP = "disable_step_up"
    CREATE_BUSINESS_OPERATOR_PASS = "create_business_operator_pass"
    CREATE_CASHIER_SHIFT_PASS = "create_cashier_shift_pass"
    CREATE_BOT_PASS = "create_bot_pass"
    INCREASE_METRIC_QUOTA = "increase_metric_quota"
    ENABLE_ENTERPRISE_PRIVATE_POLICY = "enable_enterprise_private_policy"


class HumanIntentRiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


_HIGH_OR_CRITICAL_ACTIONS = {
    HumanIntentAction.RECOVERY_CHANGE,
    HumanIntentAction.LOCKDOWN_DISABLE,
    HumanIntentAction.TREASURY_POLICY_CHANGE,
    HumanIntentAction.ENTERPRISE_POLICY_CHANGE,
}
_EXPLICIT_CANNOT_ACCESS_ACTIONS = {
    HumanIntentAction.CREATE_API_KEY,
    HumanIntentAction.CREATE_DELEGATED_PASS,
    HumanIntentAction.CREATE_BOT_PASS,
    HumanIntentAction.CREATE_BUSINESS_OPERATOR_PASS,
    HumanIntentAction.CREATE_CASHIER_SHIFT_PASS,
}
_FORBIDDEN_TEXT_PARTS = (
    "raw_access_pass",
    "access_pass",
    "raw_pass",
    "session_token",
    "recovery_seed",
    "recovery_phrase",
    "bitcoin_seed",
    "bitcoin_private_key",
    "wallet_seed",
    "xprv",
    "private_key",
)


class HumanIntentManifest(BaseModel):
    type: Literal["bastion_human_intent"] = "bastion_human_intent"
    version: int = 1
    action: HumanIntentAction
    actor_fingerprint: str
    certificate_fingerprint: str
    session_fingerprint: str | None = None
    origin: str
    requested_scopes: list[str] = Field(default_factory=list)
    granted_scopes: list[str] = Field(default_factory=list)
    cannot_access: list[str] = Field(default_factory=list)
    target_resource_type: str | None = None
    target_resource_hash: str | None = None
    plan_code: str
    risk_level: HumanIntentRiskLevel
    created_at: datetime
    expires_at: datetime
    nonce: str
    human_summary: str
    consequences: list[str]
    policy_decision_ref: str | None = None
    request_hash: str | None = None

    @field_validator("human_summary")
    @classmethod
    def _summary_required(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("human_summary_required")
        _reject_forbidden_text(value)
        return value

    @field_validator("actor_fingerprint", "certificate_fingerprint", "session_fingerprint", "origin", "target_resource_type", "target_resource_hash", "plan_code", "nonce", "policy_decision_ref", "request_hash")
    @classmethod
    def _safe_string(cls, value: str | None) -> str | None:
        if value is not None:
            _reject_forbidden_text(value)
        return value

    @field_validator("requested_scopes", "granted_scopes", "cannot_access", "consequences")
    @classmethod
    def _safe_list(cls, value: list[str]) -> list[str]:
        for item in value:
            _reject_forbidden_text(item)
        return value

    @model_validator(mode="after")
    def _validate_manifest(self) -> "HumanIntentManifest":
        created = _aware(self.created_at)
        expires = _aware(self.expires_at)
        if expires <= created:
            raise ValueError("intent_expiry_must_follow_creation")
        if self.action in _EXPLICIT_CANNOT_ACCESS_ACTIONS and not self.cannot_access:
            raise ValueError("cannot_access_required")
        if self.action == HumanIntentAction.LOCKDOWN_DISABLE and self.risk_level != HumanIntentRiskLevel.CRITICAL:
            raise ValueError("critical_risk_required_for_lockdown_disable")
        if self.action in _HIGH_OR_CRITICAL_ACTIONS and self.risk_level not in {HumanIntentRiskLevel.HIGH, HumanIntentRiskLevel.CRITICAL}:
            raise ValueError("risk_level_too_low_for_action")
        return self


class HumanIntentCreateRequest(BaseModel):
    action: HumanIntentAction
    requested_scopes: list[str] = Field(default_factory=list)
    cannot_access: list[str] = Field(default_factory=list)
    target_resource_type: str | None = None
    target_resource_id: str | None = None
    target_resource_hash: str | None = None
    origin: str
    human_summary: str
    consequences: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def _safe_payload(self) -> "HumanIntentCreateRequest":
        _reject_forbidden_value(self.model_dump(mode="json"))
        return self


class HumanIntentResponse(BaseModel):
    intent_id: str
    manifest: HumanIntentManifest
    canonical_manifest_hash: str
    expires_at: datetime
    required_signature_alg: str = "ed25519"
    signing_instructions: str


class HumanIntentSignatureRequest(BaseModel):
    intent_id: str
    signature: str
    signature_alg: str
    device_key_fingerprint: str

    model_config = {"extra": "forbid"}


class HumanIntentVerificationResult(BaseModel):
    valid: bool
    decision: str
    reason: str | None = None
    manifest_hash: str
    verified_at: datetime | None = None


def _aware(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _reject_forbidden_text(value: str) -> None:
    lowered = value.lower()
    if any(part in lowered for part in _FORBIDDEN_TEXT_PARTS):
        raise ValueError("human_intent_secret_material_forbidden")
    if "xprv" in lowered or "bitcoin seed" in lowered or "wallet seed" in lowered:
        raise ValueError("human_intent_bitcoin_seed_forbidden")


def _reject_forbidden_value(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_forbidden_text(str(key))
            _reject_forbidden_value(item)
    elif isinstance(value, list | tuple):
        for item in value:
            _reject_forbidden_value(item)
    elif isinstance(value, str):
        _reject_forbidden_text(value)
