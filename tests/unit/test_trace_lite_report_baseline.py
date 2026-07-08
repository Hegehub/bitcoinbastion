from app.schemas.bastion_trace import TraceBand, TraceReport
from app.services.bastion_trace.lite_report import LiteTraceReportService


def test_lite_mapping_unknown() -> None:
    t = TraceReport(
        address="1BoatSLRHtKNngkdXEeobR76b53LETtpyT", trace_band=TraceBand.UNKNOWN, limitations=[]
    )
    lite = LiteTraceReportService().from_trace_report(t)
    assert lite.status_label.value == "Insufficient information"


def test_lite_contains_payloads_and_warnings() -> None:
    t = TraceReport(
        address="bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kygt080",
        trace_band=TraceBand.LOW,
        limitations=[],
    )
    lite = LiteTraceReportService().from_trace_report(t)
    assert lite.qr_payload.startswith("bitcoin:")
    assert lite.clipboard_payload.startswith("bitcoin:")
    joined = " ".join(lite.warnings).lower()
    for bad in ["clean", "dirty", "criminal", "guaranteed", "approved", "safe"]:
        assert bad not in joined
