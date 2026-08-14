from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict


class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class IncidentSeverity(str, Enum):
    MAJOR = "MAJOR"
    CRITICAL = "CRITICAL"


class IncidentTransitionType(str, Enum):
    OPENED = "OPENED"
    UPDATED = "UPDATED"
    RESOLVED = "RESOLVED"


class IncidentTransitionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    transition: IncidentTransitionType
    status: IncidentStatus
    severity: IncidentSeverity
    observed_at: datetime
    source: str
    summary: str


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    incident_id: str
    detector_id: str
    kind: str
    status: IncidentStatus
    severity: IncidentSeverity
    affected_target: str
    summary: str
    source: str
    limitations: str
    opened_at: datetime
    updated_at: datetime
    resolved_at: datetime | None


class IncidentDetailOut(IncidentOut):
    history: list[IncidentTransitionOut]


class SLOUnit(str, Enum):
    RATIO = "ratio"


class SLOComparison(str, Enum):
    AT_LEAST = "AT_LEAST"
    AT_MOST = "AT_MOST"


class SLOStatus(str, Enum):
    WITHIN_TARGET = "WITHIN_TARGET"
    BREACHED = "BREACHED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNAVAILABLE = "UNAVAILABLE"


class OperationsSLOOut(BaseModel):
    slo_id: str
    title: str
    service: str
    indicator_id: str
    target: Decimal
    current: Decimal | None
    unit: SLOUnit
    comparison: SLOComparison
    window_seconds: int
    status: SLOStatus
    sample_count: int
    observed_at: datetime
    source: str
    limitations: str
    error_budget_remaining: Decimal | None = None
    error_budget_consumed: Decimal | None = None
