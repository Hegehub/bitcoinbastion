from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FlexibleModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class PublicStatus(FlexibleModel):
    status: str | None = None
    degraded: bool | None = None
    stale: bool | None = None
    message: str | None = None


class PublicRoadmap(FlexibleModel):
    items: list[dict[str, Any]] | None = None


class PublicFeature(FlexibleModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None


class ApiResult(FlexibleModel):
    ok: bool
    data: dict[str, Any] | list[Any] | None = None
    error: str | None = None
    status_code: int | None = None
    degraded: bool = False


class TraceLiteResult(FlexibleModel):
    address: str
    report_id: str | None = None
    risk_band: str | None = None
    confidence: float | None = None
    summary: str | None = None
    provider_count: int | None = None
    source_count: int | None = None
    degraded: bool = False
    limitations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    generated_at: str | None = None


class TraceReportSummary(FlexibleModel):
    report_id: str | None = None
    summary: str | None = None
    confidence: str | None = None


class TraceEvidenceSummary(FlexibleModel):
    report_id: str | None = None
    evidence_count: int | None = None
    items: list[dict[str, Any]] | None = None


class EvidencePacketSummary(FlexibleModel):
    packet_id: str | None = None
    title: str | None = None
    sources: list[dict[str, Any]] | None = None


class ProviderHealthSummary(FlexibleModel):
    status: str | None = None
    degraded: bool | None = None
    providers: list[dict[str, Any]] | None = None


class MarketDashboardSummary(FlexibleModel):
    status: str | None = None
    stale: bool | None = None
    panels: list[dict[str, Any]] | None = None


class ConsoleModuleSummary(FlexibleModel):
    module: str | None = None
    status: str | None = None
    degraded: bool | None = None
