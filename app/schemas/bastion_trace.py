from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TraceBand(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class TraceFreshness(str, Enum):
    FRESH = "FRESH"
    RECENT = "RECENT"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class TraceSourceQuality(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"


class TraceReasonCode(str, Enum):
    NO_MEANINGFUL_EVIDENCE = "NO_MEANINGFUL_EVIDENCE"
    BASELINE_SCORING_ONLY = "BASELINE_SCORING_ONLY"
    KNOWN_HIGH_RISK_EXPOSURE = "KNOWN_HIGH_RISK_EXPOSURE"
    SUSPICIOUS_PATTERN_SIGNAL = "SUSPICIOUS_PATTERN_SIGNAL"
    PRIVACY_LEAK_SIGNAL = "PRIVACY_LEAK_SIGNAL"
    ORIGIN_UNCERTAIN = "ORIGIN_UNCERTAIN"
    PROVIDER_DISAGREEMENT = "PROVIDER_DISAGREEMENT"
    STALE_EVIDENCE = "STALE_EVIDENCE"
    WEAK_SOURCE_QUALITY = "WEAK_SOURCE_QUALITY"
    NODE_BACKED_CHAIN_CONFIRMATION = "NODE_BACKED_CHAIN_CONFIRMATION"
    MULTIPLE_INDEPENDENT_SOURCES = "MULTIPLE_INDEPENDENT_SOURCES"
    FALSE_POSITIVE_GUARD_APPLIED = "FALSE_POSITIVE_GUARD_APPLIED"
    SOVEREIGNTY_PRESERVED = "SOVEREIGNTY_PRESERVED"
    MANUAL_REVIEW_RECOMMENDED = "MANUAL_REVIEW_RECOMMENDED"
    ADVISORY_ONLY = "ADVISORY_ONLY"
    NOT_LEGAL_VERDICT = "NOT_LEGAL_VERDICT"
    NOT_CONSENSUS_PROOF = "NOT_CONSENSUS_PROOF"
    NO_CUSTODY = "NO_CUSTODY"


class TraceDNA(BaseModel):
    risk: float = Field(ge=0, le=1)
    privacy_exposure: float = Field(ge=0, le=1)
    origin_uncertainty: float = Field(ge=0, le=1)
    provider_disagreement: float = Field(ge=0, le=1)
    freshness_decay: float = Field(ge=0, le=1)
    sovereignty: float = Field(ge=0, le=1)
    evidence_strength: float = Field(ge=0, le=1)
    false_positive_risk: float = Field(ge=0, le=1)


class TraceFactorContribution(BaseModel):
    factor: str
    value: float
    weight: float
    contribution: float
    direction: str
    reason: str


class TraceConfidenceLedgerEntry(BaseModel):
    factor: str
    delta: float
    reason: str


class TraceScoringInput(BaseModel):
    factors: dict[str, float] = Field(default_factory=dict)
    evidence_count: int = 0
    independent_source_count: int = 0
    evidence_freshness_days: list[int] = Field(default_factory=list)
    baseline_mode: bool = True
    reason_codes: list[str] = Field(default_factory=list)


class TraceScoringResult(BaseModel):
    final_score: float
    band: TraceBand
    confidence: float
    source_quality: TraceSourceQuality
    freshness: TraceFreshness
    trace_dna: TraceDNA
    factor_contributions: list[TraceFactorContribution] = Field(default_factory=list)
    confidence_ledger: list[TraceConfidenceLedgerEntry] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)


class TraceScoreBreakdown(BaseModel):
    base_score: float
    final_score: float
    band: TraceBand
    confidence: float
    source_quality: TraceSourceQuality
    freshness: TraceFreshness
    trace_dna: TraceDNA
    factor_contributions: list[TraceFactorContribution] = Field(default_factory=list)
    confidence_ledger: list[TraceConfidenceLedgerEntry] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    operator_guidance: list[str] = Field(default_factory=list)


class TraceReport(BaseModel):
    id: int | None = None
    address: str
    status: str = "COMPLETE"
    summary: str = ""
    chain: str = "bitcoin"
    trace_score: float = 0
    trace_band: TraceBand = TraceBand.UNKNOWN
    confidence: float = 0
    source_quality: TraceSourceQuality = TraceSourceQuality.UNKNOWN
    freshness: TraceFreshness = TraceFreshness.UNKNOWN
    trace_dna: TraceDNA | None = None
    factor_contributions: list[TraceFactorContribution] = Field(default_factory=list)
    confidence_ledger: list[TraceConfidenceLedgerEntry] = Field(default_factory=list)
    score_breakdown: TraceScoreBreakdown | None = None
    reason_codes: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    operator_guidance: list[str] = Field(default_factory=list)
    advisory_not_legal_verdict: bool = True
    not_consensus_proof: bool = True
    no_custody: bool = True
    created_at: datetime | None = None


class TraceSubjectType(str, Enum):
    BITCOIN_ADDRESS = "BITCOIN_ADDRESS"


class TraceSubmitRequest(BaseModel):
    subject_type: TraceSubjectType
    subject: str = Field(min_length=14, max_length=128)
    network: str = Field(default="bitcoin-mainnet", pattern="^bitcoin-mainnet$")


class TraceSubmissionResult(BaseModel):
    trace_id: int
    report_id: int
    status: str = "COMPLETE"
    normalized_subject: str
    network: str = "bitcoin-mainnet"
    idempotency_replayed: bool = False


class TraceEvidence(BaseModel):
    id: int
    report_id: int
    evidence_type: str
    source_name: str
    source_type: str
    confidence: float
    freshness_days: int
    description: str
    limitations: list[str] = Field(default_factory=list)
    evidence_ref: str
    created_at: datetime


class TraceSourceStatus(BaseModel):
    id: int
    source_name: str
    source_type: str
    trust_level: str
    enabled: bool
    freshness: str = "UNKNOWN"
    confidence: float = 0.0
    last_refreshed_at: datetime | None = None
    last_refresh_status: str = "UNKNOWN"
    limitations: list[str] = Field(default_factory=list)
    is_internal: bool = False
    is_external: bool = False
    is_synthetic: bool = False
    is_node_backed: bool = False


class TraceWatchlistEntry(BaseModel):
    id: int
    address: str
    label: str
    reason: str
    risk_hint: str
    active: bool
    created_at: datetime


class TraceWatchlistCreate(BaseModel):
    address: str
    label: str = ""
    reason: str = ""
    risk_hint: str = "UNKNOWN"


class TraceSourceType(str, Enum):
    NODE = "NODE"
    INDEXER = "INDEXER"
    PUBLIC_DATASET = "PUBLIC_DATASET"
    COMMERCIAL_PROVIDER = "COMMERCIAL_PROVIDER"
    INTERNAL_WATCHLIST = "INTERNAL_WATCHLIST"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    SYNTHETIC_BASELINE = "SYNTHETIC_BASELINE"
    UNKNOWN = "UNKNOWN"


class TraceSourceTrustLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class TraceSourceFreshness(str, Enum):
    FRESH = "FRESH"
    RECENT = "RECENT"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class ProviderDisagreementSeverity(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ProviderDisagreementType(str, Enum):
    RISK_BAND_CONFLICT = "RISK_BAND_CONFLICT"
    ORIGIN_CONFLICT = "ORIGIN_CONFLICT"
    CONFIDENCE_CONFLICT = "CONFIDENCE_CONFLICT"
    FRESHNESS_CONFLICT = "FRESHNESS_CONFLICT"
    SOURCE_QUALITY_CONFLICT = "SOURCE_QUALITY_CONFLICT"
    NO_CONFLICT = "NO_CONFLICT"


class ProviderDisagreementResult(BaseModel):
    has_disagreement: bool
    severity: ProviderDisagreementSeverity
    disagreement_type: ProviderDisagreementType
    description: str
    affected_fields: list[str] = Field(default_factory=list)
    source_names: list[str] = Field(default_factory=list)
    confidence_impact: float = 0.0
    manual_review_recommended: bool = False
    reason_codes: list[str] = Field(default_factory=list)


class EvidenceIndependenceResult(BaseModel):
    score: float = Field(ge=0, le=1)
    source_count: int
    independent_source_count: int
    dominant_source: str
    dominant_source_share: float = Field(ge=0, le=1)
    limitations: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)


class OriginPassport(BaseModel):
    address: str
    chain: str
    origin_category: str
    origin_label: str
    origin_confidence: float = Field(ge=0, le=1)
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    source_count: int
    independent_source_count: int
    evidence_refs: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    provider_disagreement: ProviderDisagreementResult
    evidence_independence_score: float = Field(ge=0, le=1)
    advisory_not_legal_verdict: bool = True
    not_consensus_proof: bool = True
    no_custody: bool = True
    created_at: datetime


class PrivacyBand(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class PrivacyRiskLevel(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class UTXOHygieneReport(BaseModel):
    hygiene_score: float | None = None
    hygiene_band: PrivacyBand = PrivacyBand.UNKNOWN
    utxo_count: int = 0
    small_utxo_count: int = 0
    large_utxo_count: int = 0
    dust_like_utxo_count: int = 0
    reuse_detected: bool = False
    consolidation_risk_level: PrivacyRiskLevel = PrivacyRiskLevel.UNKNOWN
    toxic_change_risk_level: PrivacyRiskLevel = PrivacyRiskLevel.UNKNOWN
    limitations: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)


class DustRadarReport(BaseModel):
    dust_exposure_detected: bool
    dust_like_utxo_count: int
    dust_threshold_sats: int
    dust_exposure_score: float
    limitations: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)


class AddressReuseReport(BaseModel):
    reuse_detected: bool
    reuse_count: int
    reuse_risk_level: PrivacyRiskLevel
    limitations: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)


