"""Generated strict HTTP transport models. Do not edit."""
# ruff: noqa
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, RootModel

type JsonValue = (None | bool | int | Decimal | str
    | list[JsonValue] | dict[str, JsonValue])

class ClosedEmptyObject(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

class AccessCertificateIssueRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    device_attestation: dict[str, JsonValue] | None = Field(default=None)
    device_class: str | None = Field(default=None)
    device_key_fingerprint: str | None = Field(default=None)
    device_public_key: str
    payment_intent_id: int
    requested_origin: str | None = Field(default=None)
    subscription_period_days: int | None = Field(default=None)

class AccessCertificateIssueResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    access_certificate: dict[str, JsonValue]
    certificate_fingerprint: str
    expires_at: datetime
    plan_code: PlanCode
    raw_access_pass: str | None = Field(default=None)
    recovery_setup_recommended: bool | None = Field(default=None)
    save_warning: str
    subscription_entitlement: SubscriptionEntitlementResponse | None = Field(default=None)

class AccessChallengeCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    certificate_fingerprint: str
    device_key_fingerprint: str | None = Field(default=None)
    origin: str
    requested_scopes: list[str]

class AccessChallengeResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    challenge_hash: str
    challenge_id: str
    challenge_payload: dict[str, JsonValue]
    expires_at: datetime
    status: str

class AccessIssueRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    challenge_id: str
    checkout_id: str
    idempotency_key: str
    signature: str

class AccessLimitsResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    limits: dict[str, JsonValue]
    offline_validity_status: bool | str | None = Field(default=None)
    plan_code: str

class AccessLockdownRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confirmation_intent_signature: str | None = Field(default=None)
    reason: str | None = Field(default=None)
    recovery_mode: bool | None = Field(default=None)
    scope: AccessLockdownScope | None = Field(default=None)

class AccessLockdownResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    affected_child_api_keys: int
    affected_delegated_passes: int
    affected_devices: int
    affected_offline_packs: int
    affected_sessions: int
    audit_event_hash: str
    created_at: datetime
    lockdown_id: str
    recovery_only: bool
    status: str

class AccessLockdownScope(RootModel[Literal['current_pass', 'current_workspace', 'all_linked_devices', 'business_workspace', 'enterprise_workspace']]):
    pass

class AccessMeResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    access_integrity_summary: dict[str, JsonValue]
    active_scopes: list[str]
    certificate_fingerprint: str
    device_status: str
    entitlement_status: str
    plan_code: str
    recovery_status_summary: dict[str, JsonValue]
    session_expires_at: datetime

class AccessOfferOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    amount_sats: int
    availability: OfferAvailability
    capability: str
    duration_days: int
    limitations: list[str]
    offer_id: str
    plan_code: PlanCode
    price_unit: str
    revision_id: str
    scopes: list[str]
    terms_version: str

class AccessPaymentIntentCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    amount_sats: int | None = Field(default=None)
    metadata: dict[str, JsonValue] | None = Field(default=None)
    payment_method: str | None = Field(default=None)
    plan_code: PlanCode
    return_url: str | None = Field(default=None)

class AccessPaymentIntentResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    amount_sats: int
    certificate_available: bool | None = Field(default=None)
    checkout_url: str | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)
    payment_intent_id: int
    payment_method: str
    plan_code: PlanCode
    provider: str | None = Field(default=None)
    status: str

class AccessPaymentIntentStatusResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    amount_sats: int
    certificate_available: bool | None = Field(default=None)
    checkout_url: str | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)
    payment_intent_id: int
    payment_method: str
    plan_code: PlanCode
    provider: str | None = Field(default=None)
    status: str

class AccessSessionCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    certificate_fingerprint: str
    challenge_id: str
    challenge_signature: str
    client_session_public_key: str | None = Field(default=None)
    device_key_fingerprint: str
    origin: str
    requested_scopes: list[str] | None = Field(default=None)

class AccessSessionResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    certificate_fingerprint: str
    device_key_fingerprint: str
    expires_at: datetime
    plan_code: PlanCode
    policy_mode: str
    requires_request_signing: bool
    scopes: list[str]
    session_hash_fingerprint: str
    session_token: str

class AlertSummaryOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    critical: int | None = Field(default=None)
    degraded_components: list[DegradedComponentOut] | None = Field(default=None)
    warning: int | None = Field(default=None)

class AttributionRelation(RootModel[Literal['ASSOCIATED', 'CORRELATION_CANDIDATE']]):
    pass

class AuditLogOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    action: str
    actor_user_id: int | None
    after_json: str
    before_json: str
    created_at: datetime
    id: int
    resource_id: str
    resource_type: str

