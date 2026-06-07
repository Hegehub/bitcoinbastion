from enum import StrEnum


class EventDomain(StrEnum):
    NEWS = "news"
    EVENT = "event"
    SIGNAL = "signal"
    ONCHAIN = "onchain"
    TRACE = "trace"
    WALLET = "wallet"
    TREASURY = "treasury"
    POLICY = "policy"
    MARKET = "market"
    OBSERVABILITY = "observability"
    PROVIDER = "provider"
    EVIDENCE = "evidence"
    SYSTEM = "system"


class BastionEventType(StrEnum):
    NEWS_ARTICLE_CREATED = "news.article.created"
    NEWS_ARTICLE_SCORED = "news.article.scored"
    NEWS_EVENT_CREATED = "news.event.created"
    NEWS_EVENT_HIGH_IMPACT = "news.event.high_impact"

    SIGNAL_CREATED = "signal.created"
    SIGNAL_PUBLISHED = "signal.published"
    SIGNAL_SUPPRESSED = "signal.suppressed"
    SIGNAL_OPERATOR_REVIEW_REQUIRED = "signal.operator_review_required"

    ONCHAIN_LARGE_TRANSFER = "onchain.large_transfer"
    ONCHAIN_WATCHLIST_HIT = "onchain.watchlist_hit"
    ONCHAIN_FEE_SPIKE = "onchain.fee_spike"
    ONCHAIN_MEMPOOL_PRESSURE = "onchain.mempool_pressure"

    TRACE_REPORT_CREATED = "trace.report.created"
    TRACE_RISK_BAND_CHANGED = "trace.risk_band.changed"
    TRACE_BATCH_COMPLETED = "trace.batch.completed"
    TRACE_SOURCE_DISAGREEMENT_DETECTED = "trace.source_disagreement.detected"
    TRACE_TREASURY_DESTINATION_CHECK_CREATED = "trace.treasury_destination_check.created"

    WALLET_HEALTH_GENERATED = "wallet.health.generated"
    WALLET_PRIVACY_RISK_HIGH = "wallet.privacy_risk.high"

    TREASURY_REQUEST_CREATED = "treasury.request.created"
    TREASURY_POLICY_FAILED = "treasury.policy.failed"
    TREASURY_APPROVAL_REQUIRED = "treasury.approval.required"
    TREASURY_REQUEST_APPROVED = "treasury.request.approved"
    TREASURY_REQUEST_REJECTED = "treasury.request.rejected"

    POLICY_EXECUTION_FAILED = "policy.execution.failed"
    POLICY_WARNING_CREATED = "policy.warning.created"
    POLICY_EVALUATION_COMPLETED = "policy.evaluation.completed"

    MARKET_REGIME_CHANGED = "market.regime.changed"
    MARKET_CANDLE_ATTRIBUTED = "market.candle.attributed"
    MARKET_PRICE_TICK_OBSERVED = "market.price_tick.observed"
    MARKET_CANDLE_CLOSED = "market.candle.closed"

    EVIDENCE_PACKET_CREATED = "evidence.packet.created"
    EVIDENCE_REPLAY_COMPLETED = "evidence.replay.completed"
    EVIDENCE_REPLAY_FAILED = "evidence.replay.failed"

    PROVIDER_DEGRADED = "provider.degraded"
    PROVIDER_RECOVERED = "provider.recovered"
    PIPELINE_LAG_HIGH = "pipeline.lag.high"
    JOB_FAILED = "job.failed"

    SYSTEM_DEGRADED_MODE_ENTERED = "system.degraded_mode.entered"
    SYSTEM_DEGRADED_MODE_EXITED = "system.degraded_mode.exited"
    SYSTEM_RUNTIME_WARNING_CREATED = "system.runtime_warning.created"


class ActorType(StrEnum):
    SYSTEM = "system"
    OPERATOR = "operator"
    API_CLIENT = "api_client"
    WORKER = "worker"
    UNKNOWN = "unknown"


class EventVisibility(StrEnum):
    INTERNAL = "internal"
    PUBLIC = "public"
    RESTRICTED = "restricted"


class EventSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
