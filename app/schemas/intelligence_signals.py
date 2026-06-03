from datetime import datetime
from pydantic import BaseModel

SIGNAL_LIMITATIONS = [
    "Correlation-based attribution, not proof of causation.",
    "Not financial advice.",
    "Operator policy controls publication visibility.",
]


class PublicSignalOut(BaseModel):
    signal_id: int
    signal_type: str
    title: str
    summary: str
    confidence_score: float
    evidence_refs: dict[str, object]
    limitations: list[str]
    correlation_not_causation: bool = True
    not_financial_advice: bool = True
    operator_reviewed: bool
    evidence_based: bool
    published_at: datetime | None
    status: str
    display_title: str
    display_summary: str
    badge_label: str
    badge_severity: str
    confidence_percent: int
    top_reasons: list[str]
    evidence_count: int
    limitations_count: int
    operator_status: str
    can_approve: bool
    can_reject: bool
    can_hold: bool
    can_mark_false_positive: bool


class DeliveryLogOut(BaseModel):
    id: int
    signal_candidate_id: int
    channel: str
    delivery_status: str
    target: str
    message_id: str | None = None
    error_type: str | None = None
    error_message_sanitized: str | None = None
    delivered_at: datetime | None = None
    created_at: datetime
