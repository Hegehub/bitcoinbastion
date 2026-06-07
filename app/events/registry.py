from pydantic import BaseModel

from app.events.safety import SafetyFlag
from app.events.types import BastionEventType, EventDomain, EventSeverity, EventVisibility


class EventMetadata(BaseModel):
    event_type: BastionEventType
    domain: EventDomain
    description: str
    default_visibility: EventVisibility
    default_severity: EventSeverity
    webhook_allowed: bool
    websocket_allowed: bool
    audit_required: bool
    public_safe: bool
    contains_financial_advice: bool = False
    contains_legal_verdict: bool = False
    requires_operator_review: bool = False
    safety_flags: list[SafetyFlag]


def _metadata(
    event_type: BastionEventType,
    domain: EventDomain,
    description: str,
    *,
    visibility: EventVisibility = EventVisibility.INTERNAL,
    severity: EventSeverity = EventSeverity.INFO,
    webhook: bool = False,
    websocket: bool = False,
    audit: bool = False,
    public_safe: bool = False,
    review: bool = False,
    flags: list[SafetyFlag] | None = None,
) -> EventMetadata:
    return EventMetadata(
        event_type=event_type,
        domain=domain,
        description=description,
        default_visibility=visibility,
        default_severity=severity,
        webhook_allowed=webhook,
        websocket_allowed=websocket,
        audit_required=audit,
        public_safe=public_safe,
        requires_operator_review=review,
        safety_flags=flags or [],
    )


TRACE_FLAGS = [
    SafetyFlag.ADVISORY_ONLY,
    SafetyFlag.NOT_LEGAL_VERIFICATION,
    SafetyFlag.NOT_BITCOIN_CONSENSUS_PROOF,
    SafetyFlag.NO_CUSTODY,
    SafetyFlag.PUBLIC_DATA_ONLY,
]
MARKET_FLAGS = [SafetyFlag.NOT_FINANCIAL_ADVICE, SafetyFlag.CORRELATION_NOT_CAUSATION]
SIGNAL_FLAGS = [SafetyFlag.NOT_FINANCIAL_ADVICE, SafetyFlag.CORRELATION_NOT_CAUSATION]
PROVIDER_FLAGS = [SafetyFlag.DEGRADED_DATA_VISIBLE, SafetyFlag.STALE_DATA_VISIBLE]
NO_AUTO_FLAGS = [SafetyFlag.NO_AUTO_EXECUTION, SafetyFlag.OPERATOR_REVIEW_REQUIRED]

