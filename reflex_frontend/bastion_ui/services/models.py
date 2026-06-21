from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class FlexibleModel(BaseModel):
    """Permissive frontend DTO base; backend owns domain semantics."""

    model_config = ConfigDict(extra="allow")


class PublicStatus(FlexibleModel):
    status: str | None = None
    degraded: bool | None = None
    stale: bool | None = None
    message: str | None = None


class PublicRoadmap(FlexibleModel):
    items: list[dict[str, Any]] | None = None


class PublicFeature(FlexibleModel):
    key: str | None = None
    title: str | None = None
    description: str | None = None


class TraceLiteResult(FlexibleModel):
    address: str | None = None
    report_id: str | int | None = None
    status: str | None = None


class TraceReportSummary(FlexibleModel):
    report_id: str | int | None = None
    generated_at: str | None = None
    summary: str | None = None


class TraceEvidenceSummary(FlexibleModel):
    report_id: str | int | None = None
    evidence: list[dict[str, Any]] | None = None


class EvidencePacketSummary(FlexibleModel):
    packet_id: str | int | None = None
    title: str | None = None
    source_count: int | None = None


class ProviderHealthSummary(FlexibleModel):
    status: str | None = None
    providers: list[dict[str, Any]] | None = None
    degraded: bool | None = None
    stale: bool | None = None


class MarketDashboardSummary(FlexibleModel):
    status: str | None = None
    data: dict[str, Any] | None = None


class ConsoleModuleSummary(FlexibleModel):
    module: str | None = None
    status: str | None = None
    degraded: bool | None = None
    stale: bool | None = None
