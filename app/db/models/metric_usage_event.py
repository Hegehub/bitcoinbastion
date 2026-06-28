from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Index, Integer, JSON, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class MetricUsageEvent(Base):
    __tablename__ = "metric_usage_events"
    __table_args__ = (
        Index("ix_metric_usage_recorded_at", "recorded_at"),
        Index("ix_metric_usage_group_recorded", "metric_group", "recorded_at"),
        Index("ix_metric_usage_name_recorded", "metric_name", "recorded_at"),
        Index("ix_metric_usage_pass_recorded", "pass_lookup_hash", "recorded_at"),
        Index("ix_metric_usage_workspace_recorded", "workspace_id_hash", "recorded_at"),
        Index("ix_metric_usage_api_key_recorded", "api_key_hash", "recorded_at"),
        Index("ix_metric_usage_session_recorded", "session_id_hash", "recorded_at"),
        Index("ix_metric_usage_source_recorded", "source_component", "recorded_at"),
        Index("ix_metric_usage_decision_recorded", "decision", "recorded_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    metric_group: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    metric_name: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    feature_code: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    endpoint: Mapped[str | None] = mapped_column(String(200), nullable=True)
    method: Mapped[str | None] = mapped_column(String(16), nullable=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    credit_cost: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    request_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    pass_lookup_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    workspace_id_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    api_key_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    session_id_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    device_binding_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    telegram_binding_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sdk_client: Mapped[str | None] = mapped_column(String(80), nullable=True)
    client_kind: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_component: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    risk_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    policy_decision: Mapped[str | None] = mapped_column(String(64), nullable=True)
    denial_reason: Mapped[str | None] = mapped_column(String(160), nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
