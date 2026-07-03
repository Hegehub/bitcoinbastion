from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.db.repositories.bastion_trace_repository import BastionTraceRepository
from app.schemas.base import ResponseEnvelope
from app.schemas.public_site import (
    PublicFeatureEntry,
    PublicLandingResponse,
    PublicRoadmapResponse,
    PublicStatsResponse,
    PublicStatusResponse,
    PublicTraceSummary,
)
from app.services.public_site.feature_catalog import list_features
from app.services.public_site.landing_service import get_landing
from app.services.public_site.public_stats_service import get_public_stats
from app.services.public_site.public_trace_presenter import present_trace_summary
from app.services.public_site.roadmap_service import get_roadmap
from app.services.public_site.status_service import get_public_status

router = APIRouter(prefix="/public", tags=["public"])


@router.get(
    "/landing",
    response_model=ResponseEnvelope[PublicLandingResponse],
    summary="Public landing payload",
    description="This endpoint is advisory-only.",
)
def public_landing() -> ResponseEnvelope[PublicLandingResponse]:
    return ResponseEnvelope(data=PublicLandingResponse.model_validate(get_landing()))


@router.get(
    "/status",
    response_model=ResponseEnvelope[PublicStatusResponse],
    summary="Public platform status",
)
def public_status() -> ResponseEnvelope[PublicStatusResponse]:
    return ResponseEnvelope(data=PublicStatusResponse.model_validate(get_public_status()))


@router.get(
    "/roadmap",
    response_model=ResponseEnvelope[PublicRoadmapResponse],
    summary="Public roadmap summary",
)
def public_roadmap() -> ResponseEnvelope[PublicRoadmapResponse]:
    return ResponseEnvelope(data=get_roadmap())


@router.get(
    "/stats", response_model=ResponseEnvelope[PublicStatsResponse], summary="Public-safe stats"
)
def public_stats() -> ResponseEnvelope[PublicStatsResponse]:
    return ResponseEnvelope(data=PublicStatsResponse.model_validate(get_public_stats()))


@router.get(
    "/features",
    response_model=ResponseEnvelope[list[PublicFeatureEntry]],
    summary="Feature catalog",
)
def public_features() -> ResponseEnvelope[list[PublicFeatureEntry]]:
    return ResponseEnvelope(data=list_features())


@router.get(
    "/trace/{report_id}/summary",
    response_model=ResponseEnvelope[PublicTraceSummary],
    summary="Public Trace summary",
)
def public_trace_summary(
    report_id: int, db: Session = Depends(db_session)
) -> ResponseEnvelope[PublicTraceSummary]:
    report = BastionTraceRepository(db).get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Trace report not found")
    return ResponseEnvelope(data=present_trace_summary(report))