class ConsolidationRiskReport(BaseModel):
    consolidation_risk_level: PrivacyRiskLevel
    input_count: int
    utxo_count: int
    small_utxo_ratio: float
    reason_codes: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class ToxicChangeReport(BaseModel):
    toxic_change_risk_level: PrivacyRiskLevel
    possible_toxic_change_detected: bool
    heuristic_confidence: float
    limitations: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)


class PrivacyGuidance(BaseModel):
    items: list[str] = Field(default_factory=list)


class PrivacyShieldReport(BaseModel):
    address: str
    chain: str
    privacy_exposure_score: float
    privacy_band: PrivacyBand
    utxo_hygiene: UTXOHygieneReport
    dust_radar: DustRadarReport
    address_reuse: AddressReuseReport
    consolidation_risk: ConsolidationRiskReport
    toxic_change: ToxicChangeReport
    privacy_reason_codes: list[str] = Field(default_factory=list)
    privacy_limitations: list[str] = Field(default_factory=list)
    privacy_guidance: PrivacyGuidance
    evidence_refs: list[str] = Field(default_factory=list)
    confidence: float
    freshness: str
    advisory_not_legal_verdict: bool = True
    not_consensus_proof: bool = True
    no_custody: bool = True
    created_at: datetime


class CounterpartyType(str, Enum):
    EXCHANGE = "EXCHANGE"
    MERCHANT = "MERCHANT"
    INDIVIDUAL = "INDIVIDUAL"
    MINER = "MINER"
    INSTITUTION = "INSTITUTION"
    UNKNOWN = "UNKNOWN"


class CounterpartyRiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class PaymentDirection(str, Enum):
    SEND = "SEND"
    RECEIVE = "RECEIVE"
    UNKNOWN = "UNKNOWN"


class SafeToSendAdvisory(str, Enum):
    PROCEED_WITH_CAUTION = "PROCEED_WITH_CAUTION"
    MANUAL_REVIEW_RECOMMENDED = "MANUAL_REVIEW_RECOMMENDED"
    DO_NOT_PROCEED_WITHOUT_REVIEW = "DO_NOT_PROCEED_WITHOUT_REVIEW"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"


class ContextSensitivity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"
    UNKNOWN = "UNKNOWN"


class AmountSensitivity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"
    UNKNOWN = "UNKNOWN"


class DestinationReviewLevel(str, Enum):
    NONE = "NONE"
    LIGHT_REVIEW = "LIGHT_REVIEW"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    SENIOR_REVIEW = "SENIOR_REVIEW"


class CounterpartyLens(BaseModel):
    address: str
    chain: str
    counterparty_label: str
    counterparty_type: CounterpartyType
    counterparty_confidence: float
    trace_band: str
    privacy_band: str
    origin_category: str
    provider_disagreement_severity: str
    evidence_independence_score: float
    counterparty_risk_level: CounterpartyRiskLevel
    manual_review_recommended: bool
    limitations: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    operator_guidance: list[str] = Field(default_factory=list)
    advisory_not_legal_verdict: bool = True
    not_consensus_proof: bool = True
    no_custody: bool = True
    created_at: datetime