class BTCMarketOverviewEnvelope(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: BTCMarketOverviewOut

class BTCMarketOverviewOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    limitations: list[str]
    observed_at: datetime | None
    pair: str
    price_usd: str | None
    provider_confidence: str | None
    provider_count: int
    source: str
    symbol: str

class BackgroundJobHealthOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    duration_ms: int | None = Field(default=None)
    failure_reason: str | None = Field(default=None)
    health_state: str | None = Field(default=None)
    job_name: str
    last_finish_at: datetime | None = Field(default=None)
    last_start_at: datetime | None = Field(default=None)
    next_scheduled_at: datetime | None = Field(default=None)
    retry_count: int | None = Field(default=None)
    success: bool | None = Field(default=None)
    worker_name: str | None = Field(default=None)

class BastionTraceRegisterAdvisoryRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    incoming_payment_id: str | None = Field(default=None)
    payer_address: str

class BastionTraceTreasuryCheckRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    destination_address: str

class BatchTraceRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    addresses: list[str]
    batch_label: str | None = Field(default=None)
    business_context: BusinessContextType | None = Field(default=None)
    policy_profile_id: str | None = Field(default=None)

class BrowserSafeMarketSourceOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    category: str
    display_name: str
    homepage_url: str | None = Field(default=None)
    limitations: list[str] | None = Field(default=None)
    observed_at: datetime | None = Field(default=None)
    source_id: str
    source_type: MarketSourceType

class BusinessContextType(RootModel[Literal['RETAIL', 'MERCHANT', 'TREASURY', 'OTC', 'DONATION', 'CONSULTING', 'UNKNOWN']]):
    pass

class ChainStateOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confirmation_depth: int
    finality_band: str
    finality_score: Decimal
    headers_height: int
    observed_block_height: int
    reorg_risk_score: Decimal
    tip_height: int

class CheckoutCreateRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    idempotency_key: str
    offer_id: str
    payment_method: str | None = Field(default=None)

class CheckoutOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    amount_sats: int
    capability: str
    checkout_id: str
    created_at: datetime
    duration_days: int
    eligibility_reason: EligibilityReason
    expires_at: datetime
    issuance_eligible: bool
    offer_id: str
    offer_revision_id: str
    payment_intent_id: int | None
    plan_code: PlanCode
    price_unit: str
    scopes: list[str]
    status: CheckoutStatus
    terms_version: str

class CheckoutStatus(RootModel[Literal['awaiting_payment', 'eligible', 'expired', 'cancelled', 'failed', 'issued']]):
    pass

class ChildApiKeyCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    can_delegate: bool | None = Field(default=None)
    denied_scopes: list[str] | None = Field(default=None)
    description: str | None = Field(default=None)
    expires_at: datetime
    limits: dict[str, JsonValue] | None = Field(default=None)
    metric_entitlements: dict[str, JsonValue] | None = Field(default=None)
    name: str
    requires_request_signing: bool | None = Field(default=None)
    scopes: list[str]

class ChildApiKeyCreateResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    expires_at: datetime
    key_id: str
    limits: dict[str, JsonValue]
    raw_child_api_key: str
    scopes: list[str]
    warning: str | None = Field(default=None)

class ChildApiKeyPublic(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    can_delegate: bool | None = Field(default=None)
    created_at: datetime
    denied_scopes: list[str] | None = Field(default=None)
    expires_at: datetime
    key_id: str
    last_used_at: datetime | None = Field(default=None)
    limits: dict[str, JsonValue] | None = Field(default=None)
    name: str | None = Field(default=None)
    requires_request_signing: bool | None = Field(default=None)
    scopes: list[str]
    status: str

class CitadelAssessmentOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confidence_penalty: Decimal | None = Field(default=None)
    created_at: datetime
    critical_findings: list[CitadelFindingOut] | None = Field(default=None)
    custody_resilience_score: Decimal
    data_sources: list[str] | None = Field(default=None)
    evidence_refs: list[str] | None = Field(default=None)
    explainability: ExplainabilityOut | None = Field(default=None)
    fee_survivability_score: Decimal
    freshness: CitadelFreshnessOut | None = Field(default=None)
    generated_at: datetime
    id: int
    inheritance_readiness_score: Decimal
    limitations: list[str] | None = Field(default=None)
    operational_hygiene_score: Decimal
    operator_warning: str | None = Field(default=None)
    overall_score: Decimal
    owner_id: int
    owner_type: str
    policy_maturity_score: Decimal
    privacy_resilience_score: Decimal
    production_replacement_path: str | None = Field(default=None)
    recommendations: list[str] | None = Field(default=None)
    recovery_readiness_score: Decimal
    source_quality: dict[str, JsonValue] | None = Field(default=None)
    synthetic_component: bool | None = Field(default=None)
    synthetic_reason: str | None = Field(default=None)
    treasury_resilience_score: Decimal
    updated_at: datetime
    vendor_independence_score: Decimal
    warnings: list[CitadelFindingOut] | None = Field(default=None)

class CitadelAssessmentRecalculateIn(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    owner_id: int
    owner_type: str | None = Field(default=None)

class CitadelDependencyGraphOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confidence: Decimal
    confidence_penalty: Decimal | None = Field(default=None)
    data_sources: list[str] | None = Field(default=None)
    edges: list[dict[str, JsonValue]] | None = Field(default=None)
    evidence_refs: list[str] | None = Field(default=None)
    explainability: ExplainabilityOut | None = Field(default=None)
    findings: list[dict[str, JsonValue]] | None = Field(default=None)
    freshness: dict[str, JsonValue] | None = Field(default=None)
    limitations: list[str] | None = Field(default=None)
    nodes: list[dict[str, JsonValue]] | None = Field(default=None)
    operator_warning: str | None = Field(default=None)
    production_replacement_path: str | None = Field(default=None)
    single_points_of_failure: list[dict[str, JsonValue]] | None = Field(default=None)
    source_quality: dict[str, JsonValue] | None = Field(default=None)
    synthetic_component: bool | None = Field(default=None)
    synthetic_reason: str | None = Field(default=None)

class CitadelFindingOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    detail: str
    domain: str
    severity: str
    title: str

class CitadelFreshnessOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    assessment_generated_at: str | None = Field(default=None)
    cache_age_seconds: int | None = Field(default=None)
    cache_source: str | None = Field(default=None)
    is_stale: bool | None = Field(default=None)
    recompute_reason: str | None = Field(default=None)
    stale_reason: str | None = Field(default=None)
    ttl_seconds: int | None = Field(default=None)

class CitadelInheritanceOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    completeness_score: Decimal
    confidence: Decimal
    confidence_penalty: Decimal | None = Field(default=None)
    critical_gaps: list[str] | None = Field(default=None)
    data_sources: list[str] | None = Field(default=None)
    evidence_refs: list[str] | None = Field(default=None)
    explainability: ExplainabilityOut | None = Field(default=None)
    freshness: dict[str, JsonValue] | None = Field(default=None)
    human_dependency_score: Decimal
    limitations: list[str] | None = Field(default=None)
    operational_readability_score: Decimal
    operator_warning: str | None = Field(default=None)
    owner_id: int
    production_replacement_path: str | None = Field(default=None)
    recommendations: list[str] | None = Field(default=None)
    source_quality: dict[str, JsonValue] | None = Field(default=None)
    status: str
    synthetic_component: bool | None = Field(default=None)
    synthetic_reason: str | None = Field(default=None)

class CitadelOverviewOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confidence: Decimal | None = Field(default=None)
    data_sources: list[str] | None = Field(default=None)
    explainability: ExplainabilityOut | None = Field(default=None)
    freshness: CitadelFreshnessOut | None = Field(default=None)
    overall_score: Decimal
    owner_id: int
    owner_type: str
    recovery_readiness_score: Decimal
    top_findings: list[str] | None = Field(default=None)

class CitadelPolicyChecksOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confidence: Decimal
    data_sources: list[str] | None = Field(default=None)
    explainability: ExplainabilityOut | None = Field(default=None)
    freshness: dict[str, JsonValue] | None = Field(default=None)
    gaps: list[str] | None = Field(default=None)
    maturity: str
    owner_id: int
    policy_maturity_score: Decimal

class CitadelRepairPlanOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confidence: Decimal
    confidence_penalty: Decimal | None = Field(default=None)
    data_sources: list[str] | None = Field(default=None)
    evidence_refs: list[str] | None = Field(default=None)
    explainability: ExplainabilityOut | None = Field(default=None)
    freshness: dict[str, JsonValue] | None = Field(default=None)
    items: list[dict[str, JsonValue]] | None = Field(default=None)
    limitations: list[str] | None = Field(default=None)
    operator_warning: str | None = Field(default=None)
    owner_id: int
    production_replacement_path: str | None = Field(default=None)
    source_quality: dict[str, JsonValue] | None = Field(default=None)
    synthetic_component: bool | None = Field(default=None)
    synthetic_reason: str | None = Field(default=None)

class CitadelSimulationIn(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    owner_id: int
    scenario_code: str

class CitadelSimulationOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    blocked_paths: list[str] | None = Field(default=None)
    confidence: Decimal
    confidence_penalty: Decimal | None = Field(default=None)
    critical_failure_points: list[str] | None = Field(default=None)
    data_sources: list[str] | None = Field(default=None)
    evidence_refs: list[str] | None = Field(default=None)
    explainability: ExplainabilityOut | None = Field(default=None)
    freshness: dict[str, JsonValue] | None = Field(default=None)
    limitations: list[str] | None = Field(default=None)
    operator_warning: str | None = Field(default=None)
    owner_id: int
    production_replacement_path: str | None = Field(default=None)
    recommended_remediations: list[str] | None = Field(default=None)
    remaining_paths: list[str] | None = Field(default=None)
    scenario_code: str
    source_quality: dict[str, JsonValue] | None = Field(default=None)
    survivability_score: Decimal
    synthetic_component: bool | None = Field(default=None)
    synthetic_reason: str | None = Field(default=None)

class DataSufficiency(RootModel[Literal['AVAILABLE', 'INSUFFICIENT']]):
    pass

class DegradedComponentOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    affected_component: str
    automatic_fallback_used: bool | None = Field(default=None)
    operator_attention_required: bool | None = Field(default=None)
    recommendation: str
    severity: str
    started_at: datetime

class DelegatedPassCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    can_create_child_keys: bool | None = Field(default=None)
    can_delegate: bool | None = Field(default=None)
    constraints: dict[str, JsonValue] | None = Field(default=None)
    delegated_to_label: str | None = Field(default=None)
    denied_scopes: list[str] | None = Field(default=None)
    expires_at: datetime
    metric_entitlements: dict[str, JsonValue] | None = Field(default=None)
    name: str
    scopes: list[str]
    valid_from: datetime | None = Field(default=None)

class DelegatedPassCreateResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    constraints: dict[str, JsonValue]
    delegated_pass_id: str
    expires_at: datetime
    raw_delegated_pass: str
    scopes: list[str]
    warning: str | None = Field(default=None)

class DelegatedPassPublic(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    can_create_child_keys: bool | None = Field(default=None)
    can_delegate: bool | None = Field(default=None)
    constraints: dict[str, JsonValue] | None = Field(default=None)
    delegated_pass_id: str
    delegated_to_label: str | None = Field(default=None)
    expires_at: datetime
    last_used_at: datetime | None = Field(default=None)
    name: str | None = Field(default=None)
    scopes: list[str]
    status: str
    valid_from: datetime

class DeliveryStatsOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    failed_24h: int
    sent_24h: int

class DependencyHealthOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    degraded_reason: str | None = Field(default=None)
    last_failure_at: datetime | None = Field(default=None)
    last_success_at: datetime | None = Field(default=None)
    latency_ms: Decimal | None = Field(default=None)
    name: str
    provider_confidence: Decimal | None = Field(default=None)
    status: str

class EducationSnippetOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    level: str
    slug: str
    summary: str
    title: str

class EligibilityReason(RootModel[Literal['payment_pending', 'payment_settled', 'checkout_expired', 'terminal_state']]):
    pass

class EnterpriseRole(RootModel[Literal['OWNER', 'ADMIN', 'ANALYST', 'REVIEWER', 'AUDITOR', 'READ_ONLY']]):
    pass

class EntityOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confidence: Decimal
    created_at: datetime
    description: str
    entity_type: str
    id: int
    label: str
    name: str
    provenance_score: Decimal
    provenance_tier: str
    source_ref_count: int
    updated_at: datetime

class EvidenceAccessRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    evidence_ref: str
    purpose: str
    requester_role: EnterpriseRole

class EvidenceEdgeOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    from_node_key: str
    relation: str
    to_node_key: str
    weight: Decimal

class EvidenceLineageCompleteness(RootModel[Literal['complete', 'partial', 'truncated', 'unavailable']]):
    pass

class EvidenceLineageEdgeDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    direction: str | None = Field(default=None)
    id: str
    relation: EvidenceLineageRelation
    source_id: str
    target_id: str

class EvidenceLineageNodeDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    captured_at: datetime | None = Field(default=None)
    id: str
    kind: EvidenceLineageNodeKind
    label: str
    limitations: list[str] | None = Field(default=None)
    producer: str | None = Field(default=None)
    producer_version: str | None = Field(default=None)

class EvidenceLineageNodeKind(RootModel[Literal['source_reference', 'evidence', 'topology_relationship', 'claim', 'graph_snapshot', 'report_capture', 'proof_packet']]):
    pass

class EvidenceLineagePathDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    edge_ids: list[str]
    node_ids: list[str]
    path_id: str

class EvidenceLineageRelation(RootModel[Literal['produced_from', 'supports', 'captured_in', 'included_in', 'referenced_by']]):
    pass

class EvidenceNodeOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    label: str
    node_key: str
    node_type: str
    weight: Decimal

class EvidenceReplayEligibility(RootModel[Literal['replayable', 'not_replayable', 'input_unavailable', 'version_unavailable', 'unsupported_legacy']]):
    pass

class EvidenceReplayStatus(RootModel[Literal['match', 'mismatch', 'not_replayable', 'input_unavailable', 'version_unavailable', 'execution_failed']]):
    pass

class EvidenceVerificationScope(RootModel[Literal['evidence_identity_integrity']]):
    pass

class EvidenceVerificationStatus(RootModel[Literal['verified', 'failed', 'not_run', 'unavailable', 'unsupported']]):
    pass

class ExplainabilityOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confidence: Decimal | None = Field(default=None)
    data_sources: list[str] | None = Field(default=None)
    explanation: str | None = Field(default=None)

class FeeRecommendationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    mempool_congestion: Decimal
    target_blocks: int

class FeeRecommendationResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confidence: Decimal
    congestion_state: str
    data_sources: list[str] | None = Field(default=None)
    explainability: ExplainabilityOut | None = Field(default=None)
    freshness: FreshnessOut | None = Field(default=None)
    high_fee_scenario_sat_vb: int
    rationale: str
    suggested_fee_rate_sat_vb: int

class FreshnessOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    computed_at: str | None = Field(default=None)
    is_stale: bool | None = Field(default=None)
    stale_reason: str | None = Field(default=None)
    ttl_seconds: int | None = Field(default=None)

class HTTPValidationError(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    detail: list[ValidationError] | None = Field(default=None)

class HealthHistoryOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    items: list[HealthSnapshotOut]
    limit: int

class HealthOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    app: str
    details: dict[str, str] | None = Field(default=None)
    status: str

class HealthSnapshotOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confidence_score: Decimal | None = Field(default=None)
    degraded_reason: str | None = Field(default=None)
    domain: str
    error_rate: Decimal | None = Field(default=None)
    failure_count: int
    health_score: Decimal | None = Field(default=None)
    is_degraded: bool
    latency_ms: int | None = Field(default=None)
    observed_at: str
    provider_key: str | None = Field(default=None)
    runtime_mode: str
    source_key: str | None = Field(default=None)
    source_type: str | None = Field(default=None)
    status: str
    success_count: int

class HumanIntentAction(RootModel[Literal['create_api_key', 'increase_scope', 'export_data', 'create_delegated_pass', 'enable_payregister_admin', 'treasury_policy_change', 'recovery_change', 'device_add', 'lockdown_disable', 'business_role_assignment', 'enterprise_policy_change', 'subscription_upgrade_with_new_permissions', 'create_offline_validity_pack', 'rotate_recovery_seed', 'rotate_issuer_bound_device', 'disable_step_up', 'create_business_operator_pass', 'create_cashier_shift_pass', 'create_bot_pass', 'increase_metric_quota', 'enable_enterprise_private_policy']]):
    pass

class HumanIntentCreateRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    action: HumanIntentAction
    cannot_access: list[str] | None = Field(default=None)
    consequences: list[str] | None = Field(default=None)
    human_summary: str
    metadata: dict[str, JsonValue] | None = Field(default=None)
    origin: str
    requested_scopes: list[str] | None = Field(default=None)
    target_resource_hash: str | None = Field(default=None)
    target_resource_id: str | None = Field(default=None)
    target_resource_type: str | None = Field(default=None)

class HumanIntentManifest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    action: HumanIntentAction
    actor_fingerprint: str
    cannot_access: list[str] | None = Field(default=None)
    certificate_fingerprint: str
    consequences: list[str]
    created_at: datetime
    expires_at: datetime
    granted_scopes: list[str] | None = Field(default=None)
    human_summary: str
    nonce: str
    origin: str
    plan_code: str
    policy_decision_ref: str | None = Field(default=None)
    request_hash: str | None = Field(default=None)
    requested_scopes: list[str] | None = Field(default=None)
    risk_level: HumanIntentRiskLevel
    session_fingerprint: str | None = Field(default=None)
    target_resource_hash: str | None = Field(default=None)
    target_resource_type: str | None = Field(default=None)
    type: Literal['bastion_human_intent'] | None = Field(default=None)
    version: int | None = Field(default=None)

class HumanIntentResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    canonical_manifest_hash: str
    expires_at: datetime
    intent_id: str
    manifest: HumanIntentManifest
    required_signature_alg: str | None = Field(default=None)
    signing_instructions: str

class HumanIntentRiskLevel(RootModel[Literal['low', 'medium', 'high', 'critical']]):
    pass

class HumanIntentSignatureRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    device_key_fingerprint: str
    intent_id: str
    signature: str
    signature_alg: str

class HumanIntentVerificationResult(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    decision: str
    manifest_hash: str
    reason: str | None = Field(default=None)
    valid: bool
    verified_at: datetime | None = Field(default=None)

class IncidentDetailOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    affected_target: str
    detector_id: str
    history: list[IncidentTransitionOut]
    incident_id: str
    kind: str
    limitations: str
    opened_at: datetime
    resolved_at: datetime | None
    severity: IncidentSeverity
    source: str
    status: IncidentStatus
    summary: str
    updated_at: datetime

class IncidentOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    affected_target: str
    detector_id: str
    incident_id: str
    kind: str
    limitations: str
    opened_at: datetime
    resolved_at: datetime | None
    severity: IncidentSeverity
    source: str
    status: IncidentStatus
    summary: str
    updated_at: datetime

class IncidentSeverity(RootModel[Literal['MAJOR', 'CRITICAL']]):
    pass

class IncidentStatus(RootModel[Literal['OPEN', 'RESOLVED']]):
    pass

class IncidentTransitionOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    observed_at: datetime
    severity: IncidentSeverity
    source: str
    status: IncidentStatus
    summary: str
    transition: IncidentTransitionType

class IncidentTransitionType(RootModel[Literal['OPENED', 'UPDATED', 'RESOLVED']]):
    pass

class IntelligenceHealthOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    degraded_state: bool
    last_failure: datetime | None = Field(default=None)
    last_success: datetime | None = Field(default=None)
    operational_limitations: list[str] | None = Field(default=None)
    provider_confidence: Decimal
    status: str

class IssuanceChallengeCreateRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    checkout_id: str
    device_public_key: str

class IssuanceChallengeOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    algorithm: str
    canonical_payload: str
    challenge_id: str
    checkout_id: str
    expires_at: datetime
    protocol_version: str

class IssuedAccessOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    capability: str
    certificate_fingerprint: str
    checkout_id: str
    device_key_fingerprint: str
    expires_at: datetime
    grant_id: str
    issued_at: datetime
    offer_revision_id: str
    scopes: list[str]
    status: str
    terms_version: str

class JobRetryRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    task_name: str

class JobRetryResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    task_id: str
    task_name: str

class JobRunOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    correlation_id: str
    error_message: str
    finished_at: datetime | None
    id: int
    started_at: datetime
    status: str
    task_name: str

class JobStatsOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    failed_24h: int
    started_24h: int

class LNURLActivationCompleteRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    activation_reference: str | None = Field(default=None)
    active_pop_session_context: dict[str, JsonValue] | None = Field(default=None)
    device_key_fingerprint: str | None = Field(default=None)
    expected_purpose: LNURLActivationPurpose

class LNURLActivationPurpose(RootModel[Literal['subscription_activation', 'subscription_renewal', 'subscription_upgrade', 'vault_setup', 'access_certificate_setup', 'payregister_receipt', 'merchant_receipt', 'business_onboarding', 'enterprise_onboarding', 'payment_receipt', 'contribution_receipt']]):
    pass

class LNURLActivationStatus(RootModel[Literal['created', 'invoice_issued', 'payment_pending', 'payment_settled', 'entitlement_pending', 'ready', 'opened', 'completed', 'expired', 'revoked', 'refunded', 'failed']]):
    pass

class LNURLActivationStatusResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    activation_id: str
    completed: bool
    entitlement_status: str | None = Field(default=None)
    expires_at: datetime
    payment_status: str
    purpose: LNURLActivationPurpose
    ready: bool
    reason_code: str | None = Field(default=None)
    receipt_reference: str | None = Field(default=None)
    safe_next_url: str | None = Field(default=None)
    status: LNURLActivationStatus

class LNURLApiAuthChallengeRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    action: LNURLAuthAction
    client_capabilities: dict[str, JsonValue] | None = Field(default=None)
    device_key_fingerprint: str | None = Field(default=None)
    intended_policy_action: str | None = Field(default=None)
    origin: str
    requested_scopes: list[str] | None = Field(default=None)
    risk_context: dict[str, JsonValue] | None = Field(default=None)

class LNURLApiAuthSessionRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    auth_attempt_id: str
    device_key_fingerprint: str
    device_public_key: str
    requested_scopes: list[str] | None = Field(default=None)
    session_public_key: str

class LNURLApiAuthStepUpRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    action: str
    cannot_access: list[str] | None = Field(default=None)
    device_key_fingerprint: str
    requested_expiry_seconds: int | None = Field(default=None)
    requested_scopes: list[str] | None = Field(default=None)
    risk_level: WalletRiskLevel | None = Field(default=None)
    target_reference: str | None = Field(default=None)

class LNURLApiPaySubscriptionRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    comment_allowed: int | None = Field(default=None)
    duration_days: int | None = Field(default=None)
    payerdata_auth_requested: bool | None = Field(default=None)
    plan_code: str
    success_action_requested: bool | None = Field(default=None)

class LNURLApiWithdrawRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    amount_msat: int
    description: str
    network: str | None = Field(default=None)
    purpose: str
    source_reference: str | None = Field(default=None)
    step_up_id: str | None = Field(default=None)

class LNURLAuthAction(RootModel[Literal['register', 'login', 'link', 'auth']]):
    pass

class LNURLErrorResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    reason: str
    status: str | None = Field(default=None)

class LNURLPayDiscoveryResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    callback: str
    commentAllowed: int | None = Field(default=None)
    maxSendable: int
    metadata: str
    minSendable: int
    payerData: dict[str, JsonValue] | None = Field(default=None)
    tag: str | None = Field(default=None)

class MarketAttributionOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    attribution_id: int
    confidence_ratio: Decimal
    evidence_links: list[MarketEvidenceLink] | None = Field(default=None)
    explanation: str
    factor_event_id: int | None
    limitations: list[str]
    relation: AttributionRelation
    subject_candle_id: int

class MarketEvidenceLink(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    evidence_id: int
    label: str
    linked_at: datetime
    relation: MarketEvidenceRelation
    verification_status: Literal['NOT_REQUESTED', 'INTEGRITY_RECORD_AVAILABLE']

class MarketEvidenceRelation(RootModel[Literal['RELATED_EVIDENCE', 'SOURCE_MATERIAL']]):
    pass

class MarketNarrativeOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    body_plain_text: str
    confidence_ratio: Decimal
    generated_at: datetime
    limitations: list[str]
    narrative_id: int
    origin: NarrativeOrigin
    slug: str
    title: str

class MarketReplayCaptureOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    capture_id: UUID
    captured_at: datetime
    effective_at: datetime
    event: MarketTimelineEventOut
    historical: Literal[True] | None = Field(default=None)
    integrity: ReplayIntegrityOut
    limitations: list[str] | None = Field(default=None)
    schema_version: Literal['market-replay.capture.v1'] | None = Field(default=None)

class MarketSimilarityMatchOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    candidate_event_id: int
    candidate_occurred_at: datetime
    candidate_title: str
    dimensions: list[SimilarityDimensionOut]
    limitations: list[str]
    method: SimilarityMethod | None = Field(default=None)
    method_version: Literal['historical-event-similarity.v1'] | None = Field(default=None)
    rank: int
    reference_event_id: int
    replay_event_id: int
    result_id: int
    score_meaning: Literal['HIGHER_IS_MORE_SIMILAR_NOT_PREDICTIVE'] | None = Field(default=None)
    score_ratio: Decimal

class MarketSimilarityReportOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    generated_at: datetime
    interpretation: Literal['RETROSPECTIVE_COMPARISON_NOT_FORECAST'] | None = Field(default=None)
    method: SimilarityMethod | None = Field(default=None)
    method_version: Literal['historical-event-similarity.v1'] | None = Field(default=None)
    provenance: Literal['LIVE'] | None = Field(default=None)
    reference_event_id: int
    results: list[MarketSimilarityMatchOut]
    uncertainty: SimilarityUncertaintyOut

class MarketSourceRef(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    display_name: str
    source_id: str
    source_type: MarketSourceType

class MarketSourceType(RootModel[Literal['INTERNAL', 'NEWS', 'SIGNAL', 'PROVIDER', 'MARKET_DATA', 'UNKNOWN']]):
    pass

class MarketTimeMachineAnalyticsResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    generated_at: datetime
    items: list[dict[str, JsonValue]] | None = Field(default=None)
    limit: int
    limitations: list[str] | None = Field(default=None)
    runtime_mode: MarketTimeMachineRuntimeMode
    runtime_ms: Decimal | None = Field(default=None)
    source_store: MarketTimeMachineSourceStore
    warnings: list[str] | None = Field(default=None)
    window: MarketTimeMachineQueryWindow

class MarketTimeMachineQueryWindow(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    from_ts: datetime
    to_ts: datetime

class MarketTimeMachineRuntimeMode(RootModel[Literal['live', 'degraded', 'disabled', 'unavailable']]):
    pass

class MarketTimeMachineSourceStore(RootModel[Literal['clickhouse', 'postgres_fallback', 'none']]):
    pass

class MarketTimelineEventOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    event_id: int
    evidence_links: list[MarketEvidenceLink] | None = Field(default=None)
    kind: TimelineKind
    limitations: list[str] | None = Field(default=None)
    observed_at: datetime
    occurred_at: datetime
    producer_type: str
    related_candle_id: int | None = Field(default=None)
    related_signal_id: int | None = Field(default=None)
    sequence: int
    source: MarketSourceRef
    summary: str
    title: str

class MarketTimelinePageOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    items: list[MarketTimelineEventOut]
    limit: int
    next_before_sequence: int | None = Field(default=None)
    ordering: Literal['occurred_at_desc,event_id_desc'] | None = Field(default=None)

class MerchantLightningAddressCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    comment_allowed: int | None = Field(default=None)
    description: str | None = Field(default=None)
    display_label: str | None = Field(default=None)
    domain_id: str
    local_part: str
    max_sendable_msat: int | None = Field(default=None)
    min_sendable_msat: int | None = Field(default=None)
    settlement_mode: Literal['merchant_node', 'payregister_node', 'btcpay', 'bastion_proxy', 'external_provider'] | None = Field(default=None)
    target_id_hash: str
    target_type: Literal['workspace', 'store', 'terminal', 'cashier_shift', 'campaign', 'donation', 'subscription', 'custom']
    workspace_id_hash: str

class MerchantLightningDomainCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    normalized_domain: str
    verification_method: Literal['dns_txt', 'http_well_known', 'bastion_managed'] | None = Field(default=None)
    workspace_id_hash: str

class MetricUsageSummaryOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    allowed: int
    cached: int
    degraded: int
    degraded_mode: bool | None = Field(default=None)
    denied: int
    event_count: int
    skipped: int
    top_metric_groups: list[dict[str, JsonValue]] | None = Field(default=None)
    total_credits: int
    total_requests: int
    window: str

class MetricsStatusOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    bounded_labels: list[str] | None = Field(default=None)
    endpoint: str | None = Field(default=None)
    prometheus_enabled: bool | None = Field(default=None)
    registered_metrics: list[str] | None = Field(default=None)

class NarrativeOrigin(RootModel[Literal['STORED_BACKEND_RECORD']]):
    pass

class NewsArticleOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    btc_relevance_score: Decimal
    confidence_score: Decimal
    id: int
    impact_score: Decimal
    summary: str
    title: str
    urgency_score: Decimal
    url: str

class OfferAvailability(RootModel[Literal['active', 'inactive']]):
    pass

class OnchainChainStateOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confidence_score: Decimal
    confirmation_depth: int
    explainability: dict[str, JsonValue]
    finality_band: str
    finality_score: Decimal
    freshness: dict[str, JsonValue]
    headers_height: int
    observed_block_height: int
    reorg_risk_score: Decimal
    tip_height: int

class OnchainEventOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    address: str
    block_height: int
    confidence_score: Decimal
    event_type: str
    id: int
    observed_at: datetime
    significance_score: Decimal
    txid: str
    value_sats: int

class OperationalEvidencePacketOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confidence: Decimal | None = Field(default=None)
    degraded_dependencies: list[str] | None = Field(default=None)
    delivery_health: dict[str, JsonValue] | None = Field(default=None)
    drill_status: dict[str, JsonValue] | None = Field(default=None)
    evidence_refs: list[str] | None = Field(default=None)
    explainability: dict[str, JsonValue] | None = Field(default=None)
    packet_type: str
    provider_quality: dict[str, JsonValue] | None = Field(default=None)
    recovery_slo_status: str | None = Field(default=None)
    runtime_state: str
    unresolved_critical_findings: int | None = Field(default=None)

class OperationalHealthOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    backup_verified: bool | None = Field(default=None)
    degraded_state_visible: bool | None = Field(default=None)
    evidence_status: str
    integrity_verified: bool | None = Field(default=None)
    last_backup: datetime | None = Field(default=None)
    last_integrity_scan: datetime | None = Field(default=None)
    last_restore_test: datetime | None = Field(default=None)
    operational_limitations: list[str] | None = Field(default=None)
    operator_visible: bool | None = Field(default=None)
    provider_status: list[OperationalProviderStatusOut] | None = Field(default=None)
    readiness_status: str
    restore_verified: bool | None = Field(default=None)
    scheduler_status: str
    signal_queue_status: str
    system_status: str
    timeline_status: str

class OperationalProviderStatusOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    backoff_until: datetime | None = Field(default=None)
    failure_count: int | None = Field(default=None)
    last_error_sanitized: str | None = Field(default=None)
    last_failure_at: datetime | None = Field(default=None)
    last_success_at: datetime | None = Field(default=None)
    latency_ms: Decimal | None = Field(default=None)
    provider_confidence: Decimal | None = Field(default=None)
    provider_name: str
    provider_type: str
    status: str

class OperationsDrillOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    artifact_refs: list[str] | None = Field(default=None)
    drill_id: str
    drill_type: str
    finished_at: datetime | None = Field(default=None)
    notes: str | None = Field(default=None)
    operator: str | None = Field(default=None)
    started_at: datetime
    success: bool | None = Field(default=None)

class OperationsHealthOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    degraded_state: bool
    dependencies: list[DependencyHealthOut]
    last_failure: datetime | None = Field(default=None)
    last_success: datetime | None = Field(default=None)
    operational_limitations: list[str] | None = Field(default=None)
    status: str

class OperationsMetricsSummaryOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    api_availability_status: str | None = Field(default=None)
    background_job_success_status: str | None = Field(default=None)
    degraded_state: bool | None = Field(default=None)
    evidence_generation_latency_status: str | None = Field(default=None)
    operational_limitations: list[str] | None = Field(default=None)
    provider_availability_status: str | None = Field(default=None)
    replay_latency_status: str | None = Field(default=None)
    signal_generation_latency_status: str | None = Field(default=None)

class OperationsRunbookOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    failure_modes: list[str] | None = Field(default=None)
    path: str
    slug: str
    title: str

class OperationsSLOOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    comparison: SLOComparison
    current: str | None
    error_budget_consumed: str | None = Field(default=None)
    error_budget_remaining: str | None = Field(default=None)
    indicator_id: str
    limitations: str
    observed_at: datetime
    sample_count: int
    service: str
    slo_id: str
    source: str
    status: SLOStatus
    target: str
    title: str
    unit: SLOUnit
    window_seconds: int

class OperationsSnapshotOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    chain_state: ChainStateOut
    degraded_mode: RuntimeDegradedModeOut
    deliveries: DeliveryStatsOut
    jobs: JobStatsOut
    operational_evidence: OperationalEvidencePacketOut
    providers: list[ProviderHealthOut]
    queue_depth: int
    recovery_slo: RecoverySLOOut
    runtime_severity: RuntimeSeverityOut
    stale_jobs: int

class OperationsStatusOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    alert_summary: AlertSummaryOut
    dependency_status: list[DependencyHealthOut]
    operational_limitations: list[str] | None = Field(default=None)
    operations_timeline: list[OperationsDrillOut] | None = Field(default=None)
    platform_status: RuntimeStatusOut
    provider_status: list[ProviderHealthSnapshotOut]
    recovery_drills: list[OperationsDrillOut] | None = Field(default=None)
    system_health: str

class OperatorActionRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confidence_override: Decimal | None = Field(default=None)
    decision_reason: str | None = Field(default=None)
    operator_note: str | None = Field(default=None)
    publish_override: bool | None = Field(default=None)
    reviewer_id: int | None = Field(default=None)

class PaginatedDataEntityOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    items: list[EntityOut]
    limit: int
    offset: int
    total: int

class PaginatedDataNewsArticleOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    items: list[NewsArticleOut]
    limit: int
    offset: int
    total: int

class PaginatedDataOnchainEventOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    items: list[OnchainEventOut]
    limit: int
    offset: int
    total: int

class PaginatedDataSignalOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    items: list[SignalOut]
    limit: int
    offset: int
    total: int

class PaginatedDataTreasuryRequestOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    items: list[TreasuryRequestOut]
    limit: int
    offset: int
    total: int

class PaginatedDataUserOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    items: list[UserOut]
    limit: int
    offset: int
    total: int

class PaginatedDataWalletHealthReportOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    items: list[WalletHealthReportOut]
    limit: int
    offset: int
    total: int

class PaginatedDataWalletProfileOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    items: list[WalletProfileOut]
    limit: int
    offset: int
    total: int

class PaginatedDataWatchedEntityOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    items: list[WatchedEntityOut]
    limit: int
    offset: int
    total: int

class PayRegisterLNURLCheckoutCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    amount_msat: int | None = Field(default=None)
    context_version: int | None = Field(default=None)
    description: str
    order_reference: str | None = Field(default=None)
    ttl_seconds: int | None = Field(default=None)

class PayRegisterLNURLStaticEndpointCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    comment_allowed: int | None = Field(default=None)
    display_label: str | None = Field(default=None)
    endpoint_mode: Literal['terminal_checkout', 'store_open_amount', 'fixed_product', 'checkout_rotating']
    max_sendable_msat: int | None = Field(default=None)
    merchant_description: str | None = Field(default=None)
    merchant_workspace_hash: str
    min_sendable_msat: int | None = Field(default=None)
    public_alias: str
    store_hash: str
    terminal_hash: str | None = Field(default=None)

class PayRegisterLNURLStaticEndpointUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    display_label: str | None = Field(default=None)
    merchant_description: str | None = Field(default=None)

class PaymentContextRiskRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    address: str
    amount_sats: int | None = Field(default=None)
    business_context: str | None = Field(default=None)
    counterparty_label: str | None = Field(default=None)
    direction: PaymentDirection | None = Field(default=None)
    known_relationship: bool | None = Field(default=None)
    operator_role: str | None = Field(default=None)
    payment_purpose: str | None = Field(default=None)
    urgency: str | None = Field(default=None)

class PaymentDirection(RootModel[Literal['SEND', 'RECEIVE', 'UNKNOWN']]):
    pass

class PlanCode(RootModel[Literal['lite_pass', 'basic_pass', 'plus_pass', 'pro_pass', 'business_pass', 'enterprise_pass']]):
    pass

class PluginDryRunRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    payload: dict[str, JsonValue] | None = Field(default=None)

class PolicyCatalogCompareOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    baseline_policy_name: str
    candidate_policy_name: str
    changed_rules: list[str]
    changed_thresholds: list[str]
    confidence: Decimal | None = Field(default=None)
    data_sources: list[str] | None = Field(default=None)
    explainability: ExplainabilityOut | None = Field(default=None)
    freshness: FreshnessOut | None = Field(default=None)
    risk_level: Literal['low', 'medium', 'high']

class PolicyCatalogCompareRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    baseline_policy_name: str
    candidate_policy_name: str

class PolicyCatalogOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    max_single_tx_sats: int
    min_wallet_health_score: int
    name: str

class PolicyCatalogUpsertIn(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    change_justification: str | None = Field(default=None)
    description: str | None = Field(default=None)
    governance_ticket: str | None = Field(default=None)
    max_single_tx_sats: int
    min_wallet_health_score: int
    name: str
    required_peer_review_approvals: int | None = Field(default=None)
    rules: list[PolicyRuleUpsertIn] | None = Field(default=None)

class PolicyCheckRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    policy_name: str
    required_approvals: int | None = Field(default=None)
    transaction_amount_sats: int
    wallet_health_score: Decimal

class PolicyCheckResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    allowed: bool
    applied_rules: list[PolicyRuleOut]
    confidence: Decimal | None = Field(default=None)
    data_sources: list[str] | None = Field(default=None)
    evaluated_policy: str
    explainability: ExplainabilityOut | None = Field(default=None)
    freshness: FreshnessOut | None = Field(default=None)
    next_actions: list[str]
    violations: list[str]

class PolicyExecutionLogOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    allowed: bool
    executed_at: datetime
    id: int
    next_actions: list[str]
    policy_name: str
    transaction_amount_sats: int
    violations: list[str]
    wallet_health_score: int

class PolicyExecutionPolicyBreakdownOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    allowed: int
    blocked: int
    policy_name: str
    total: int

class PolicyExecutionSummaryOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    allow_rate: Decimal
    allowed: int
    blocked: int
    by_policy: list[PolicyExecutionPolicyBreakdownOut]
    total: int

class PolicyRuleOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    rule_key: str
    rule_value: str
    severity: str

class PolicyRuleUpsertIn(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    comparator: Literal['gte', 'lte', 'eq']
    rule_key: Literal['min_wallet_health_score', 'max_single_tx_sats', 'min_required_approvals']
    severity: Literal['warning', 'error'] | None = Field(default=None)
    threshold: int

class PolicySimulationDiffOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    added_violations: list[str]
    baseline_allowed: bool
    candidate_allowed: bool
    changed: bool
    changed_rules: list[str]
    governance_actions: list[str]
    removed_violations: list[str]
    required_approvals_suggested: int
    risk_level: Literal['low', 'medium', 'high']

class PolicySimulationOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    baseline: PolicyCheckResponse
    candidate: PolicyCheckResponse
    confidence: Decimal | None = Field(default=None)
    data_sources: list[str] | None = Field(default=None)
    diff: PolicySimulationDiffOut
    explainability: ExplainabilityOut | None = Field(default=None)
    freshness: FreshnessOut | None = Field(default=None)

class PolicySimulationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    baseline_policy_name: str
    candidate_policy_name: str
    required_approvals: int | None = Field(default=None)
    transaction_amount_sats: int
    wallet_health_score: Decimal

class PrivacyAssessmentRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    known_kyc_exposure: bool | None = Field(default=None)
    merged_clusters_count: int | None = Field(default=None)
    reused_addresses: int | None = Field(default=None)
    utxo_fragmentation_score: Decimal | None = Field(default=None)

class PrivacyAssessmentResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    explainability: dict[str, Decimal | str]
    priority_action: str
    recommendations: list[str]
    risk_level: str
    risk_score: Decimal

class ProvenanceEntityDeltaOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    drift: Decimal
    entity_id: int
    name: str
    new_confidence: Decimal
    old_confidence: Decimal

class ProvenanceRefreshOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    deltas: list[ProvenanceEntityDeltaOut] | None = Field(default=None)
    drifted: int
    scanned: int
    updated: int

class ProviderHealthOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confidence: Decimal | None = Field(default=None)
    degradation_reason: str | None = Field(default=None)
    details: str
    freshness_seconds: int | None = Field(default=None)
    healthy: bool
    is_fallback: bool | None = Field(default=None)
    is_mock: bool | None = Field(default=None)
    operator_guidance: list[str] | None = Field(default=None)
    provider: str
    provider_name: str | None = Field(default=None)
    stale_evidence: bool | None = Field(default=None)

class ProviderHealthSnapshotOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    avg_latency_ms: Decimal | None = Field(default=None)
    backoff_until: datetime | None = Field(default=None)
    consecutive_failures: int | None = Field(default=None)
    failure_count: int | None = Field(default=None)
    health_state: str | None = Field(default=None)
    last_failure_at: datetime | None = Field(default=None)
    last_success_at: datetime | None = Field(default=None)
    provider_confidence: Decimal | None = Field(default=None)
    provider_name: str
    provider_type: str

class PublicFeatureAvailability(RootModel[Literal['PUBLIC', 'PRO', 'BUSINESS', 'ENTERPRISE', 'INTERNAL']]):
    pass

class PublicFeatureEntry(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    availability: PublicFeatureAvailability
    category: str
    id: str
    limitations: list[str] | None = Field(default=None)
    name: str
    safety_notes: list[str] | None = Field(default=None)
    status: PublicFeatureStatus
    summary: str

class PublicFeatureStatus(RootModel[Literal['IMPLEMENTED', 'BASELINE', 'PLACEHOLDER', 'PLANNED', 'NOT_IMPLEMENTED']]):
    pass

class PublicLandingResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    feature_catalog: list[PublicFeatureEntry]
    links: dict[str, str]
    modules: list[str]
    platform_name: str
    platform_tagline: str
    production_readiness: dict[str, JsonValue]
    roadmap_summary: dict[str, JsonValue]
    safety_principles: list[str]
    status_summary: dict[str, JsonValue]

class PublicRoadmapResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    baseline: list[str] | None = Field(default=None)
    current_phase: str
    implemented: list[str] | None = Field(default=None)
    not_started: list[str] | None = Field(default=None)
    placeholder: list[str] | None = Field(default=None)
    planned: list[str] | None = Field(default=None)

class PublicStatsResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    limitations: list[str] | None = Field(default=None)
    proof_packets_generated: int
    reports_generated: int
    runtime_events: int
    supported_modules: list[str]
    watchtower_entries: int

class PublicStatusResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    known_limitations: list[str] | None = Field(default=None)
    last_update: datetime
    modules: dict[str, str]
    platform_status: str
    production_calibrated: bool
    trace_status: str

class PublicTraceSummary(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    band: str
    confidence_summary: str
    created_at: datetime | None = Field(default=None)
    limitations: list[str] | None = Field(default=None)
    manual_review_recommended: bool
    origin_summary: str
    privacy_summary: str
    report_id: int
    risk_summary: str
    safety_warnings: list[str] | None = Field(default=None)
    top_reasons: list[str] | None = Field(default=None)

class RecommendationItemOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    action: str
    action_confidence: Decimal | None = Field(default=None)
    evidence_paths: list[str] | None = Field(default=None)
    evidence_refs: list[str] | None = Field(default=None)
    horizon: str
    policy_refs: list[str] | None = Field(default=None)
    priority: str
    rationale: str

class RecoveryCancelRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    recovery_attempt_id: str

class RecoveryCheckOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    drill_execution: dict[str, JsonValue] | None = Field(default=None)
    drills: list[RecoveryDrillOut]
    failed_deliveries_24h: int
    failed_jobs_24h: int
    hotspots: list[RecoveryHotspotOut]
    issues: list[RecoveryIssueOut]
    ok: bool
    recommended_actions: list[str]
    recovery_slo: dict[str, JsonValue] | None = Field(default=None)
    severity: Literal['ok', 'warning', 'critical']

class RecoveryCompleteRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    new_device_key_fingerprint: str | None = Field(default=None)
    new_device_public_key: str | None = Field(default=None)
    recovery_attempt_id: str
    revoke_old_sessions: bool | None = Field(default=None)

class RecoveryCompleteResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    certificate_fingerprint: str | None = Field(default=None)
    device_key_fingerprint: str | None = Field(default=None)
    old_sessions_revoked: int
    recovery_attempt_id: str
    safety_warnings: list[str]
    status: str

class RecoveryDrillOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    automation_ready: bool
    drill_code: str
    priority: Literal['low', 'medium', 'high']
    run_within_hours: int
    target_reference: str
    title: str

class RecoveryFactorSubmitRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    factor_type: str
    recovery_attempt_id: str
    recovery_factor: str

class RecoveryFactorSubmitResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    decision: str
    reason: str
    recovery_attempt_id: str
    status: str
    threshold: int
    verified_factors: list[str]

class RecoveryHotspotOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    failures_24h: int
    issue_type: str
    reference: str

class RecoveryIssueOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    detail: str
    issue_type: str
    occurred_at: datetime | None
    reference: str

class RecoveryReadinessOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    artifact_summary: dict[str, JsonValue] | None = Field(default=None)
    confidence: Decimal
    confidence_penalty: Decimal | None = Field(default=None)
    data_sources: list[str] | None = Field(default=None)
    evidence_refs: list[str] | None = Field(default=None)
    explainability: ExplainabilityOut | None = Field(default=None)
    freshness: dict[str, JsonValue] | None = Field(default=None)
    human_dependency_score: Decimal
    limitations: list[str] | None = Field(default=None)
    operator_warning: str | None = Field(default=None)
    production_replacement_path: str | None = Field(default=None)
    recoverability_assumption: str
    recovery_readiness_score: Decimal
    source_quality: dict[str, JsonValue] | None = Field(default=None)
    synthetic_component: bool | None = Field(default=None)
    synthetic_reason: str | None = Field(default=None)
    warnings: list[str] | None = Field(default=None)

class RecoveryRotateRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    certificate_fingerprint: str | None = Field(default=None)
    pass_lookup_hash: str
    plan_code: PlanCode

class RecoveryRotateResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    bastion_recovery_phrase: list[str]
    display_once: bool | None = Field(default=None)
    recovery_factor_id: str
    warning: str
    word_count: int

class RecoverySLOOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    actual: dict[str, JsonValue] | None = Field(default=None)
    explainability: dict[str, JsonValue] | None = Field(default=None)
    signals: dict[str, JsonValue] | None = Field(default=None)
    status: str
    target: dict[str, JsonValue] | None = Field(default=None)

class RecoverySetupRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    certificate_fingerprint: str | None = Field(default=None)
    pass_lookup_hash: str
    plan_code: PlanCode

class RecoverySetupResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    bastion_recovery_phrase: list[str]
    display_once: bool | None = Field(default=None)
    recovery_factor_id: str
    warning: str
    word_count: int

class RecoveryStartRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    certificate_fingerprint: str | None = Field(default=None)
    declared_plan_code: PlanCode
    new_device_key_fingerprint: str | None = Field(default=None)
    pass_lookup_hash: str
    recovery_reason: str | None = Field(default=None)

class RecoveryStartResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    allowed_factors: list[str]
    cooldown_until: datetime
    recovery_attempt_id: str
    required_factors: list[str]
    safety_warnings: list[str]
    status: str
    threshold: int

class RecoveryStatusResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    cooldown_until: datetime | None = Field(default=None)
    decision: str
    missing_factor_count: int
    reason: str
    recovery_attempt_id: str
    status: str
    threshold: int
    verified_factor_count: int

class ReplayIntegrityOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    algorithm: Literal['sha256'] | None = Field(default=None)
    content_digest: str
    meaning: Literal['CONTENT_EQUALITY_ONLY'] | None = Field(default=None)

class ResponseEnvelopeCitadelAssessmentOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: CitadelAssessmentOut
    success: bool | None = Field(default=None)

class ResponseEnvelopeCitadelDependencyGraphOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: CitadelDependencyGraphOut
    success: bool | None = Field(default=None)

class ResponseEnvelopeCitadelInheritanceOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: CitadelInheritanceOut
    success: bool | None = Field(default=None)

class ResponseEnvelopeCitadelOverviewOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: CitadelOverviewOut
    success: bool | None = Field(default=None)

class ResponseEnvelopeCitadelPolicyChecksOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: CitadelPolicyChecksOut
    success: bool | None = Field(default=None)

class ResponseEnvelopeCitadelRepairPlanOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: CitadelRepairPlanOut
    success: bool | None = Field(default=None)

class ResponseEnvelopeCitadelSimulationOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: CitadelSimulationOut
    success: bool | None = Field(default=None)

class ResponseEnvelopeFeeRecommendationResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: FeeRecommendationResponse
    success: bool | None = Field(default=None)

class ResponseEnvelopeJobRetryResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: JobRetryResponse
    success: bool | None = Field(default=None)

class ResponseEnvelopeOnchainChainStateOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: OnchainChainStateOut
    success: bool | None = Field(default=None)

class ResponseEnvelopeOperationsSnapshotOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: OperationsSnapshotOut
    success: bool | None = Field(default=None)

class ResponseEnvelopePaginatedDataEntityOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: PaginatedDataEntityOut
    success: bool | None = Field(default=None)

class ResponseEnvelopePaginatedDataNewsArticleOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: PaginatedDataNewsArticleOut
    success: bool | None = Field(default=None)

class ResponseEnvelopePaginatedDataOnchainEventOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: PaginatedDataOnchainEventOut
    success: bool | None = Field(default=None)

class ResponseEnvelopePaginatedDataSignalOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: PaginatedDataSignalOut
    success: bool | None = Field(default=None)

class ResponseEnvelopePaginatedDataTreasuryRequestOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: PaginatedDataTreasuryRequestOut
    success: bool | None = Field(default=None)

class ResponseEnvelopePaginatedDataUserOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: PaginatedDataUserOut
    success: bool | None = Field(default=None)

class ResponseEnvelopePaginatedDataWalletHealthReportOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: PaginatedDataWalletHealthReportOut
    success: bool | None = Field(default=None)

class ResponseEnvelopePaginatedDataWalletProfileOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: PaginatedDataWalletProfileOut
    success: bool | None = Field(default=None)

class ResponseEnvelopePaginatedDataWatchedEntityOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: PaginatedDataWatchedEntityOut
    success: bool | None = Field(default=None)

class ResponseEnvelopePolicyCatalogCompareOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: PolicyCatalogCompareOut
    success: bool | None = Field(default=None)

class ResponseEnvelopePolicyCatalogOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: PolicyCatalogOut
    success: bool | None = Field(default=None)

class ResponseEnvelopePolicyCheckResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: PolicyCheckResponse
    success: bool | None = Field(default=None)

class ResponseEnvelopePolicyExecutionSummaryOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: PolicyExecutionSummaryOut
    success: bool | None = Field(default=None)

class ResponseEnvelopePolicySimulationOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: PolicySimulationOut
    success: bool | None = Field(default=None)

class ResponseEnvelopePrivacyAssessmentResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: PrivacyAssessmentResponse
    success: bool | None = Field(default=None)

class ResponseEnvelopeProvenanceRefreshOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: ProvenanceRefreshOut
    success: bool | None = Field(default=None)

class ResponseEnvelopePublicLandingResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: PublicLandingResponse
    success: bool | None = Field(default=None)

class ResponseEnvelopePublicRoadmapResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: PublicRoadmapResponse
    success: bool | None = Field(default=None)

class ResponseEnvelopePublicStatsResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: PublicStatsResponse
    success: bool | None = Field(default=None)

class ResponseEnvelopePublicStatusResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: PublicStatusResponse
    success: bool | None = Field(default=None)

class ResponseEnvelopePublicTraceSummary(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: PublicTraceSummary
    success: bool | None = Field(default=None)

class ResponseEnvelopeRecoveryCheckOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: RecoveryCheckOut
    success: bool | None = Field(default=None)

class ResponseEnvelopeRecoveryReadinessOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: RecoveryReadinessOut
    success: bool | None = Field(default=None)

class ResponseEnvelopeSafeEvidenceExportDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: SafeEvidenceExportDTO
    success: bool | None = Field(default=None)

class ResponseEnvelopeSafeEvidenceLineageDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: SafeEvidenceLineageDTO
    success: bool | None = Field(default=None)

class ResponseEnvelopeSafeEvidenceReplayDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: SafeEvidenceReplayDTO
    success: bool | None = Field(default=None)

class ResponseEnvelopeSafeEvidenceVerificationDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: SafeEvidenceVerificationDTO
    success: bool | None = Field(default=None)

class ResponseEnvelopeSafeTraceDisagreementCollectionDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: SafeTraceDisagreementCollectionDTO
    success: bool | None = Field(default=None)

class ResponseEnvelopeSafeTraceProofPacketDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: SafeTraceProofPacketDTO
    success: bool | None = Field(default=None)

class ResponseEnvelopeSignalExplanationOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: SignalExplanationOut
    success: bool | None = Field(default=None)

class ResponseEnvelopeSignalRecommendationOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: SignalRecommendationOut
    success: bool | None = Field(default=None)

class ResponseEnvelopeTraceGraphDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: TraceGraphDTO
    success: bool | None = Field(default=None)

class ResponseEnvelopeTraceGraphHistoryDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: TraceGraphHistoryDTO
    success: bool | None = Field(default=None)

class ResponseEnvelopeTraceGraphMetadataDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: TraceGraphMetadataDTO
    success: bool | None = Field(default=None)

class ResponseEnvelopeTraceGraphObjectDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: TraceGraphObjectDTO
    success: bool | None = Field(default=None)

class ResponseEnvelopeTraceGraphRelationshipDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: TraceGraphRelationshipDTO
    success: bool | None = Field(default=None)

class ResponseEnvelopeTraceGraphSnapshotDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: TraceGraphSnapshotDTO
    success: bool | None = Field(default=None)

class ResponseEnvelopeTraceReport(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: TraceReport
    success: bool | None = Field(default=None)

class ResponseEnvelopeTraceSourceStatus(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: TraceSourceStatus
    success: bool | None = Field(default=None)

class ResponseEnvelopeTraceSubmissionResult(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: TraceSubmissionResult
    success: bool | None = Field(default=None)

class ResponseEnvelopeTraceWatchlistEntry(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: TraceWatchlistEntry
    success: bool | None = Field(default=None)

class ResponseEnvelopeTreasuryApprovalOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: TreasuryApprovalOut
    success: bool | None = Field(default=None)

class ResponseEnvelopeTreasuryRejectOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: TreasuryRejectOut
    success: bool | None = Field(default=None)

class ResponseEnvelopeTreasuryRequestOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: TreasuryRequestOut
    success: bool | None = Field(default=None)

class ResponseEnvelopeUserOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: UserOut
    success: bool | None = Field(default=None)

class ResponseEnvelopeWalletHealthReportOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: WalletHealthReportOut
    success: bool | None = Field(default=None)

class ResponseEnvelopeWalletHealthResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: WalletHealthResponse
    success: bool | None = Field(default=None)

class ResponseEnvelopeDictStrAny(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: dict[str, JsonValue]
    success: bool | None = Field(default=None)

class ResponseEnvelopeDictStrObject(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: dict[str, JsonValue]
    success: bool | None = Field(default=None)

class ResponseEnvelopeDictStrStr(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: dict[str, str]
    success: bool | None = Field(default=None)

class ResponseEnvelopeListAuditLogOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: list[AuditLogOut]
    success: bool | None = Field(default=None)

class ResponseEnvelopeListCitadelSimulationOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: list[CitadelSimulationOut]
    success: bool | None = Field(default=None)

class ResponseEnvelopeListEducationSnippetOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: list[EducationSnippetOut]
    success: bool | None = Field(default=None)

class ResponseEnvelopeListJobRunOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: list[JobRunOut]
    success: bool | None = Field(default=None)

class ResponseEnvelopeListPolicyCatalogOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: list[PolicyCatalogOut]
    success: bool | None = Field(default=None)

class ResponseEnvelopeListPolicyExecutionLogOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: list[PolicyExecutionLogOut]
    success: bool | None = Field(default=None)

class ResponseEnvelopeListPublicFeatureEntry(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: list[PublicFeatureEntry]
    success: bool | None = Field(default=None)

class ResponseEnvelopeListSourceReputationProfileOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: list[SourceReputationProfileOut]
    success: bool | None = Field(default=None)

class ResponseEnvelopeListTraceEvidence(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: list[TraceEvidence]
    success: bool | None = Field(default=None)

class ResponseEnvelopeListTraceSourceStatus(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: list[TraceSourceStatus]
    success: bool | None = Field(default=None)

class ResponseEnvelopeListTraceWatchlistEntry(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: list[TraceWatchlistEntry]
    success: bool | None = Field(default=None)

class ResponseEnvelopeListDictStrObject(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: list[dict[str, JsonValue]]
    success: bool | None = Field(default=None)

class ResponseEnvelopeListStr(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    data: list[str]
    success: bool | None = Field(default=None)

class RuntimeDegradedModeOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    active: bool
    component_states: dict[str, str] | None = Field(default=None)
    confidence_penalty: Decimal | None = Field(default=None)
    explainability: dict[str, JsonValue] | None = Field(default=None)
    reasons: list[str] | None = Field(default=None)

class RuntimeSeverityOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    dimensions: dict[str, str] | None = Field(default=None)
    escalation_conditions: list[str] | None = Field(default=None)
    escalation_required: bool
    explainability: dict[str, JsonValue] | None = Field(default=None)
    level: str
    operator_guidance: list[str] | None = Field(default=None)
    score: int

class RuntimeStatusOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    degraded_components: list[DegradedComponentOut] | None = Field(default=None)
    evidence_pipeline_state: str
    fallback_active: bool | None = Field(default=None)
    job_health: list[BackgroundJobHealthOut] | None = Field(default=None)
    job_state: str
    last_success: datetime | None = Field(default=None)
    operator_attention_required: bool | None = Field(default=None)
    provider_health: list[ProviderHealthSnapshotOut] | None = Field(default=None)
    provider_state: str
    queue_depth: int | None = Field(default=None)
    signal_pipeline_state: str
    system_state: str
    telegram_health: TelegramHealthOut | None = Field(default=None)
    telegram_state: str

class SLOComparison(RootModel[Literal['AT_LEAST', 'AT_MOST']]):
    pass

class SLOStatus(RootModel[Literal['WITHIN_TARGET', 'BREACHED', 'INSUFFICIENT_DATA', 'UNAVAILABLE']]):
    pass

class SLOUnit(RootModel[Literal['ratio']]):
    pass

class SafeBitcoinNetworkClaimValueDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    kind: Literal['bitcoin_network']
    network: str

class SafeEvidenceExportDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    content: str
    content_digest: str
    evidence_id: str
    export_id: str
    filename: str
    graph_snapshot_id: str
    integrity_status: str
    limitations: list[str] | None = Field(default=None)
    media_type: str
    proof_packet_id: str
    schema_version: str

class SafeEvidenceLineageDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    completeness: EvidenceLineageCompleteness
    edges: list[EvidenceLineageEdgeDTO]
    evidence: SafeTraceEvidenceDTO
    graph_snapshot_id: str
    historical: bool
    limitations: list[str] | None = Field(default=None)
    nodes: list[EvidenceLineageNodeDTO]
    paths: list[EvidenceLineagePathDTO]
    proof_packet_id: str

class SafeEvidenceReplayDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    comparison_scope: str
    eligibility: EvidenceReplayEligibility
    evidence_id: str
    graph_snapshot_id: str
    immutable_input_ids: list[str]
    limitations: list[str] | None = Field(default=None)
    method_id: str
    method_version: str
    original_identity: str
    replay_id: str
    replayed_at: datetime
    reproduced_identity: str | None
    status: EvidenceReplayStatus

class SafeEvidenceVerificationDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    evidence_id: str
    graph_snapshot_id: str
    limitations: list[str] | None = Field(default=None)
    proposition: str
    scope: EvidenceVerificationScope
    status: EvidenceVerificationStatus
    verification_id: str
    verified_at: datetime
    verifier_id: str
    verifier_version: str

class SafeRiskBandClaimValueDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    band: str
    kind: Literal['risk_band']

class SafeTraceClaimDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confidence: Decimal | None
    evaluated_at: datetime
    id: str
    limitations: list[str]
    predicate: str
    producer: str
    producer_version: str
    provenance: SafeTraceClaimProvenanceDTO
    source: str
    subject: SafeTraceClaimSubjectDTO
    value: SafeRiskBandClaimValueDTO | SafeBitcoinNetworkClaimValueDTO

class SafeTraceClaimProvenanceDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    input_references: list[str]
    limitations: list[str]

class SafeTraceClaimSubjectDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    kind: str
    object_id: str
    public_value: str

class SafeTraceDisagreementCollectionDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    evaluations: list[SafeTraceDisagreementDTO]
    graph_snapshot_id: str

class SafeTraceDisagreementCoverageDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    eligible_claim_count: int
    eligible_producer_count: int
    failed_producer_count: int
    insufficient_producer_count: int
    unavailable_producer_count: int

class SafeTraceDisagreementDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    claims: list[SafeTraceClaimDTO]
    coverage: SafeTraceDisagreementCoverageDTO
    evaluation_id: str
    evaluator_version: str
    graph_snapshot_id: str
    limitations: list[str]
    predicate: str | None
    resolution_status: str
    status: str
    subject: SafeTraceClaimSubjectDTO | None

class SafeTraceEvidenceDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    captured_at: datetime
    evidence_id: str
    integrity_status: TraceEvidenceIntegrityStatus
    kind: TraceEvidenceKind
    limitations: list[str] | None = Field(default=None)
    linked_claim_ids: list[str] | None = Field(default=None)
    linked_relationship_ids: list[str] | None = Field(default=None)
    producer: str
    reference: str
    source_category: str
    verification_status: TraceEvidenceVerificationStatus

class SafeTraceProofPacketDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    advisory_only: bool | None = Field(default=None)
    assembler_version: str
    captured_at: datetime
    claim_capture_id: str
    claims: list[SafeTraceClaimDTO]
    disagreements: list[SafeTraceDisagreementDTO]
    evidence: list[SafeTraceEvidenceDTO]
    graph_snapshot_id: str
    historical: bool
    integrity_status: TraceEvidenceIntegrityStatus
    limitations: list[str] | None = Field(default=None)
    not_bitcoin_consensus_proof: bool | None = Field(default=None)
    not_legal_verification: bool | None = Field(default=None)
    packet_digest: str
    packet_id: str
    packet_schema_version: str
    subject: str
    topology: TraceProofPacketTopologyReferenceDTO
    trace_id: int
    verification_status: TraceEvidenceVerificationStatus

class SignalExplanationOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confidence_reasoning: str
    data_sources: list[str] | None = Field(default=None)
    edges: list[EvidenceEdgeOut]
    explanation_text: str
    generated_at: datetime
    horizon: str
    nodes: list[EvidenceNodeOut]
    signal_id: int

class SignalOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confidence: Decimal
    created_at: datetime
    explainability: ExplainabilityOut | None = Field(default=None)
    freshness: FreshnessOut | None = Field(default=None)
    horizons: dict[str, Decimal | str] | None = Field(default=None)
    id: int
    is_published: bool
    score: Decimal
    severity: str
    signal_type: str
    summary: str
    title: str

class SignalRecommendationOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    generated_by: str
    recommendations: list[RecommendationItemOut]
    signal_id: int

class SimilarityDimensionOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    dimension: Literal['PATTERN', 'SENTIMENT', 'IMPACT', 'VOLATILITY']
    score_ratio: Decimal

class SimilarityIntervalSubject(RootModel[Literal['HISTORICAL_CANDIDATE_SIMILARITY_SCORE_DISTRIBUTION']]):
    pass

class SimilarityIntervalType(RootModel[Literal['EMPIRICAL_QUANTILE_INTERVAL']]):
    pass

class SimilarityMethod(RootModel[Literal['WEIGHTED_EVENT_CONTEXT_V1']]):
    pass

class SimilarityStatisticalIntervalOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    cohort: Literal['ELIGIBLE_PERSISTED_MATCHES_BOUNDED_500_AT_REQUEST_BOUNDARY']
    interval_type: SimilarityIntervalType
    limitations: list[str]
    lower: Decimal
    lower_quantile: Decimal
    method_id: Literal['EMPIRICAL_SIMILARITY_SCORE_QUANTILES']
    method_version: Literal['empirical-similarity-quantiles.v1']
    sample_count: int
    subject: SimilarityIntervalSubject
    unit: Literal['SIMILARITY_RATIO'] | None = Field(default=None)
    upper: Decimal
    upper_quantile: Decimal

class SimilarityUncertaintyOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confidence_ratio: Decimal | None = Field(default=None)
    coverage_dimension_count: int
    interval: SimilarityStatisticalIntervalOut | None = Field(default=None)
    limitations: list[str] | None = Field(default=None)
    sample_count: int
    sufficiency: DataSufficiency

class SourceReputationProfileOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    consistency_score: Decimal
    reliability_score: Decimal
    sample_size: int
    signal_quality_score: Decimal
    source_id: int
    updated_at: datetime

class StorageDegradedMode(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    active: bool
    impact: list[str] | None = Field(default=None)
    reason: str | None = Field(default=None)

class StorageRole(RootModel[Literal['required', 'optional', 'future', 'local_only']]):
    pass

class StorageStatusResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    degraded_mode: StorageDegradedMode
    profile: str
    status: StorageStatusValue
    stores: dict[str, StorageStoreStatus]
    summary: StorageStatusSummary

class StorageStatusSummary(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    critical_failures: int
    optional_degraded: bool
    required_ok: bool
    warnings: int

class StorageStatusValue(RootModel[Literal['ok', 'disabled', 'degraded', 'unavailable', 'misconfigured', 'not_configured', 'not_implemented', 'unknown']]):
    pass

class StorageStoreStatus(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    details: dict[str, JsonValue] | None = Field(default=None)
    latency_ms: Decimal | None = Field(default=None)
    purpose: str
    role: StorageRole
    status: StorageStatusValue

class SubscriptionEntitlementResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    created_at: datetime
    crypto_epoch: int
    grace_until: datetime | None = Field(default=None)
    issuer_key_id: str | None = Field(default=None)
    limits: dict[str, JsonValue]
    locked_metric_groups: list[dict[str, JsonValue]] | None = Field(default=None)
    metric_groups: list[str]
    plan_code: PlanCode
    scopes: list[str]
    status: str
    valid_from: datetime
    valid_until: datetime

class SystemHealthOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    degraded_components: list[DegradedComponentOut]
    job_health: list[BackgroundJobHealthOut]
    last_success: datetime | None = Field(default=None)
    provider_health: list[ProviderHealthSnapshotOut]
    queue_depth: int | None = Field(default=None)
    recovery_events: list[dict[str, JsonValue]] | None = Field(default=None)
    runtime_status: RuntimeStatusOut
    system_health: str

class TelegramHealthOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    average_delivery_latency: Decimal | None = Field(default=None)
    delivery_failures: int | None = Field(default=None)
    health_state: str | None = Field(default=None)
    last_publish_failure: datetime | None = Field(default=None)
    last_publish_success: datetime | None = Field(default=None)
    pending_queue_size: int | None = Field(default=None)

class TimelineKind(RootModel[Literal['NEWS', 'SIGNAL', 'MARKET', 'NARRATIVE', 'PROVIDER', 'OTHER']]):
    pass

class TraceBand(RootModel[Literal['LOW', 'MEDIUM', 'HIGH', 'CRITICAL', 'UNKNOWN']]):
    pass

class TraceConfidenceLedgerEntry(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    delta: Decimal
    factor: str
    reason: str

class TraceDNA(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    evidence_strength: Decimal
    false_positive_risk: Decimal
    freshness_decay: Decimal
    origin_uncertainty: Decimal
    privacy_exposure: Decimal
    provider_disagreement: Decimal
    risk: Decimal
    sovereignty: Decimal

class TraceEvidence(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confidence: Decimal
    created_at: datetime
    description: str
    evidence_ref: str
    evidence_type: str
    freshness_days: int
    id: int
    limitations: list[str] | None = Field(default=None)
    report_id: int
    source_name: str
    source_type: str

class TraceEvidenceIntegrityStatus(RootModel[Literal['not_checked', 'content_integrity_checked']]):
    pass

class TraceEvidenceKind(RootModel[Literal['topology_relationship_support', 'claim_input_reference', 'report_evidence_reference']]):
    pass

class TraceEvidenceVerificationStatus(RootModel[Literal['not_verified', 'verification_unavailable']]):
    pass

class TraceFactorContribution(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    contribution: Decimal
    direction: str
    factor: str
    reason: str
    value: Decimal
    weight: Decimal

class TraceFreshness(RootModel[Literal['FRESH', 'RECENT', 'STALE', 'UNKNOWN']]):
    pass

class TraceGraphApiVersion(RootModel[Literal['trace-graph-api-v1']]):
    pass

class TraceGraphDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    metadata: TraceGraphMetadataDTO
    objects: list[TraceGraphObjectDTO]
    observations: list[TraceGraphObservationDTO]
    relationships: list[TraceGraphRelationshipDTO]
    snapshot: TraceGraphSnapshotDTO

class TraceGraphError(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    code: TraceGraphErrorCode
    message: str

class TraceGraphErrorCode(RootModel[Literal['GRAPH_NOT_FOUND', 'GRAPH_VALIDATION_FAILED']]):
    pass

class TraceGraphEvidenceReferenceDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    reference: str
    source_name: str
    source_type: str

class TraceGraphHistoryDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    entries: list[TraceGraphHistoryEntryDTO]
    graph_id: str

class TraceGraphHistoryEntryDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    analysis_version: str
    api_version: TraceGraphApiVersion
    builder_version: str
    created_at: datetime
    graph_id: str
    graph_version: str
    limitations: list[str] | None = Field(default=None)
    provenance_summary: list[str] | None = Field(default=None)
    schema_version: str
    snapshot_id: str
    snapshot_version: TraceSnapshotVersion
    topology_snapshot_id: str | None = Field(default=None)
    topology_source_status: TraceTopologySourceStatus

class TraceGraphMetadataDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    analysis_version: str
    api_version: TraceGraphApiVersion
    builder_version: str
    chain: str
    created_at: datetime
    graph_hash: str
    graph_id: str
    graph_version: str
    limitations: list[str] | None = Field(default=None)
    schema_version: str
    snapshot_version: TraceSnapshotVersion
    topology_engine_version: str | None = Field(default=None)
    topology_network: str | None = Field(default=None)
    topology_snapshot_id: str | None = Field(default=None)
    topology_source_status: TraceTopologySourceStatus
    topology_version: str | None = Field(default=None)

class TraceGraphObjectDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    id: str
    kind: str
    label: str
    limitations: list[str] | None = Field(default=None)
    provenance: TraceGraphProvenanceDTO

class TraceGraphObservationDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    id: str
    kind: str
    limitations: list[str] | None = Field(default=None)
    provenance: TraceGraphProvenanceDTO
    subject: str
    value: str

class TraceGraphProvenanceDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    evidence: list[TraceGraphEvidenceReferenceDTO] | None = Field(default=None)
    limitations: list[str] | None = Field(default=None)
    observations: list[str] | None = Field(default=None)
    producer: str
    source_relationship_id: str | None = Field(default=None)
    stage: str
    topology_snapshot_id: str | None = Field(default=None)

class TraceGraphRelationshipDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confidence: Decimal | None = Field(default=None)
    direction: str
    id: str
    limitations: list[str] | None = Field(default=None)
    originating_observation_id: str
    provenance: TraceGraphProvenanceDTO
    relationship_type: str
    source_id: str
    target_id: str

class TraceGraphSnapshotDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    graph_id: str
    metadata: TraceGraphMetadataDTO
    object_ids: list[str]
    observation_ids: list[str]
    relationship_ids: list[str]
    report_fact_ids: list[str]
    snapshot_id: str
    topology_snapshot_id: str | None = Field(default=None)

class TraceProofPacketTopologyReferenceDTO(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    graph_snapshot_id: str
    node_ids: list[str]
    relationship_ids: list[str]
    topology_snapshot_id: str | None

class TraceReport(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    address: str
    advisory_not_legal_verdict: bool | None = Field(default=None)
    chain: str | None = Field(default=None)
    confidence: Decimal | None = Field(default=None)
    confidence_ledger: list[TraceConfidenceLedgerEntry] | None = Field(default=None)
    created_at: datetime | None = Field(default=None)
    evidence_refs: list[str] | None = Field(default=None)
    factor_contributions: list[TraceFactorContribution] | None = Field(default=None)
    freshness: TraceFreshness | None = Field(default=None)
    id: int | None = Field(default=None)
    limitations: list[str] | None = Field(default=None)
    no_custody: bool | None = Field(default=None)
    not_consensus_proof: bool | None = Field(default=None)
    operator_guidance: list[str] | None = Field(default=None)
    reason_codes: list[str] | None = Field(default=None)
    score_breakdown: TraceScoreBreakdown | None = Field(default=None)
    source_quality: TraceSourceQuality | None = Field(default=None)
    status: str | None = Field(default=None)
    summary: str | None = Field(default=None)
    trace_band: TraceBand | None = Field(default=None)
    trace_dna: TraceDNA | None = Field(default=None)
    trace_score: Decimal | None = Field(default=None)

class TraceScoreBreakdown(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    band: TraceBand
    base_score: Decimal
    confidence: Decimal
    confidence_ledger: list[TraceConfidenceLedgerEntry] | None = Field(default=None)
    factor_contributions: list[TraceFactorContribution] | None = Field(default=None)
    final_score: Decimal
    freshness: TraceFreshness
    limitations: list[str] | None = Field(default=None)
    operator_guidance: list[str] | None = Field(default=None)
    reason_codes: list[str] | None = Field(default=None)
    source_quality: TraceSourceQuality
    trace_dna: TraceDNA

class TraceSnapshotVersion(RootModel[Literal['trace-snapshot-v1']]):
    pass

class TraceSourceQuality(RootModel[Literal['HIGH', 'MEDIUM', 'LOW', 'MIXED', 'UNKNOWN']]):
    pass

class TraceSourceStatus(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confidence: Decimal | None = Field(default=None)
    enabled: bool
    freshness: str | None = Field(default=None)
    id: int
    is_external: bool | None = Field(default=None)
    is_internal: bool | None = Field(default=None)
    is_node_backed: bool | None = Field(default=None)
    is_synthetic: bool | None = Field(default=None)
    last_refresh_status: str | None = Field(default=None)
    last_refreshed_at: datetime | None = Field(default=None)
    limitations: list[str] | None = Field(default=None)
    source_name: str
    source_type: str
    trust_level: str

class TraceSubjectType(RootModel[Literal['BITCOIN_ADDRESS']]):
    pass

class TraceSubmissionResult(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    idempotency_replayed: bool | None = Field(default=None)
    network: str | None = Field(default=None)
    normalized_subject: str
    report_id: int
    status: str | None = Field(default=None)
    trace_id: int

class TraceSubmitRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    network: str | None = Field(default=None)
    subject: str
    subject_type: TraceSubjectType

class TraceTopologySourceStatus(RootModel[Literal['authoritative', 'topology_source_unavailable']]):
    pass

class TraceWatchlistCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    address: str
    label: str | None = Field(default=None)
    reason: str | None = Field(default=None)
    risk_hint: str | None = Field(default=None)

class TraceWatchlistEntry(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    active: bool
    address: str
    created_at: datetime
    id: int
    label: str
    reason: str
    risk_hint: str

class TreasuryApprovalActionIn(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    note: str | None = Field(default=None)
    policy_name: str | None = Field(default=None)
    wallet_health_score: Decimal | None = Field(default=None)

class TreasuryApprovalOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    allowed_by_policy: bool
    approved_count: int
    request_id: int
    required_approvals: int
    status: str
    violations: list[str]

class TreasuryRejectActionIn(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    note: str | None = Field(default=None)

class TreasuryRejectOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    note: str
    request_id: int
    status: str

class TreasuryRequestIn(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    amount_sats: int
    destination_reference: str
    policy_name: str | None = Field(default=None)
    title: str
    wallet_health_score: Decimal | None = Field(default=None)

class TreasuryRequestOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    amount_sats: int
    approved_count: int | None = Field(default=None)
    created_at: datetime
    id: int
    policy_allowed: bool | None = Field(default=None)
    policy_violations: list[str] | None = Field(default=None)
    required_approvals: int | None = Field(default=None)
    status: str
    title: str

class UserOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    email: str
    id: int
    is_active: bool
    role: str
    username: str

class ValidationError(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    ctx: ClosedEmptyObject | None = Field(default=None)
    input: JsonValue | None = Field(default=None)
    loc: list[str | int]
    msg: str
    type: str

class WalletApiChallengeRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    action: str
    device_key_fingerprint: str
    intent_context: dict[str, JsonValue] | None = Field(default=None)
    network: WalletNetwork
    origin: str
    proof_type: WalletProofType | None = Field(default=None)
    requested_scopes: list[str] | None = Field(default=None)

class WalletApiChallengeResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    canonical_intent: str
    challenge_id: str
    expires_at: datetime
    intent_hash: str
    intent_type: str | None = Field(default=None)
    intent_version: int | None = Field(default=None)
    network: str
    proof_type: str
    safety_warning: str

class WalletApiLockdownRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    reason_code: str
    recovery_reference: str | None = Field(default=None)
    step_up_id: str | None = Field(default=None)

class WalletApiLoginResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    authentication_grant: str
    expires_at: datetime
    next_action: str | None = Field(default=None)

class WalletApiRecoveryCompleteRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    idempotency_key: str | None = Field(default=None)
    new_device_public_key: str
    revoke_compromised_devices: bool | None = Field(default=None)

class WalletApiRecoveryFactorRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    factor_type: str
    idempotency_key: str | None = Field(default=None)
    proof: dict[str, JsonValue]

class WalletApiRecoveryStartRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    new_device_public_key: str
    principal_reference: str
    recovery_profile: str
    requested_action: str

class WalletApiRegistrationResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    authentication_grant: str | None = Field(default=None)
    device: dict[str, JsonValue]
    next_action: str | None = Field(default=None)
    principal: dict[str, JsonValue]

class WalletApiSessionRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    authentication_grant: str
    device_public_key: str
    requested_scopes: list[str] | None = Field(default=None)
    session_public_key: str

class WalletApiStepUpRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    action: str
    challenge_id: str
    intent_hash: str
    proof_type: WalletProofType
    signature: str
    wallet_identifier: str

class WalletDeviceClass(RootModel[Literal['desktop_vault', 'mobile_vault', 'cli_vault', 'browser_extension', 'hardware_wallet', 'lightning_wallet', 'payregister_device', 'access_card', 'server_bot', 'unknown']]):
    pass

class WalletHealthReportOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confidence: Decimal | None = Field(default=None)
    data_sources: list[str] | None = Field(default=None)
    explainability: ExplainabilityOut | None = Field(default=None)
    fee_exposure_score: Decimal
    freshness: FreshnessOut | None = Field(default=None)
    generated_at: datetime
    health_score: Decimal
    id: int
    privacy_score: Decimal
    recommendations: list[str]
    utxo_fragmentation_score: Decimal
    wallet_profile_id: int

class WalletHealthRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    avg_fee_rate_sat_vb: Decimal
    has_backup_reference: bool | None = Field(default=None)
    has_descriptor: bool | None = Field(default=None)
    has_recovery_instructions: bool | None = Field(default=None)
    largest_utxo_share: Decimal
    script_hint: str | None = Field(default=None)
    utxo_count: int
    utxo_values_sats: list[int] | None = Field(default=None)

class WalletHealthResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confidence: Decimal | None = Field(default=None)
    explainability: ExplainabilityOut | None = Field(default=None)
    fee_exposure_score: Decimal
    freshness: FreshnessOut | None = Field(default=None)
    health_score: Decimal
    privacy_score: Decimal
    recommendations: list[str]
    utxo_fragmentation_score: Decimal

class WalletLoginRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    challenge_id: str
    device_key_fingerprint: str
    network: WalletNetwork | None = Field(default=None)
    origin: str
    proof_type: WalletProofType
    public_key: str | None = Field(default=None)
    signature: str
    wallet_identifier: str | None = Field(default=None)

class WalletNetwork(RootModel[Literal['bitcoin-mainnet', 'bitcoin-testnet', 'bitcoin-signet', 'bitcoin-regtest']]):
    pass

class WalletProfileOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    created_at: datetime
    id: int
    name: str
    wallet_type: str
    watch_only: bool

class WalletProofType(RootModel[Literal['bip322', 'legacy_message_signature', 'hardware_wallet', 'air_gapped', 'multisig_quorum', 'lnurl_auth', 'access_certificate_bridge']]):
    pass

class WalletRegisterRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    challenge_id: str
    device_class: WalletDeviceClass
    device_key_fingerprint: str
    hardware_wallet_claim: dict[str, JsonValue] | None = Field(default=None)
    network: WalletNetwork | None = Field(default=None)
    origin: str
    proof_type: WalletProofType
    public_key: str | None = Field(default=None)
    signature: str
    wallet_identifier: str | None = Field(default=None)
    wallet_name: str | None = Field(default=None)

class WalletRiskLevel(RootModel[Literal['low', 'medium', 'high', 'critical']]):
    pass

class WatchedEntityOut(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    address: str
    created_at: datetime
    entity_type: str
    id: int
    is_active: bool
    label: str
    name: str
    updated_at: datetime
    watch_type: str

class WebhookEndpointCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    description: str | None = Field(default=None)
    event_types: list[str]
    metadata: dict[str, JsonValue] | None = Field(default=None)
    name: str
    target_url: str

class WebhookEndpointUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    description: str | None = Field(default=None)
    enabled: bool | None = Field(default=None)
    event_types: list[str] | None = Field(default=None)
    metadata: dict[str, JsonValue] | None = Field(default=None)
    name: str | None = Field(default=None)
    target_url: str | None = Field(default=None)

class WebhookSubscriptionCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    event_type: str

class WebhookTestRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    event_type: str | None = Field(default=None)
    payload: dict[str, JsonValue] | None = Field(default=None)

AccessCertificateIssueRequest.model_rebuild()
AccessCertificateIssueResponse.model_rebuild()
AccessChallengeCreate.model_rebuild()
AccessChallengeResponse.model_rebuild()
AccessIssueRequest.model_rebuild()
AccessLimitsResponse.model_rebuild()
AccessLockdownRequest.model_rebuild()
AccessLockdownResponse.model_rebuild()
AccessLockdownScope.model_rebuild()
AccessMeResponse.model_rebuild()
AccessOfferOut.model_rebuild()
AccessPaymentIntentCreate.model_rebuild()
AccessPaymentIntentResponse.model_rebuild()
AccessPaymentIntentStatusResponse.model_rebuild()
AccessSessionCreate.model_rebuild()
AccessSessionResponse.model_rebuild()
AlertSummaryOut.model_rebuild()
AttributionRelation.model_rebuild()
AuditLogOut.model_rebuild()
BTCMarketOverviewEnvelope.model_rebuild()
BTCMarketOverviewOut.model_rebuild()
BackgroundJobHealthOut.model_rebuild()
BastionTraceRegisterAdvisoryRequest.model_rebuild()
BastionTraceTreasuryCheckRequest.model_rebuild()
BatchTraceRequest.model_rebuild()
BrowserSafeMarketSourceOut.model_rebuild()
BusinessContextType.model_rebuild()
ChainStateOut.model_rebuild()
CheckoutCreateRequest.model_rebuild()
CheckoutOut.model_rebuild()
CheckoutStatus.model_rebuild()
ChildApiKeyCreate.model_rebuild()
ChildApiKeyCreateResponse.model_rebuild()
ChildApiKeyPublic.model_rebuild()
CitadelAssessmentOut.model_rebuild()
CitadelAssessmentRecalculateIn.model_rebuild()
CitadelDependencyGraphOut.model_rebuild()
CitadelFindingOut.model_rebuild()
CitadelFreshnessOut.model_rebuild()
CitadelInheritanceOut.model_rebuild()
CitadelOverviewOut.model_rebuild()
CitadelPolicyChecksOut.model_rebuild()
CitadelRepairPlanOut.model_rebuild()
CitadelSimulationIn.model_rebuild()
CitadelSimulationOut.model_rebuild()
DataSufficiency.model_rebuild()
DegradedComponentOut.model_rebuild()
DelegatedPassCreate.model_rebuild()
DelegatedPassCreateResponse.model_rebuild()
DelegatedPassPublic.model_rebuild()
DeliveryStatsOut.model_rebuild()
DependencyHealthOut.model_rebuild()
EducationSnippetOut.model_rebuild()
EligibilityReason.model_rebuild()
EnterpriseRole.model_rebuild()
EntityOut.model_rebuild()
EvidenceAccessRequest.model_rebuild()
EvidenceEdgeOut.model_rebuild()
EvidenceLineageCompleteness.model_rebuild()
EvidenceLineageEdgeDTO.model_rebuild()
EvidenceLineageNodeDTO.model_rebuild()
EvidenceLineageNodeKind.model_rebuild()
EvidenceLineagePathDTO.model_rebuild()
EvidenceLineageRelation.model_rebuild()
EvidenceNodeOut.model_rebuild()
EvidenceReplayEligibility.model_rebuild()
EvidenceReplayStatus.model_rebuild()
EvidenceVerificationScope.model_rebuild()
EvidenceVerificationStatus.model_rebuild()
ExplainabilityOut.model_rebuild()
FeeRecommendationRequest.model_rebuild()
FeeRecommendationResponse.model_rebuild()
FreshnessOut.model_rebuild()
HTTPValidationError.model_rebuild()
HealthHistoryOut.model_rebuild()
HealthOut.model_rebuild()
HealthSnapshotOut.model_rebuild()
HumanIntentAction.model_rebuild()
HumanIntentCreateRequest.model_rebuild()
HumanIntentManifest.model_rebuild()
HumanIntentResponse.model_rebuild()
HumanIntentRiskLevel.model_rebuild()
HumanIntentSignatureRequest.model_rebuild()
HumanIntentVerificationResult.model_rebuild()
IncidentDetailOut.model_rebuild()
IncidentOut.model_rebuild()
IncidentSeverity.model_rebuild()
IncidentStatus.model_rebuild()
IncidentTransitionOut.model_rebuild()
IncidentTransitionType.model_rebuild()
IntelligenceHealthOut.model_rebuild()
IssuanceChallengeCreateRequest.model_rebuild()
IssuanceChallengeOut.model_rebuild()
IssuedAccessOut.model_rebuild()
JobRetryRequest.model_rebuild()
JobRetryResponse.model_rebuild()
JobRunOut.model_rebuild()
JobStatsOut.model_rebuild()
LNURLActivationCompleteRequest.model_rebuild()
LNURLActivationPurpose.model_rebuild()
LNURLActivationStatus.model_rebuild()
LNURLActivationStatusResponse.model_rebuild()
LNURLApiAuthChallengeRequest.model_rebuild()
LNURLApiAuthSessionRequest.model_rebuild()
LNURLApiAuthStepUpRequest.model_rebuild()
LNURLApiPaySubscriptionRequest.model_rebuild()
LNURLApiWithdrawRequest.model_rebuild()
LNURLAuthAction.model_rebuild()
LNURLErrorResponse.model_rebuild()
LNURLPayDiscoveryResponse.model_rebuild()
MarketAttributionOut.model_rebuild()
MarketEvidenceLink.model_rebuild()
MarketEvidenceRelation.model_rebuild()
MarketNarrativeOut.model_rebuild()
MarketReplayCaptureOut.model_rebuild()
MarketSimilarityMatchOut.model_rebuild()
MarketSimilarityReportOut.model_rebuild()
MarketSourceRef.model_rebuild()
MarketSourceType.model_rebuild()
MarketTimeMachineAnalyticsResponse.model_rebuild()
MarketTimeMachineQueryWindow.model_rebuild()
MarketTimeMachineRuntimeMode.model_rebuild()
MarketTimeMachineSourceStore.model_rebuild()
MarketTimelineEventOut.model_rebuild()
MarketTimelinePageOut.model_rebuild()
MerchantLightningAddressCreate.model_rebuild()
MerchantLightningDomainCreate.model_rebuild()
MetricUsageSummaryOut.model_rebuild()
MetricsStatusOut.model_rebuild()
NarrativeOrigin.model_rebuild()
NewsArticleOut.model_rebuild()
OfferAvailability.model_rebuild()
OnchainChainStateOut.model_rebuild()
OnchainEventOut.model_rebuild()
OperationalEvidencePacketOut.model_rebuild()
OperationalHealthOut.model_rebuild()
OperationalProviderStatusOut.model_rebuild()
OperationsDrillOut.model_rebuild()
OperationsHealthOut.model_rebuild()
OperationsMetricsSummaryOut.model_rebuild()
OperationsRunbookOut.model_rebuild()
OperationsSLOOut.model_rebuild()
OperationsSnapshotOut.model_rebuild()
OperationsStatusOut.model_rebuild()
OperatorActionRequest.model_rebuild()
PaginatedDataEntityOut.model_rebuild()
PaginatedDataNewsArticleOut.model_rebuild()
PaginatedDataOnchainEventOut.model_rebuild()
PaginatedDataSignalOut.model_rebuild()
PaginatedDataTreasuryRequestOut.model_rebuild()
PaginatedDataUserOut.model_rebuild()
PaginatedDataWalletHealthReportOut.model_rebuild()
PaginatedDataWalletProfileOut.model_rebuild()
PaginatedDataWatchedEntityOut.model_rebuild()
PayRegisterLNURLCheckoutCreate.model_rebuild()
PayRegisterLNURLStaticEndpointCreate.model_rebuild()
PayRegisterLNURLStaticEndpointUpdate.model_rebuild()
PaymentContextRiskRequest.model_rebuild()
PaymentDirection.model_rebuild()
PlanCode.model_rebuild()
PluginDryRunRequest.model_rebuild()
PolicyCatalogCompareOut.model_rebuild()
PolicyCatalogCompareRequest.model_rebuild()
PolicyCatalogOut.model_rebuild()
PolicyCatalogUpsertIn.model_rebuild()
PolicyCheckRequest.model_rebuild()
PolicyCheckResponse.model_rebuild()
PolicyExecutionLogOut.model_rebuild()
PolicyExecutionPolicyBreakdownOut.model_rebuild()
PolicyExecutionSummaryOut.model_rebuild()
PolicyRuleOut.model_rebuild()
PolicyRuleUpsertIn.model_rebuild()
PolicySimulationDiffOut.model_rebuild()
PolicySimulationOut.model_rebuild()
PolicySimulationRequest.model_rebuild()
PrivacyAssessmentRequest.model_rebuild()
PrivacyAssessmentResponse.model_rebuild()
ProvenanceEntityDeltaOut.model_rebuild()
ProvenanceRefreshOut.model_rebuild()
ProviderHealthOut.model_rebuild()
ProviderHealthSnapshotOut.model_rebuild()
PublicFeatureAvailability.model_rebuild()
PublicFeatureEntry.model_rebuild()
PublicFeatureStatus.model_rebuild()
PublicLandingResponse.model_rebuild()
PublicRoadmapResponse.model_rebuild()
PublicStatsResponse.model_rebuild()
PublicStatusResponse.model_rebuild()
PublicTraceSummary.model_rebuild()
RecommendationItemOut.model_rebuild()
RecoveryCancelRequest.model_rebuild()
RecoveryCheckOut.model_rebuild()
RecoveryCompleteRequest.model_rebuild()
RecoveryCompleteResponse.model_rebuild()
RecoveryDrillOut.model_rebuild()
RecoveryFactorSubmitRequest.model_rebuild()
RecoveryFactorSubmitResponse.model_rebuild()
RecoveryHotspotOut.model_rebuild()
RecoveryIssueOut.model_rebuild()
RecoveryReadinessOut.model_rebuild()
RecoveryRotateRequest.model_rebuild()
RecoveryRotateResponse.model_rebuild()
RecoverySLOOut.model_rebuild()
RecoverySetupRequest.model_rebuild()
RecoverySetupResponse.model_rebuild()
RecoveryStartRequest.model_rebuild()
RecoveryStartResponse.model_rebuild()
RecoveryStatusResponse.model_rebuild()
ReplayIntegrityOut.model_rebuild()
ResponseEnvelopeCitadelAssessmentOut.model_rebuild()
ResponseEnvelopeCitadelDependencyGraphOut.model_rebuild()
ResponseEnvelopeCitadelInheritanceOut.model_rebuild()
ResponseEnvelopeCitadelOverviewOut.model_rebuild()
ResponseEnvelopeCitadelPolicyChecksOut.model_rebuild()
ResponseEnvelopeCitadelRepairPlanOut.model_rebuild()
ResponseEnvelopeCitadelSimulationOut.model_rebuild()
ResponseEnvelopeFeeRecommendationResponse.model_rebuild()
ResponseEnvelopeJobRetryResponse.model_rebuild()
ResponseEnvelopeOnchainChainStateOut.model_rebuild()
ResponseEnvelopeOperationsSnapshotOut.model_rebuild()
ResponseEnvelopePaginatedDataEntityOut.model_rebuild()
ResponseEnvelopePaginatedDataNewsArticleOut.model_rebuild()
ResponseEnvelopePaginatedDataOnchainEventOut.model_rebuild()
ResponseEnvelopePaginatedDataSignalOut.model_rebuild()
ResponseEnvelopePaginatedDataTreasuryRequestOut.model_rebuild()
ResponseEnvelopePaginatedDataUserOut.model_rebuild()
ResponseEnvelopePaginatedDataWalletHealthReportOut.model_rebuild()
ResponseEnvelopePaginatedDataWalletProfileOut.model_rebuild()
ResponseEnvelopePaginatedDataWatchedEntityOut.model_rebuild()
ResponseEnvelopePolicyCatalogCompareOut.model_rebuild()
ResponseEnvelopePolicyCatalogOut.model_rebuild()
ResponseEnvelopePolicyCheckResponse.model_rebuild()
ResponseEnvelopePolicyExecutionSummaryOut.model_rebuild()
ResponseEnvelopePolicySimulationOut.model_rebuild()
ResponseEnvelopePrivacyAssessmentResponse.model_rebuild()
ResponseEnvelopeProvenanceRefreshOut.model_rebuild()
ResponseEnvelopePublicLandingResponse.model_rebuild()
ResponseEnvelopePublicRoadmapResponse.model_rebuild()
ResponseEnvelopePublicStatsResponse.model_rebuild()
ResponseEnvelopePublicStatusResponse.model_rebuild()
ResponseEnvelopePublicTraceSummary.model_rebuild()
ResponseEnvelopeRecoveryCheckOut.model_rebuild()
ResponseEnvelopeRecoveryReadinessOut.model_rebuild()
ResponseEnvelopeSafeEvidenceExportDTO.model_rebuild()
ResponseEnvelopeSafeEvidenceLineageDTO.model_rebuild()
ResponseEnvelopeSafeEvidenceReplayDTO.model_rebuild()
ResponseEnvelopeSafeEvidenceVerificationDTO.model_rebuild()
ResponseEnvelopeSafeTraceDisagreementCollectionDTO.model_rebuild()
ResponseEnvelopeSafeTraceProofPacketDTO.model_rebuild()
ResponseEnvelopeSignalExplanationOut.model_rebuild()
ResponseEnvelopeSignalRecommendationOut.model_rebuild()
ResponseEnvelopeTraceGraphDTO.model_rebuild()
ResponseEnvelopeTraceGraphHistoryDTO.model_rebuild()
ResponseEnvelopeTraceGraphMetadataDTO.model_rebuild()
ResponseEnvelopeTraceGraphObjectDTO.model_rebuild()
ResponseEnvelopeTraceGraphRelationshipDTO.model_rebuild()
ResponseEnvelopeTraceGraphSnapshotDTO.model_rebuild()
ResponseEnvelopeTraceReport.model_rebuild()
ResponseEnvelopeTraceSourceStatus.model_rebuild()
ResponseEnvelopeTraceSubmissionResult.model_rebuild()
ResponseEnvelopeTraceWatchlistEntry.model_rebuild()
ResponseEnvelopeTreasuryApprovalOut.model_rebuild()
ResponseEnvelopeTreasuryRejectOut.model_rebuild()
ResponseEnvelopeTreasuryRequestOut.model_rebuild()
ResponseEnvelopeUserOut.model_rebuild()
ResponseEnvelopeWalletHealthReportOut.model_rebuild()
ResponseEnvelopeWalletHealthResponse.model_rebuild()
ResponseEnvelopeDictStrAny.model_rebuild()
ResponseEnvelopeDictStrObject.model_rebuild()
ResponseEnvelopeDictStrStr.model_rebuild()
ResponseEnvelopeListAuditLogOut.model_rebuild()
ResponseEnvelopeListCitadelSimulationOut.model_rebuild()
ResponseEnvelopeListEducationSnippetOut.model_rebuild()
ResponseEnvelopeListJobRunOut.model_rebuild()
ResponseEnvelopeListPolicyCatalogOut.model_rebuild()
ResponseEnvelopeListPolicyExecutionLogOut.model_rebuild()
ResponseEnvelopeListPublicFeatureEntry.model_rebuild()
ResponseEnvelopeListSourceReputationProfileOut.model_rebuild()
ResponseEnvelopeListTraceEvidence.model_rebuild()
ResponseEnvelopeListTraceSourceStatus.model_rebuild()
ResponseEnvelopeListTraceWatchlistEntry.model_rebuild()
ResponseEnvelopeListDictStrObject.model_rebuild()
ResponseEnvelopeListStr.model_rebuild()
RuntimeDegradedModeOut.model_rebuild()
RuntimeSeverityOut.model_rebuild()
RuntimeStatusOut.model_rebuild()
SLOComparison.model_rebuild()
SLOStatus.model_rebuild()
SLOUnit.model_rebuild()
SafeBitcoinNetworkClaimValueDTO.model_rebuild()
SafeEvidenceExportDTO.model_rebuild()
SafeEvidenceLineageDTO.model_rebuild()
SafeEvidenceReplayDTO.model_rebuild()
SafeEvidenceVerificationDTO.model_rebuild()
SafeRiskBandClaimValueDTO.model_rebuild()
SafeTraceClaimDTO.model_rebuild()
SafeTraceClaimProvenanceDTO.model_rebuild()
SafeTraceClaimSubjectDTO.model_rebuild()
SafeTraceDisagreementCollectionDTO.model_rebuild()
SafeTraceDisagreementCoverageDTO.model_rebuild()
SafeTraceDisagreementDTO.model_rebuild()
SafeTraceEvidenceDTO.model_rebuild()
SafeTraceProofPacketDTO.model_rebuild()
SignalExplanationOut.model_rebuild()
SignalOut.model_rebuild()
SignalRecommendationOut.model_rebuild()
SimilarityDimensionOut.model_rebuild()
SimilarityIntervalSubject.model_rebuild()
SimilarityIntervalType.model_rebuild()
SimilarityMethod.model_rebuild()
SimilarityStatisticalIntervalOut.model_rebuild()
SimilarityUncertaintyOut.model_rebuild()
SourceReputationProfileOut.model_rebuild()
StorageDegradedMode.model_rebuild()
StorageRole.model_rebuild()
StorageStatusResponse.model_rebuild()
StorageStatusSummary.model_rebuild()
StorageStatusValue.model_rebuild()
StorageStoreStatus.model_rebuild()
SubscriptionEntitlementResponse.model_rebuild()
SystemHealthOut.model_rebuild()
TelegramHealthOut.model_rebuild()
TimelineKind.model_rebuild()
TraceBand.model_rebuild()
TraceConfidenceLedgerEntry.model_rebuild()
TraceDNA.model_rebuild()
TraceEvidence.model_rebuild()
TraceEvidenceIntegrityStatus.model_rebuild()
TraceEvidenceKind.model_rebuild()
TraceEvidenceVerificationStatus.model_rebuild()
TraceFactorContribution.model_rebuild()
TraceFreshness.model_rebuild()
TraceGraphApiVersion.model_rebuild()
TraceGraphDTO.model_rebuild()
TraceGraphError.model_rebuild()
TraceGraphErrorCode.model_rebuild()
TraceGraphEvidenceReferenceDTO.model_rebuild()
TraceGraphHistoryDTO.model_rebuild()
TraceGraphHistoryEntryDTO.model_rebuild()
TraceGraphMetadataDTO.model_rebuild()
TraceGraphObjectDTO.model_rebuild()
TraceGraphObservationDTO.model_rebuild()
TraceGraphProvenanceDTO.model_rebuild()
TraceGraphRelationshipDTO.model_rebuild()
TraceGraphSnapshotDTO.model_rebuild()
TraceProofPacketTopologyReferenceDTO.model_rebuild()
TraceReport.model_rebuild()
TraceScoreBreakdown.model_rebuild()
TraceSnapshotVersion.model_rebuild()
TraceSourceQuality.model_rebuild()
TraceSourceStatus.model_rebuild()
TraceSubjectType.model_rebuild()
TraceSubmissionResult.model_rebuild()
TraceSubmitRequest.model_rebuild()
TraceTopologySourceStatus.model_rebuild()
TraceWatchlistCreate.model_rebuild()
TraceWatchlistEntry.model_rebuild()
TreasuryApprovalActionIn.model_rebuild()
TreasuryApprovalOut.model_rebuild()
TreasuryRejectActionIn.model_rebuild()
TreasuryRejectOut.model_rebuild()
TreasuryRequestIn.model_rebuild()
TreasuryRequestOut.model_rebuild()
UserOut.model_rebuild()
ValidationError.model_rebuild()
WalletApiChallengeRequest.model_rebuild()
WalletApiChallengeResponse.model_rebuild()
WalletApiLockdownRequest.model_rebuild()
WalletApiLoginResponse.model_rebuild()
WalletApiRecoveryCompleteRequest.model_rebuild()
WalletApiRecoveryFactorRequest.model_rebuild()
WalletApiRecoveryStartRequest.model_rebuild()
WalletApiRegistrationResponse.model_rebuild()
WalletApiSessionRequest.model_rebuild()
WalletApiStepUpRequest.model_rebuild()
WalletDeviceClass.model_rebuild()
WalletHealthReportOut.model_rebuild()
WalletHealthRequest.model_rebuild()
WalletHealthResponse.model_rebuild()
WalletLoginRequest.model_rebuild()
WalletNetwork.model_rebuild()
WalletProfileOut.model_rebuild()
WalletProofType.model_rebuild()
WalletRegisterRequest.model_rebuild()
WalletRiskLevel.model_rebuild()
WatchedEntityOut.model_rebuild()
WebhookEndpointCreate.model_rebuild()
WebhookEndpointUpdate.model_rebuild()
WebhookSubscriptionCreate.model_rebuild()
WebhookTestRequest.model_rebuild()
