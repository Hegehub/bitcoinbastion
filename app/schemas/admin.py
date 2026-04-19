from datetime import datetime

from typing import Literal

from pydantic import BaseModel, Field


class JobRunOut(BaseModel):
    id: int
    task_name: str
    status: str
    correlation_id: str
    started_at: datetime
    finished_at: datetime | None
    error_message: str

    model_config = {"from_attributes": True}


class AuditLogOut(BaseModel):
    id: int
    actor_user_id: int | None
    action: str
    resource_type: str
    resource_id: str
    before_json: str
    after_json: str
    created_at: datetime

    model_config = {"from_attributes": True}


class JobRetryRequest(BaseModel):
    task_name: str = Field(min_length=3)


class JobRetryResponse(BaseModel):
    task_name: str
    task_id: str


class RecoveryIssueOut(BaseModel):
    issue_type: str
    reference: str
    occurred_at: datetime | None
    detail: str


class RecoveryHotspotOut(BaseModel):
    issue_type: str
    reference: str
    failures_24h: int


class RecoveryDrillOut(BaseModel):
    drill_code: str
    title: str
    priority: Literal["low", "medium", "high"]
    target_reference: str
    run_within_hours: int
    automation_ready: bool


class RecoveryCheckOut(BaseModel):
    ok: bool
    severity: Literal["ok", "warning", "critical"]
    failed_jobs_24h: int
    failed_deliveries_24h: int
    issues: list[RecoveryIssueOut]
    hotspots: list[RecoveryHotspotOut]
    drills: list[RecoveryDrillOut]
    recommended_actions: list[str]