class DestinationReviewResult(BaseModel):
    review_level: DestinationReviewLevel
    manual_review_recommended: bool
    review_reasons: list[str] = Field(default_factory=list)
    operator_guidance: list[str] = Field(default_factory=list)


class PaymentContextRiskRequest(BaseModel):
    address: str
    amount_sats: int | None = None
    direction: PaymentDirection = PaymentDirection.UNKNOWN
    payment_purpose: str | None = None
    counterparty_label: str | None = None
    operator_role: str | None = None
    business_context: str | None = None
    urgency: str | None = None
    known_relationship: bool | None = None


class PaymentContextRiskReport(BaseModel):
    payment_context_id: str
    address: str
    chain: str
    amount_sats: int | None = None
    direction: PaymentDirection
    context_risk_level: str
    context_sensitivity: ContextSensitivity
    amount_sensitivity: AmountSensitivity
    counterparty_lens: dict[str, object]
    safe_to_send_advisory: SafeToSendAdvisory
    manual_review_recommended: bool
    policy_hint: str
    limitations: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    operator_guidance: list[str] = Field(default_factory=list)
    created_at: datetime


class PaymentIntentPreviewRequest(PaymentContextRiskRequest):
    pass


class PaymentIntentPreviewReport(PaymentContextRiskReport):
    transaction_signing_performed: bool = False
    transaction_broadcast_performed: bool = False


class LiteTraceStatus(str, Enum):
    READY = "Ready"
    NEEDS_CAUTION = "Needs caution"
    MANUAL_REVIEW_RECOMMENDED = "Manual review recommended"
    INSUFFICIENT_INFORMATION = "Insufficient information"
    REJECTED_INPUT = "Rejected input"


class LiteRiskLabel(str, Enum):
    NO_STRONG_RISK_SIGNAL_FOUND = "No strong risk signal found"
    CAUTION = "Caution"
    HIGH_CAUTION = "High caution"
    CRITICAL_REVIEW_REQUIRED = "Critical review required"
    UNKNOWN = "Unknown"


class LiteConfidenceLabel(str, Enum):
    LOW_CONFIDENCE = "Low confidence"
    MEDIUM_CONFIDENCE = "Medium confidence"
    HIGH_CONFIDENCE = "High confidence"
    UNKNOWN_CONFIDENCE = "Unknown confidence"


class LiteTraceReport(BaseModel):
    address: str
    chain: str
    status_label: LiteTraceStatus
    risk_label: LiteRiskLabel
    privacy_label: str
    origin_label: str
    confidence_label: LiteConfidenceLabel
    safe_to_send_advisory: str
    short_summary: str
    what_this_means: str
    recommended_next_step: str
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    qr_payload: str
    clipboard_payload: str
    report_id: int | None = None
    created_at: datetime | None = None


class LiteTraceRequest(BaseModel):
    address: str


class LiteTraceResponse(BaseModel):
    report: LiteTraceReport


class BusinessContextType(str, Enum):
    RETAIL = "RETAIL"
    MERCHANT = "MERCHANT"
    TREASURY = "TREASURY"
    OTC = "OTC"
    DONATION = "DONATION"
    CONSULTING = "CONSULTING"
    UNKNOWN = "UNKNOWN"


class BusinessPolicyAction(str, Enum):
    ACCEPT = "ACCEPT"
    ACCEPT_WITH_NOTE = "ACCEPT_WITH_NOTE"
    HOLD_FOR_REVIEW = "HOLD_FOR_REVIEW"
    REJECT_BY_POLICY = "REJECT_BY_POLICY"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"


