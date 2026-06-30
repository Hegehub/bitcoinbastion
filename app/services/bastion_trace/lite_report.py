from app.schemas.bastion_trace import LiteTraceReport, TraceReport
from app.services.bastion_trace.lite_explainer import (
    map_confidence_label,
    map_privacy_label,
    map_risk_label,
    map_status,
)
from app.services.bastion_trace.public_safety import default_warnings


class LiteTraceReportService:
    def from_trace_report(
        self, trace_report: TraceReport, privacy_band: str = "UNKNOWN"
    ) -> LiteTraceReport:
        risk_label = map_risk_label(trace_report.trace_band)
        status = map_status(trace_report.trace_band)
        summary = {
            "No strong risk signal found": "No strong risk signal was found.",
            "Caution": "Some caution signals were found.",
            "High caution": "High caution signals were found.",
            "Critical review required": "Critical review is required.",
            "Unknown": "Information is insufficient.",
        }[risk_label.value]
        next_step = {
            "Unknown": "Insufficient information. Do not rely on this alone for high-value activity.",
            "No strong risk signal found": "No strong risk signal was found. For high-value transfers, consider deeper review.",
            "Caution": "Use caution. Consider manual review before sending a significant amount.",
            "High caution": "Manual review is recommended before proceeding.",
            "Critical review required": "Do not proceed without senior/manual review.",
        }[risk_label.value]
        return LiteTraceReport(
            address=trace_report.address,
            chain=trace_report.chain,
            status_label=status,
            risk_label=risk_label,
            privacy_label=map_privacy_label(privacy_band),
            origin_label="Source-limited origin summary",
            confidence_label=map_confidence_label(trace_report.confidence),
            safe_to_send_advisory=(
                "INSUFFICIENT_INFORMATION"
                if trace_report.trace_band.value == "UNKNOWN"
                else "PROCEED_WITH_CAUTION"
            ),
            short_summary=summary,
            what_this_means="Advisory only. Uncertainty is explicitly preserved.",
            recommended_next_step=next_step,
            warnings=default_warnings(),
            limitations=trace_report.limitations,
            qr_payload=f"bitcoin:{trace_report.address}",
            clipboard_payload=f"bitcoin:{trace_report.address}",
            report_id=trace_report.id,
            created_at=trace_report.created_at,
        )
