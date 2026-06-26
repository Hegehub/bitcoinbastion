from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from app.db.models.time_utils import utcnow


class MetricUsageEventType(StrEnum):
    METRIC_QUERY = "metric.query"
    API_REQUEST = "api.request"
    API_DENIED = "api.denied"
    QUOTA_CONSUMED = "quota.consumed"
    QUOTA_EXCEEDED = "quota.exceeded"
    ACCESS_INTEGRITY_UPDATED = "access.integrity.updated"
    SIGNAL_SCORE_RECORDED = "signal.score.recorded"
    WEBHOOK_DELIVERY = "webhook.delivery"
    WEBSOCKET_MESSAGE = "websocket.message"
    MCP_TOOL_CALL = "mcp.tool_call"
    SDK_REQUEST = "sdk.request"


class MetricUsageDecision(StrEnum):
    ALLOWED = "allowed"
    DENIED = "denied"
    DEGRADED = "degraded"
    CACHED = "cached"
    SKIPPED = "skipped"
    QUOTA_EXCEEDED = "quota_exceeded"
    UPGRADE_REQUIRED = "upgrade_required"
    POLICY_DENIED = "policy_denied"


@dataclass(frozen=True)
class MetricUsageEventCreate:
    event_type: str
    decision: str
    source_component: str
    recorded_at: datetime = field(default_factory=utcnow)
    metric_group: str | None = None
    metric_name: str | None = None
    feature_code: str | None = None
    endpoint: str | None = None
    method: str | None = None
    status_code: int | None = None
    credit_cost: int = 0
    request_count: int = 1
    pass_lookup_hash: str | None = None
    workspace_id_hash: str | None = None
    api_key_hash: str | None = None
    session_id_hash: str | None = None
    device_binding_id: str | None = None
    telegram_binding_id: str | None = None
    sdk_client: str | None = None
    client_kind: str | None = None
    risk_level: str | None = None
    policy_decision: str | None = None
    denial_reason: str | None = None
    metadata_json: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class MetricUsageSummary:
    total_requests: int
    total_credits: int
    allowed: int
    denied: int
    degraded: int
    cached: int
    skipped: int
    event_count: int