class BusinessCapability(str, Enum):
    BATCH_SCREENING = "BATCH_SCREENING"
    BUSINESS_POLICY_PROFILES = "BUSINESS_POLICY_PROFILES"
    REVIEW_DESK = "REVIEW_DESK"
    OPERATOR_NOTES = "OPERATOR_NOTES"
    PROOF_PACKET_EXPORT = "PROOF_PACKET_EXPORT"
    ACCOUNTING_EXPORT = "ACCOUNTING_EXPORT"
    WATCHLIST_GROUPS = "WATCHLIST_GROUPS"
    WEBHOOK_PLACEHOLDER = "WEBHOOK_PLACEHOLDER"
    REGISTER_INTEGRATION_PLACEHOLDER = "REGISTER_INTEGRATION_PLACEHOLDER"
    TREASURY_INTEGRATION_PLACEHOLDER = "TREASURY_INTEGRATION_PLACEHOLDER"
    API_KEY_SCOPE_PLACEHOLDER = "API_KEY_SCOPE_PLACEHOLDER"


class BusinessTierProfile(BaseModel):
    tier: str
    capabilities: list[BusinessCapability] = Field(default_factory=list)
    limits: dict[str, object] = Field(default_factory=dict)
    feature_flags: dict[str, bool] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)


class BatchTraceRequest(BaseModel):
    addresses: list[str]
    batch_label: str | None = None
    business_context: BusinessContextType = BusinessContextType.UNKNOWN
    policy_profile_id: str | None = None


class BatchTraceItemResult(BaseModel):
    address: str
    status: str
    rejection_reason: str | None = None
    report_id: int | None = None
    trace_band: str | None = None
    trace_score: float | None = None
    confidence: float | None = None
    policy_action: BusinessPolicyAction | None = None
    manual_review_recommended: bool = False
    limitations: list[str] = Field(default_factory=list)


class BatchTraceResult(BaseModel):
    batch_id: int
    batch_label: str | None = None
    business_context: BusinessContextType = BusinessContextType.UNKNOWN
    total_addresses: int
    processed_count: int
    rejected_count: int
    low_count: int
    medium_count: int
    high_count: int
    critical_count: int
    unknown_count: int
    manual_review_count: int
    reports: list[BatchTraceItemResult] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    created_at: datetime | None = None


class BusinessPolicyProfile(BaseModel):
    id: str
    name: str
    description: str
    context_type: BusinessContextType = BusinessContextType.UNKNOWN
    low_action: BusinessPolicyAction = BusinessPolicyAction.ACCEPT
    medium_action: BusinessPolicyAction = BusinessPolicyAction.HOLD_FOR_REVIEW
    high_action: BusinessPolicyAction = BusinessPolicyAction.HOLD_FOR_REVIEW
    critical_action: BusinessPolicyAction = BusinessPolicyAction.REJECT_BY_POLICY
    unknown_action: BusinessPolicyAction = BusinessPolicyAction.INSUFFICIENT_INFORMATION
    manual_review_threshold: str = "MEDIUM"
    high_value_threshold_sats: int = 5_000_000
    require_review_on_provider_disagreement: bool = True
    require_review_on_low_confidence: bool = True
    require_review_on_privacy_high: bool = False
    limitations: list[str] = Field(default_factory=list)


