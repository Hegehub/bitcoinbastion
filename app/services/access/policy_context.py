"""Typed context and decision objects for Bastion Access Policy Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from app.domain.access.plans import PlanCode


class PolicyActorType(str, Enum):
    BITCOIN_WALLET_PRINCIPAL = "bitcoin_wallet_principal"
    LIGHTNING_WALLET_PRINCIPAL = "lightning_wallet_principal"
    WALLET_DEVICE = "wallet_device"
    ACCESS_CERTIFICATE = "access_certificate"
    CHILD_API_KEY = "child_api_key"
    DELEGATED_PASS = "delegated_pass"
    BUSINESS_ROLE = "business_role"
    PAYREGISTER_DEVICE = "payregister_device"
    BOT = "bot"
    SERVICE_ACCOUNT = "service_account"
    RECOVERY_ACTOR = "recovery_actor"


class PolicyAuthMethod(str, Enum):
    BIP322 = "bip322"
    LEGACY_BITCOIN_MESSAGE = "legacy_bitcoin_message"
    HARDWARE_WALLET = "hardware_wallet"
    AIR_GAPPED_WALLET = "air_gapped_wallet"
    MULTI_WALLET_QUORUM = "multi_wallet_quorum"
    LNURL_AUTH = "lnurl_auth"
    ACCESS_CERTIFICATE = "access_certificate"
    DEVICE_POP = "device_pop"
    SESSION_POP = "session_pop"
    CHILD_API_KEY = "child_api_key"
    DELEGATED_PASS = "delegated_pass"
    RECOVERY_CAPSULE = "recovery_capsule"
    INTERNAL_SERVICE_IDENTITY = "internal_service_identity"


class AuthenticationAssuranceLevel(str, Enum):
    COMPATIBILITY = "compatibility"
    STANDARD = "standard"
    HIGH_ASSURANCE = "high_assurance"
    SOVEREIGN = "sovereign"


class PolicySourceChannel(str, Enum):
    API = "api"
    WEB = "web"
    REFLEX = "reflex"
    CLI = "cli"
    SDK_PYTHON = "sdk_python"
    SDK_TYPESCRIPT = "sdk_typescript"
    TELEGRAM = "telegram"
    PAYREGISTER = "payregister"
    LOCAL_MESH = "local_mesh"
    OFFLINE_PACK = "offline_pack"
    LNURL_CALLBACK = "lnurl_callback"
    INTERNAL_SERVICE = "internal_service"



@dataclass(frozen=True, slots=True)
class AccessPolicyContext:
    actor_type: PolicyActorType | str | None = None
    actor_hash: str | None = None
    principal_hash: str | None = None
    principal_type: str | None = None
    parent_actor_hash: str | None = None
    auth_methods: frozenset[PolicyAuthMethod | str] = field(default_factory=frozenset)
    primary_auth_method: PolicyAuthMethod | str | None = None
    continuity_auth_method: PolicyAuthMethod | str | None = None
    request_auth_method: PolicyAuthMethod | str | None = None
    authentication_assurance: AuthenticationAssuranceLevel | str = AuthenticationAssuranceLevel.STANDARD
    wallet_proof_freshness: str | None = None
    lnurl_auth_freshness: str | None = None
    actor_status: str = "active"
    parent_actor_status: str | None = None
    certificate_status: str | None = None
    requested_action: str | None = None
    action: str | None = None
    resource: str | None = None
    object_hash: str | None = None
    request_origin: str | None = None
    origin: str | None = None
    auth_method: PolicyAuthMethod | str | None = None
    requested_scopes: frozenset[str] = field(default_factory=frozenset)
    resource_type: str | None = None
    resource_hash: str | None = None
    policy_epoch: int = 1
    policy_hash: str = "sha256:access-policy-v1"
    source_channel: PolicySourceChannel | str = PolicySourceChannel.API
    revocation_epoch: int | None = None
    idempotency_key_hash: str | None = None
    previous_state: str | None = None
    requested_state: str | None = None
    object_version: int | None = None
    audit_required: bool = True
    network: str | None = None
    auth_domain: str | None = None
    step_up_evidence: dict[str, Any] | None = None
    quorum_evidence: dict[str, Any] | None = None
    access_certificate_fingerprint: str | None = None
    offline_validity_pack_fingerprint: str | None = None
    lnurl_operation: str | None = None
    lnurl_action: str | None = None
    lnurl_auth_action: str | None = None
    lnurl_k1_status: str | None = None
    k1_hash: str | None = None
    k1_status: str | None = None
    k1_expires_at: datetime | None = None
    k1_used_at: datetime | None = None
    linking_key_hash: str | None = None
    signature_verified: bool | None = None
    challenge_domain: str | None = None
    callback_domain: str | None = None
    domain_matches: bool | None = None
    challenge_action: str | None = None
    requested_internal_action: str | None = None
    wallet_compatibility_level: str | None = None
    lnurl_auth_domain: str | None = None
    lnurl_callback_origin: str | None = None
    lnurl_payment_status: str | None = None
    payment_request_hash: str | None = None
    payment_status: str | None = None
    invoice_hash: str | None = None
    invoice_status: str | None = None
    amount_msat: int | None = None
    expected_amount_msat: int | None = None
    metadata_hash: str | None = None
    callback_hash: str | None = None
    settlement_verified: bool | None = None
    settlement_method: str | None = None
    payment_proof_hash: str | None = None
    payer_data_present: bool = False
    payer_data_auth_verified: bool = False
    lnurl_payment_proof_hash: str | None = None
    lnurl_verify_status: str | None = None
    lnurl_withdraw_status: str | None = None
    withdraw_request_hash: str | None = None
    withdraw_status: str | None = None
    withdraw_k1_hash: str | None = None
    maximum_allowed_msat: int | None = None
    invoice_valid: bool | None = None
    payout_policy_id: str | None = None
    payout_recipient_context_hash: str | None = None
    refund_reference_hash: str | None = None
    cooldown_satisfied: bool | None = None
    quorum_satisfied: bool | None = None
    lightning_address_hash: str | None = None
    address_name_hash: str | None = None
    address_domain: str | None = None
    address_status: str | None = None
    product_code: str | None = None
    merchant_hash: str | None = None
    custom_domain_verified: bool | None = None
    payregister_store_hash: str | None = None
    payregister_terminal_hash: str | None = None
    verification_strength: str | None = None
    step_up_freshness: str | None = None
    payer_data_requested_fields: frozenset[str] = field(default_factory=frozenset)
    payer_data_received_fields: frozenset[str] = field(default_factory=frozenset)
    success_action_type: str | None = None
    comment_present: bool = False
    payregister_context: dict[str, Any] = field(default_factory=dict)
    recovery_state: str | None = None
    required_quorum: str | None = None
    requires_access_certificate_configured: bool = False
    certificate_fingerprint: str | None = None
    pass_lookup_hash: str | None = None
    plan_code: PlanCode | str | None = None
    effective_scopes: set[str] = field(default_factory=set)
    requested_scope: str | None = None
    requested_metric_group: str | None = None
    requested_metric_name: str | None = None
    requested_interval: str | None = None
    requested_history_days: int | None = None
    requested_object_type: str | None = None
    requested_object_id_hash: str | None = None
    request_risk_level: str = "low"
    session_id_hash: str | None = None
    session_status: str = "active"
    session_expires_at: datetime | None = None
    device_id: str | int | None = None
    device_status: str = "active"
    device_risk_score: int | None = None
    entitlement_status: str = "active"
    entitlement_valid_until: datetime | None = None
    entitlement_limits: dict[str, Any] = field(default_factory=dict)
    metric_entitlements: dict[str, Any] = field(default_factory=dict)
    quota_state: dict[str, Any] = field(default_factory=dict)
    revocation_state: dict[str, Any] = field(default_factory=dict)
    offline_mode: bool = False
    business_role: str | None = None
    workspace_id_hash: str | None = None
    is_critical_action: bool = False
    step_up_present: bool = False
    human_intent_verified: bool = False
    legacy_auth_context: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AccessPolicyDecision:
    decision: str
    allowed: bool
    reason_code: str
    human_reason: str
    current_plan: PlanCode | None = None
    required_plan: PlanCode | None = None
    requested_scope: str | None = None
    requested_metric_group: str | None = None
    upgrade_available: bool = False
    step_up_required: bool = False
    quota_remaining: int | None = None
    retry_after_seconds: int | None = None
    audit_required: bool = False
    lockdown_recommended: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    actor_type: PolicyActorType | str | None = None
    actor_hash: str | None = None
    auth_methods_used: tuple[str, ...] = ()
    authentication_assurance: AuthenticationAssuranceLevel | str | None = None
    requested_action: str | None = None
    action: str | None = None
    resource: str | None = None
    object_hash: str | None = None
    request_origin: str | None = None
    origin: str | None = None
    auth_method: PolicyAuthMethod | str | None = None
    requested_scopes: frozenset[str] = field(default_factory=frozenset)
    resource_type: str | None = None
    resource_hash: str | None = None
    requires_quorum: bool = False
    required_quorum: str | None = None
    required_step_up_methods: tuple[str, ...] = ()
    requires_access_certificate: bool = False
    offline_allowed: bool = False
    policy_epoch: int | None = None
    policy_hash: str | None = None
    evaluated_at: datetime | None = None
    safe_user_message: str | None = None
    internal_reason_details: dict[str, Any] = field(default_factory=dict)
