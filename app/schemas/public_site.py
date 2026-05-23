from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PublicFeatureStatus(str, Enum):
    IMPLEMENTED = "IMPLEMENTED"
    BASELINE = "BASELINE"
    PLACEHOLDER = "PLACEHOLDER"
    PLANNED = "PLANNED"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


class PublicFeatureAvailability(str, Enum):
    PUBLIC = "PUBLIC"
    PRO = "PRO"
    BUSINESS = "BUSINESS"
    ENTERPRISE = "ENTERPRISE"
    INTERNAL = "INTERNAL"


class PublicFeatureEntry(BaseModel):
    id: str
    name: str
    category: str
    summary: str
    status: PublicFeatureStatus
    availability: PublicFeatureAvailability
    safety_notes: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class PublicTraceSummary(BaseModel):
    report_id: int
    band: str
    risk_summary: str
    privacy_summary: str
    origin_summary: str
    confidence_summary: str
    manual_review_recommended: bool
    top_reasons: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    safety_warnings: list[str] = Field(default_factory=list)
    created_at: datetime | None = None


class PublicStatusResponse(BaseModel):
    platform_status: str
    trace_status: str
    production_calibrated: bool
    modules: dict[str, str]
    known_limitations: list[str] = Field(default_factory=list)
    last_update: datetime


class PublicRoadmapResponse(BaseModel):
    current_phase: str
    implemented: list[str] = Field(default_factory=list)
    baseline: list[str] = Field(default_factory=list)
    placeholder: list[str] = Field(default_factory=list)
    planned: list[str] = Field(default_factory=list)
    not_started: list[str] = Field(default_factory=list)


class PublicStatsResponse(BaseModel):
    reports_generated: int
    proof_packets_generated: int
    watchtower_entries: int
    runtime_events: int
    supported_modules: list[str]
    limitations: list[str] = Field(default_factory=list)


class PublicLandingResponse(BaseModel):
    platform_name: str
    platform_tagline: str
    modules: list[str]
    status_summary: dict[str, object]
    feature_catalog: list[PublicFeatureEntry]
    roadmap_summary: dict[str, object]
    safety_principles: list[str]
    production_readiness: dict[str, object]
    links: dict[str, str]
