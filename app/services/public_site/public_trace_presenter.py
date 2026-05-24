from app.db.models.bastion_trace import TraceReport
from app.schemas.public_site import PublicTraceSummary
from app.services.public_site.public_safety import public_warnings


_DEF = {
    "UNKNOWN": "Insufficient information",
    "LOW": "No strong risk signal found",
    "MEDIUM": "Caution",
    "HIGH": "Manual review recommended",
    "CRITICAL": "Manual review recommended",
}


def present_trace_summary(report: TraceReport) -> PublicTraceSummary:
    band = report.trace_band
    return PublicTraceSummary(
        report_id=report.id,
        band=band,
        risk_summary=_DEF.get(band, "Insufficient information"),
        privacy_summary="Unknown privacy exposure",
        origin_summary="Source-limited origin hints",
        confidence_summary="Medium confidence" if report.confidence >= 0.5 else "Low confidence",
        manual_review_recommended=band in {"MEDIUM", "HIGH", "CRITICAL"},
        top_reasons=[],
        limitations=["Public APIs do not expose internal evidence chains by default."],
        safety_warnings=public_warnings(),
        created_at=report.created_at,
    )