class ReviewStatus(str, Enum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    NEEDS_MORE_EVIDENCE = "NEEDS_MORE_EVIDENCE"
    APPROVED_WITH_NOTE = "APPROVED_WITH_NOTE"
    REJECTED_BY_POLICY = "REJECTED_BY_POLICY"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    CLOSED = "CLOSED"


class ReviewPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ReviewDecision(str, Enum):
    NO_DECISION = "NO_DECISION"
    APPROVE_WITH_CAUTION = "APPROVE_WITH_CAUTION"
    HOLD_FOR_REVIEW = "HOLD_FOR_REVIEW"
    REJECT_BY_POLICY = "REJECT_BY_POLICY"
    MARK_FALSE_POSITIVE = "MARK_FALSE_POSITIVE"
    REQUEST_MORE_EVIDENCE = "REQUEST_MORE_EVIDENCE"


class ReviewDeskItem(BaseModel):
    id: int
    report_id: int | None = None
    batch_id: int | None = None
    address: str
    review_status: ReviewStatus = ReviewStatus.OPEN
    review_priority: ReviewPriority = ReviewPriority.MEDIUM
    assigned_to: str | None = None
    operator_note_count: int = 0
    decision: ReviewDecision = ReviewDecision.NO_DECISION
    decision_reason: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
    closed_at: datetime | None = None


class OperatorNoteType(str, Enum):
    GENERAL = "GENERAL"
    RISK_CONTEXT = "RISK_CONTEXT"
    FALSE_POSITIVE_REASON = "FALSE_POSITIVE_REASON"
    BUSINESS_DECISION = "BUSINESS_DECISION"
    EVIDENCE_GAP = "EVIDENCE_GAP"
    FOLLOW_UP = "FOLLOW_UP"


class OperatorNote(BaseModel):
    id: int
    review_item_id: int | None = None
    report_id: int | None = None
    note_type: OperatorNoteType = OperatorNoteType.GENERAL
    note: str
    created_by: str | None = None
    redacted: bool = False
    created_at: datetime | None = None


class BusinessProofPacket(BaseModel):
    report_id: int
    base_proof_packet: dict[str, object] = Field(default_factory=dict)
    business_context: str = "UNKNOWN"
    policy_profile: dict[str, object] | None = None
    policy_action: BusinessPolicyAction = BusinessPolicyAction.INSUFFICIENT_INFORMATION
    review_item: dict[str, object] | None = None
    operator_notes: list[dict[str, object]] = Field(default_factory=list)
    batch_reference: dict[str, object] | None = None
    accounting_summary: dict[str, object] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    advisory_not_legal_verdict: bool = True
    not_consensus_proof: bool = True
    no_custody: bool = True
    not_payment_authorization: bool = True


class BusinessExportFormat(str, Enum):
    JSON = "JSON"
    CSV = "CSV"
    MARKDOWN = "MARKDOWN"
    PDF_UNSUPPORTED = "PDF_UNSUPPORTED"


class BusinessExportRequest(BaseModel):
    batch_id: int | None = None
    report_id: int | None = None
    format: BusinessExportFormat = BusinessExportFormat.JSON


class BusinessExportResult(BaseModel):
    format: BusinessExportFormat
    payload_json: object | None = None
    payload_text: str | None = None
    limitations: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)


class BusinessTraceEventType(str, Enum):
    TRACE_BATCH_COMPLETED = "TRACE_BATCH_COMPLETED"
    TRACE_REVIEW_REQUIRED = "TRACE_REVIEW_REQUIRED"
    TRACE_POLICY_ACTION_ASSIGNED = "TRACE_POLICY_ACTION_ASSIGNED"
    TRACE_REVIEW_CLOSED = "TRACE_REVIEW_CLOSED"
    TRACE_PROOF_PACKET_CREATED = "TRACE_PROOF_PACKET_CREATED"


class BusinessTraceEvent(BaseModel):
    id: int | None = None
    event_type: BusinessTraceEventType
    payload: dict[str, object] = Field(default_factory=dict)
    delivered: bool = False
    created_at: datetime | None = None


class ApiKeyScopePlaceholder(BaseModel):
    scope: str = "trace:business:*"
    enabled: bool = False
    limitation: str = "api_key_scope_placeholder_only"


class EnterpriseCapability(str, Enum):
    ENTERPRISE_RBAC_PLACEHOLDER = "ENTERPRISE_RBAC_PLACEHOLDER"
    SSO_PLACEHOLDER = "SSO_PLACEHOLDER"
    LEGAL_HOLD = "LEGAL_HOLD"
    IMMUTABLE_AUDIT_LOG = "IMMUTABLE_AUDIT_LOG"
    SIEM_HOOKS = "SIEM_HOOKS"
    RETENTION_POLICY = "RETENTION_POLICY"
    EVIDENCE_ACCESS_GOVERNANCE = "EVIDENCE_ACCESS_GOVERNANCE"
    ENTERPRISE_PROOF_PACKET = "ENTERPRISE_PROOF_PACKET"
    ORG_POLICY_PLACEHOLDER = "ORG_POLICY_PLACEHOLDER"
    APPROVAL_WORKFLOW_PLACEHOLDER = "APPROVAL_WORKFLOW_PLACEHOLDER"


