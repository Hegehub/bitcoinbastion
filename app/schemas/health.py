from datetime import datetime
from pydantic import BaseModel, Field


class HealthOut(BaseModel):
    status: str
    app: str
    details: dict[str, str] = Field(default_factory=dict)


class DegradedComponentOut(BaseModel):
    severity: str
    affected_component: str
    started_at: datetime
    recommendation: str
    automatic_fallback_used: bool = False
    operator_attention_required: bool = True


class ProviderHealthSnapshotOut(BaseModel):
    provider_name: str
    provider_type: str
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    failure_count: int = 0
    consecutive_failures: int = 0
    avg_latency_ms: float | None = None
    provider_confidence: float = 1.0
    backoff_until: datetime | None = None
    health_state: str = "healthy"


class BackgroundJobHealthOut(BaseModel):
    job_name: str
    last_start_at: datetime | None = None
    last_finish_at: datetime | None = None
    duration_ms: int | None = None
    success: bool = True
    failure_reason: str = ""
    retry_count: int = 0
    next_scheduled_at: datetime | None = None
    worker_name: str = "unknown"
    health_state: str = "healthy"


class TelegramHealthOut(BaseModel):
    health_state: str = "healthy"
    last_publish_success: datetime | None = None
    last_publish_failure: datetime | None = None
    pending_queue_size: int = 0
    delivery_failures: int = 0
    average_delivery_latency: float = 0.0


class RuntimeStatusOut(BaseModel):
    system_state: str
    provider_state: str
    job_state: str
    signal_pipeline_state: str
    evidence_pipeline_state: str
    telegram_state: str
    fallback_active: bool = False
    operator_attention_required: bool = False
    queue_depth: int = 0
    last_success: datetime | None = None
    degraded_components: list[DegradedComponentOut] = Field(default_factory=list)
    provider_health: list[ProviderHealthSnapshotOut] = Field(default_factory=list)
    job_health: list[BackgroundJobHealthOut] = Field(default_factory=list)
    telegram_health: TelegramHealthOut = Field(default_factory=TelegramHealthOut)


class SystemHealthOut(BaseModel):
    system_health: str
    runtime_status: RuntimeStatusOut
    provider_health: list[ProviderHealthSnapshotOut]
    job_health: list[BackgroundJobHealthOut]
    degraded_components: list[DegradedComponentOut]
    recovery_events: list[dict[str, object]] = Field(default_factory=list)
    queue_depth: int = 0
    last_success: datetime | None = None


class MetricsStatusOut(BaseModel):
    prometheus_enabled: bool = True
    endpoint: str = "/metrics"
    bounded_labels: list[str] = Field(default_factory=list)
    registered_metrics: list[str] = Field(default_factory=list)


class DependencyHealthOut(BaseModel):
    name: str
    status: str
    latency_ms: float = 0.0
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    provider_confidence: float = 1.0
    degraded_reason: str = ""


class IntelligenceHealthOut(BaseModel):
    status: str
    provider_confidence: float
    degraded_state: bool
    last_success: datetime | None = None
    last_failure: datetime | None = None
    operational_limitations: list[str] = Field(default_factory=list)


class OperationsHealthOut(BaseModel):
    status: str
    dependencies: list[DependencyHealthOut]
    degraded_state: bool
    last_success: datetime | None = None
    last_failure: datetime | None = None
    operational_limitations: list[str] = Field(default_factory=list)