EVENT_REGISTRY: dict[BastionEventType, EventMetadata] = {
    BastionEventType.NEWS_ARTICLE_CREATED: _metadata(
        BastionEventType.NEWS_ARTICLE_CREATED,
        EventDomain.NEWS,
        "News article was ingested.",
    ),
    BastionEventType.NEWS_ARTICLE_SCORED: _metadata(
        BastionEventType.NEWS_ARTICLE_SCORED,
        EventDomain.NEWS,
        "News article received an advisory score.",
        flags=MARKET_FLAGS,
    ),
    BastionEventType.NEWS_EVENT_CREATED: _metadata(
        BastionEventType.NEWS_EVENT_CREATED,
        EventDomain.EVENT,
        "News event cluster was created.",
        flags=MARKET_FLAGS,
    ),
    BastionEventType.NEWS_EVENT_HIGH_IMPACT: _metadata(
        BastionEventType.NEWS_EVENT_HIGH_IMPACT,
        EventDomain.EVENT,
        "News event crossed high-impact review threshold.",
        severity=EventSeverity.WARNING,
        review=True,
        flags=MARKET_FLAGS + [SafetyFlag.OPERATOR_REVIEW_REQUIRED],
    ),
    BastionEventType.SIGNAL_CREATED: _metadata(
        BastionEventType.SIGNAL_CREATED,
        EventDomain.SIGNAL,
        "Signal candidate was created.",
        flags=SIGNAL_FLAGS,
    ),
    BastionEventType.SIGNAL_PUBLISHED: _metadata(
        BastionEventType.SIGNAL_PUBLISHED,
        EventDomain.SIGNAL,
        "Signal was published after governance checks.",
        visibility=EventVisibility.RESTRICTED,
        webhook=True,
        websocket=True,
        audit=True,
        review=True,
        flags=SIGNAL_FLAGS + [SafetyFlag.OPERATOR_REVIEW_REQUIRED],
    ),
    BastionEventType.SIGNAL_SUPPRESSED: _metadata(
        BastionEventType.SIGNAL_SUPPRESSED,
        EventDomain.SIGNAL,
        "Signal was suppressed by policy or operator control.",
        audit=True,
        flags=SIGNAL_FLAGS + [SafetyFlag.NO_AUTO_EXECUTION],
    ),
    BastionEventType.SIGNAL_OPERATOR_REVIEW_REQUIRED: _metadata(
        BastionEventType.SIGNAL_OPERATOR_REVIEW_REQUIRED,
        EventDomain.SIGNAL,
        "Signal requires operator review.",
        severity=EventSeverity.WARNING,
        audit=True,
        review=True,
        flags=SIGNAL_FLAGS + [SafetyFlag.OPERATOR_REVIEW_REQUIRED],
    ),
    BastionEventType.ONCHAIN_LARGE_TRANSFER: _metadata(
        BastionEventType.ONCHAIN_LARGE_TRANSFER,
        EventDomain.ONCHAIN,
        "Large on-chain transfer was observed.",
        websocket=True,
        flags=[SafetyFlag.PUBLIC_DATA_ONLY],
    ),
    BastionEventType.ONCHAIN_WATCHLIST_HIT: _metadata(
        BastionEventType.ONCHAIN_WATCHLIST_HIT,
        EventDomain.ONCHAIN,
        "On-chain watchlist condition matched.",
        severity=EventSeverity.WARNING,
        audit=True,
        review=True,
        flags=[SafetyFlag.PUBLIC_DATA_ONLY, SafetyFlag.OPERATOR_REVIEW_REQUIRED],
    ),
    BastionEventType.ONCHAIN_FEE_SPIKE: _metadata(
        BastionEventType.ONCHAIN_FEE_SPIKE,
        EventDomain.ONCHAIN,
        "Fee environment spike was observed.",
        websocket=True,
        flags=[SafetyFlag.PUBLIC_DATA_ONLY],
    ),
    BastionEventType.ONCHAIN_MEMPOOL_PRESSURE: _metadata(
        BastionEventType.ONCHAIN_MEMPOOL_PRESSURE,
        EventDomain.ONCHAIN,
        "Mempool pressure changed materially.",
        websocket=True,
        flags=[SafetyFlag.PUBLIC_DATA_ONLY, SafetyFlag.DEGRADED_DATA_VISIBLE],
    ),
    BastionEventType.TRACE_REPORT_CREATED: _metadata(
        BastionEventType.TRACE_REPORT_CREATED,
        EventDomain.TRACE,
        "Trace report was created.",
        webhook=True,
        audit=True,
        flags=TRACE_FLAGS,
    ),
    BastionEventType.TRACE_RISK_BAND_CHANGED: _metadata(
        BastionEventType.TRACE_RISK_BAND_CHANGED,
        EventDomain.TRACE,
        "Trace risk band changed.",
        severity=EventSeverity.WARNING,
        webhook=True,
        audit=True,
        review=True,
        flags=TRACE_FLAGS + [SafetyFlag.OPERATOR_REVIEW_REQUIRED],
    ),
    BastionEventType.TRACE_BATCH_COMPLETED: _metadata(
        BastionEventType.TRACE_BATCH_COMPLETED,
        EventDomain.TRACE,
        "Trace batch screening completed.",
        webhook=True,
        audit=True,
        flags=TRACE_FLAGS,
    ),
    BastionEventType.TRACE_SOURCE_DISAGREEMENT_DETECTED: _metadata(
        BastionEventType.TRACE_SOURCE_DISAGREEMENT_DETECTED,
        EventDomain.TRACE,
        "Trace source disagreement was detected.",
        severity=EventSeverity.WARNING,
        audit=True,
        review=True,
        flags=TRACE_FLAGS
        + [SafetyFlag.PROVIDER_DISAGREEMENT_VISIBLE, SafetyFlag.OPERATOR_REVIEW_REQUIRED],
    ),
    BastionEventType.TRACE_TREASURY_DESTINATION_CHECK_CREATED: _metadata(
        BastionEventType.TRACE_TREASURY_DESTINATION_CHECK_CREATED,
        EventDomain.TRACE,
        "Trace treasury destination check was created.",
        webhook=True,
        audit=True,
        review=True,
        flags=TRACE_FLAGS + [SafetyFlag.OPERATOR_REVIEW_REQUIRED],
    ),
    BastionEventType.WALLET_HEALTH_GENERATED: _metadata(
        BastionEventType.WALLET_HEALTH_GENERATED,
        EventDomain.WALLET,
        "Wallet health report metadata was generated.",
        audit=True,
        flags=[SafetyFlag.NO_CUSTODY, SafetyFlag.PUBLIC_DATA_ONLY],
    ),
    BastionEventType.WALLET_PRIVACY_RISK_HIGH: _metadata(
        BastionEventType.WALLET_PRIVACY_RISK_HIGH,
        EventDomain.WALLET,
        "Wallet privacy risk crossed high advisory threshold.",
        severity=EventSeverity.WARNING,
        audit=True,
        review=True,
        flags=[
            SafetyFlag.NO_CUSTODY,
            SafetyFlag.ADVISORY_ONLY,
            SafetyFlag.OPERATOR_REVIEW_REQUIRED,
        ],
    ),
    BastionEventType.TREASURY_REQUEST_CREATED: _metadata(
        BastionEventType.TREASURY_REQUEST_CREATED,
        EventDomain.TREASURY,
        "Treasury request was created.",
        audit=True,
        flags=[SafetyFlag.NO_CUSTODY, SafetyFlag.NO_AUTO_EXECUTION],
    ),
    BastionEventType.TREASURY_POLICY_FAILED: _metadata(
        BastionEventType.TREASURY_POLICY_FAILED,
        EventDomain.TREASURY,
        "Treasury policy check failed.",
        severity=EventSeverity.WARNING,
        audit=True,
        review=True,
        flags=NO_AUTO_FLAGS,
    ),
    BastionEventType.TREASURY_APPROVAL_REQUIRED: _metadata(
        BastionEventType.TREASURY_APPROVAL_REQUIRED,
        EventDomain.TREASURY,
        "Treasury request requires approval.",
        severity=EventSeverity.WARNING,
        audit=True,
        review=True,
        flags=NO_AUTO_FLAGS,
    ),
    BastionEventType.TREASURY_REQUEST_APPROVED: _metadata(
        BastionEventType.TREASURY_REQUEST_APPROVED,
        EventDomain.TREASURY,
        "Treasury request was approved by operator workflow.",
        audit=True,
        review=True,
        flags=NO_AUTO_FLAGS,
    ),
    BastionEventType.TREASURY_REQUEST_REJECTED: _metadata(
        BastionEventType.TREASURY_REQUEST_REJECTED,
        EventDomain.TREASURY,
        "Treasury request was rejected by operator workflow.",
        audit=True,
        review=True,
        flags=NO_AUTO_FLAGS,
    ),
    BastionEventType.POLICY_EXECUTION_FAILED: _metadata(
        BastionEventType.POLICY_EXECUTION_FAILED,
        EventDomain.POLICY,
        "Policy execution failed.",
        severity=EventSeverity.WARNING,
        audit=True,
        flags=[SafetyFlag.NO_AUTO_EXECUTION],
    ),
    BastionEventType.POLICY_WARNING_CREATED: _metadata(
        BastionEventType.POLICY_WARNING_CREATED,
        EventDomain.POLICY,
        "Policy warning was created.",
        severity=EventSeverity.WARNING,
        audit=True,
        flags=[SafetyFlag.NO_AUTO_EXECUTION],
    ),
    BastionEventType.POLICY_EVALUATION_COMPLETED: _metadata(
        BastionEventType.POLICY_EVALUATION_COMPLETED,
        EventDomain.POLICY,
        "Policy evaluation completed.",
        audit=True,
        flags=[SafetyFlag.NO_AUTO_EXECUTION],
    ),
    BastionEventType.MARKET_REGIME_CHANGED: _metadata(
        BastionEventType.MARKET_REGIME_CHANGED,
        EventDomain.MARKET,
        "Market regime classification changed.",
        websocket=True,
        flags=MARKET_FLAGS,
    ),
    BastionEventType.MARKET_CANDLE_ATTRIBUTED: _metadata(
        BastionEventType.MARKET_CANDLE_ATTRIBUTED,
        EventDomain.MARKET,
        "Market candle attribution was produced.",
        websocket=True,
        audit=True,
        flags=MARKET_FLAGS + [SafetyFlag.HISTORICAL_SIMILARITY_NOT_PREDICTION],
    ),
    BastionEventType.MARKET_PRICE_TICK_OBSERVED: _metadata(
        BastionEventType.MARKET_PRICE_TICK_OBSERVED,
        EventDomain.MARKET,
        "Market price tick was observed.",
        websocket=True,
        public_safe=True,
        flags=[SafetyFlag.PUBLIC_DATA_ONLY, SafetyFlag.NOT_FINANCIAL_ADVICE],
    ),
    BastionEventType.MARKET_CANDLE_CLOSED: _metadata(
        BastionEventType.MARKET_CANDLE_CLOSED,
        EventDomain.MARKET,
        "Market candle closed.",
        websocket=True,
        public_safe=True,
        flags=[SafetyFlag.PUBLIC_DATA_ONLY, SafetyFlag.NOT_FINANCIAL_ADVICE],
    ),
    BastionEventType.EVIDENCE_PACKET_CREATED: _metadata(
        BastionEventType.EVIDENCE_PACKET_CREATED,
        EventDomain.EVIDENCE,
        "Evidence packet was created.",
        webhook=True,
        audit=True,
        flags=[SafetyFlag.ADVISORY_ONLY],
    ),
    BastionEventType.EVIDENCE_REPLAY_COMPLETED: _metadata(
        BastionEventType.EVIDENCE_REPLAY_COMPLETED,
        EventDomain.EVIDENCE,
        "Evidence replay completed.",
        audit=True,
        flags=[SafetyFlag.ADVISORY_ONLY],
    ),
    BastionEventType.EVIDENCE_REPLAY_FAILED: _metadata(
        BastionEventType.EVIDENCE_REPLAY_FAILED,
        EventDomain.EVIDENCE,
        "Evidence replay failed.",
        severity=EventSeverity.WARNING,
        audit=True,
        flags=[SafetyFlag.ADVISORY_ONLY, SafetyFlag.DEGRADED_DATA_VISIBLE],
    ),
    BastionEventType.PROVIDER_DEGRADED: _metadata(
        BastionEventType.PROVIDER_DEGRADED,
        EventDomain.PROVIDER,
        "Provider entered degraded state.",
        severity=EventSeverity.WARNING,
        webhook=True,
        websocket=True,
        audit=True,
        public_safe=True,
        flags=PROVIDER_FLAGS,
    ),
    BastionEventType.PROVIDER_RECOVERED: _metadata(
        BastionEventType.PROVIDER_RECOVERED,
        EventDomain.PROVIDER,
        "Provider recovered from degraded state.",
        webhook=True,
        websocket=True,
        audit=True,
        public_safe=True,
        flags=[SafetyFlag.DEGRADED_DATA_VISIBLE],
    ),
    BastionEventType.PIPELINE_LAG_HIGH: _metadata(
        BastionEventType.PIPELINE_LAG_HIGH,
        EventDomain.OBSERVABILITY,
        "Pipeline lag crossed high threshold.",
        severity=EventSeverity.WARNING,
        webhook=True,
        websocket=True,
        audit=True,
        flags=[SafetyFlag.DEGRADED_DATA_VISIBLE, SafetyFlag.STALE_DATA_VISIBLE],
    ),
    BastionEventType.JOB_FAILED: _metadata(
        BastionEventType.JOB_FAILED,
        EventDomain.OBSERVABILITY,
        "Background job failed.",
        severity=EventSeverity.WARNING,
        webhook=True,
        audit=True,
        flags=[SafetyFlag.DEGRADED_DATA_VISIBLE],
    ),
    BastionEventType.SYSTEM_DEGRADED_MODE_ENTERED: _metadata(
        BastionEventType.SYSTEM_DEGRADED_MODE_ENTERED,
        EventDomain.SYSTEM,
        "System entered degraded mode.",
        severity=EventSeverity.WARNING,
        webhook=True,
        websocket=True,
        audit=True,
        public_safe=True,
        flags=[SafetyFlag.DEGRADED_DATA_VISIBLE],
    ),
    BastionEventType.SYSTEM_DEGRADED_MODE_EXITED: _metadata(
        BastionEventType.SYSTEM_DEGRADED_MODE_EXITED,
        EventDomain.SYSTEM,
        "System exited degraded mode.",
        webhook=True,
        websocket=True,
        audit=True,
        public_safe=True,
        flags=[SafetyFlag.DEGRADED_DATA_VISIBLE],
    ),
    BastionEventType.SYSTEM_RUNTIME_WARNING_CREATED: _metadata(
        BastionEventType.SYSTEM_RUNTIME_WARNING_CREATED,
        EventDomain.SYSTEM,
        "System runtime warning was created.",
        severity=EventSeverity.WARNING,
        webhook=True,
        websocket=True,
        audit=True,
        flags=[SafetyFlag.DEGRADED_DATA_VISIBLE],
    ),
}


def event_metadata(event_type: BastionEventType) -> EventMetadata:
    return EVENT_REGISTRY[event_type]