class EnterpriseTierProfile(BaseModel):
    tier: str
    capabilities: list[EnterpriseCapability] = Field(default_factory=list)
    limits: dict[str, object] = Field(default_factory=dict)
    feature_flags: dict[str, bool] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)


class EnterpriseRole(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    REVIEWER = "REVIEWER"
    AUDITOR = "AUDITOR"
    READ_ONLY = "READ_ONLY"


class EnterprisePermission(str, Enum):
    TRACE_READ = "TRACE_READ"
    TRACE_CREATE = "TRACE_CREATE"
    TRACE_BATCH_CREATE = "TRACE_BATCH_CREATE"
    TRACE_REVIEW_DECIDE = "TRACE_REVIEW_DECIDE"
    TRACE_POLICY_MANAGE = "TRACE_POLICY_MANAGE"
    TRACE_EXPORT_CREATE = "TRACE_EXPORT_CREATE"
    TRACE_LEGAL_HOLD_MANAGE = "TRACE_LEGAL_HOLD_MANAGE"
    TRACE_AUDIT_READ = "TRACE_AUDIT_READ"
    TRACE_SIEM_MANAGE = "TRACE_SIEM_MANAGE"
    TRACE_ADMIN = "TRACE_ADMIN"


class RbacPolicyPlaceholder(BaseModel):
    role_permissions: dict[EnterpriseRole, list[EnterprisePermission]] = Field(default_factory=dict)
    production_enforced: bool = False
    limitations: list[str] = Field(default_factory=list)


class SsoProviderType(str, Enum):
    OIDC = "OIDC"
    SAML = "SAML"
    GOOGLE_WORKSPACE = "GOOGLE_WORKSPACE"
    MICROSOFT_ENTRA = "MICROSOFT_ENTRA"
    CUSTOM = "CUSTOM"
    UNCONFIGURED = "UNCONFIGURED"


class SsoConfigPlaceholder(BaseModel):
    provider_type: SsoProviderType
    configured: bool
    issuer_url: str | None = None
    client_id_present: bool = False
    metadata_url_present: bool = False
    limitations: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class LegalHoldTargetType(str, Enum):
    TRACE_REPORT = "TRACE_REPORT"
    TRACE_BATCH = "TRACE_BATCH"
    TRACE_REVIEW_ITEM = "TRACE_REVIEW_ITEM"
    TRACE_PROOF_PACKET = "TRACE_PROOF_PACKET"
    TRACE_EXPORT = "TRACE_EXPORT"
    UNKNOWN = "UNKNOWN"


class LegalHoldStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"


class LegalHold(BaseModel):
    id: int
    target_type: LegalHoldTargetType
    target_id: str
    reason: str
    status: LegalHoldStatus = LegalHoldStatus.ACTIVE
    created_by: str | None = None
    created_at: datetime | None = None
    released_at: datetime | None = None
    limitations: list[str] = Field(default_factory=list)


class ImmutableAuditEvent(BaseModel):
    id: int | None = None
    event_type: str
    actor_id: str | None = None
    actor_role: str | None = None
    target_type: str
    target_id: str
    action: str
    payload_hash: str
    previous_hash: str | None = None
    event_hash: str
    created_at: datetime | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)


class AuditHashChainVerificationResult(BaseModel):
    valid: bool
    checked_events: int
    first_mismatch_event_id: int | None = None


class SiemEventFormat(str, Enum):
    JSON = "JSON"
    CEF_PLACEHOLDER = "CEF_PLACEHOLDER"
    LEEF_PLACEHOLDER = "LEEF_PLACEHOLDER"


class SiemSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SiemDeliveryStatus(str, Enum):
    PLACEHOLDER_NOT_DELIVERED = "PLACEHOLDER_NOT_DELIVERED"


