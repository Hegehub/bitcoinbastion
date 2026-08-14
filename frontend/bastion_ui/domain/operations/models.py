from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from bastion_ui.domain.provenance import Provenance


class IntelligenceHealthViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    status: str
    degraded: bool
    provider_confidence: Decimal
    last_success: datetime | None
    last_failure: datetime | None
    limitations: tuple[str, ...] | None


class HealthViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    application: str
    status: str
    details: tuple[tuple[str, str], ...]
    provenance: Provenance


class ProviderViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str
    provider_type: str
    state: str
    last_success_at: datetime | None
    last_failure_at: datetime | None
    latency_ms: Decimal | None
    failure_count: int | None


class ProvidersViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    providers: tuple[ProviderViewModel, ...]
    provenance: Provenance


class StorageStoreViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str
    status: str
    role: str
    purpose: str
    latency_ms: Decimal | None


class StorageViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    status: str
    profile: str
    required_ok: bool
    critical_failures: int
    warnings: int
    degraded: bool
    degraded_reason: str | None
    degraded_impact: tuple[str, ...]
    stores: tuple[StorageStoreViewModel, ...]
    provenance: Provenance


class IncidentViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    incident_id: str
    severity: str
    status: str
    target: str
    summary: str
    source: str
    limitations: str
    opened_at: datetime
    updated_at: datetime
    resolved_at: datetime | None


class IncidentsViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    incidents: tuple[IncidentViewModel, ...]
    provenance: Provenance


class OperationsSLOViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    slo_id: str
    title: str
    service: str
    indicator: str
    target: Decimal
    current: Decimal | None
    unit: str
    comparison: str
    window_seconds: int
    status: str
    sample_count: int
    observed_at: datetime
    source: str
    limitations: str


class OperationsSLOListViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    objectives: tuple[OperationsSLOViewModel, ...]
    provenance: Provenance
