from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.health import DegradedComponentOut, DependencyHealthOut, ProviderHealthSnapshotOut, RuntimeStatusOut


class OperationsDrillOut(BaseModel):
    drill_id: str
    drill_type: str
    started_at: datetime
    finished_at: datetime | None = None
    success: bool = False
    operator: str = "system"
    notes: str = ""
    artifact_refs: list[str] = Field(default_factory=list)


class OperationsMetricsSummaryOut(BaseModel):
    api_availability_status: str = "unknown"
    background_job_success_status: str = "unknown"
    provider_availability_status: str = "unknown"
    signal_generation_latency_status: str = "unknown"
    evidence_generation_latency_status: str = "unknown"
    replay_latency_status: str = "unknown"
    degraded_state: bool = False
    operational_limitations: list[str] = Field(default_factory=list)


class OperationsRunbookOut(BaseModel):
    slug: str
    title: str
    path: str
    failure_modes: list[str] = Field(default_factory=list)


class AlertSummaryOut(BaseModel):
    critical: int = 0
    warning: int = 0
    degraded_components: list[DegradedComponentOut] = Field(default_factory=list)


class OperationsStatusOut(BaseModel):
    platform_status: RuntimeStatusOut
    dependency_status: list[DependencyHealthOut]
    provider_status: list[ProviderHealthSnapshotOut]
    operations_timeline: list[OperationsDrillOut] = Field(default_factory=list)
    recovery_drills: list[OperationsDrillOut] = Field(default_factory=list)
    system_health: str
    alert_summary: AlertSummaryOut
    operational_limitations: list[str] = Field(default_factory=list)


class OperationalProviderStatusOut(BaseModel):
    provider_name: str
    provider_type: str
    status: str
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    latency_ms: float | None = None
    failure_count: int = 0
    provider_confidence: float = 0.0
    backoff_until: datetime | None = None
    last_error_sanitized: str = ""


class OperationalHealthOut(BaseModel):
    system_status: str
    provider_status: list[OperationalProviderStatusOut] = Field(default_factory=list)
    scheduler_status: str
    timeline_status: str
    evidence_status: str
    signal_queue_status: str
    last_backup: datetime | None = None
    last_restore_test: datetime | None = None
    last_integrity_scan: datetime | None = None
    readiness_status: str
    degraded_state_visible: bool = True
    backup_verified: bool = False
    restore_verified: bool = False
    integrity_verified: bool = False
    operator_visible: bool = True
    operational_limitations: list[str] = Field(default_factory=list)


class BackupValidationOut(BaseModel):
    backup_id: str
    started_at: datetime
    finished_at: datetime | None = None
    success: bool
    objects_checked: int
    integrity_verified: bool
    limitations: list[str] = Field(default_factory=list)


class RecoveryValidationOut(BaseModel):
    recovery_id: str
    validation_type: str
    started_at: datetime
    finished_at: datetime | None = None
    success: bool
    deterministic_rebuild_verified: bool
    integrity_verified: bool
    replay_types: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