class SiemEvent(BaseModel):
    id: int | None = None
    event_type: str
    severity: SiemSeverity
    target_type: str
    target_id: str
    payload: dict[str, object] = Field(default_factory=dict)
    export_format: SiemEventFormat = SiemEventFormat.JSON
    delivered: bool = False
    delivery_status: SiemDeliveryStatus = SiemDeliveryStatus.PLACEHOLDER_NOT_DELIVERED
    limitations: list[str] = Field(default_factory=list)
    created_at: datetime | None = None


class RetentionPolicy(BaseModel):
    id: int
    name: str
    target_type: str
    retention_days: int
    legal_hold_override: bool = True
    auto_delete_enabled: bool = False
    limitations: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class EvidenceAccessDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REDACT = "REDACT"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


class EvidenceAccessRequest(BaseModel):
    evidence_ref: str
    requester_role: EnterpriseRole
    purpose: str


class EnterpriseProofPacket(BaseModel):
    base_proof_packet: dict[str, object] = Field(default_factory=dict)
    legal_hold_status: str = "UNKNOWN"
    audit_event_refs: list[int] = Field(default_factory=list)
    siem_event_refs: list[int] = Field(default_factory=list)
    retention_policy_summary: dict[str, object] = Field(default_factory=dict)
    evidence_access_decisions: list[dict[str, object]] = Field(default_factory=list)
    rbac_context: dict[str, object] = Field(default_factory=dict)
    sso_context: dict[str, object] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    advisory_not_legal_verdict: bool = True
    not_consensus_proof: bool = True
    no_custody: bool = True
    not_payment_authorization: bool = True
    not_legal_advice: bool = True


class BastionTraceCitadelContribution(BaseModel):
    trace_report_id: int
    trace_band: str
    trace_score: float
    confidence: float
    privacy_band: str = "UNKNOWN"
    origin_category: str = "unknown"
    provider_disagreement_severity: str = "NONE"
    evidence_independence_score: float = 0.0
    manual_review_recommended: bool = False
    highest_exposure_band: str = "UNKNOWN"
    citadel_score_impact: int = 0
    reason_codes: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    operator_guidance: list[str] = Field(default_factory=list)


class BastionTracePolicyFacts(BaseModel):
    trace_band: str
    trace_score: float
    confidence: float
    privacy_band: str = "UNKNOWN"
    provider_disagreement_severity: str = "NONE"
    safe_to_send_advisory: str = "INSUFFICIENT_INFORMATION"
    manual_review_recommended: bool = False
    business_policy_action: str = "INSUFFICIENT_INFORMATION"
    enterprise_legal_hold_active: bool = False
    evidence_independence_score: float = 0.0


class BastionTracePolicyRecommendation(BaseModel):
    recommendation: str


class BastionTraceTreasuryAdvisory(BaseModel):
    destination_address: str
    trace_report_id: int
    trace_band: str
    safe_to_send_advisory: str
    manual_review_recommended: bool
    treasury_review_level: str
    approval_packet_hint: str
    limitations: list[str] = Field(default_factory=list)
    operator_guidance: list[str] = Field(default_factory=list)


class BastionTraceRegisterAdvisory(BaseModel):
    incoming_payment_id: str | None = None
    payer_address: str | None = None
    trace_report_id: int
    merchant_recommendation: str
    risk_receipt_hint: str
    manual_review_recommended: bool
    limitations: list[str] = Field(default_factory=list)
    operator_guidance: list[str] = Field(default_factory=list)


class BastionTraceEvidenceReference(BaseModel):
    domain: str
    artifact_type: str
    artifact_id: str
    artifact_hash: str | None = None
    report_id: int
    receipt_id: str | None = None
    proof_packet_id: str | None = None
    created_at: str
    limitations: list[str] = Field(default_factory=list)


class BastionTraceOperationsStatus(BaseModel):
    trace_module_status: str
    trace_baseline_mode: bool
    trace_sources_count: int
    trace_external_sources_enabled: bool
    trace_local_only_supported: bool
    trace_last_report_at: str | None = None
    trace_known_limitations: list[str] = Field(default_factory=list)
    trace_production_calibrated: bool


class BastionTraceTreasuryCheckRequest(BaseModel):
    destination_address: str


class BastionTraceRegisterAdvisoryRequest(BaseModel):
    payer_address: str
    incoming_payment_id: str | None = None
