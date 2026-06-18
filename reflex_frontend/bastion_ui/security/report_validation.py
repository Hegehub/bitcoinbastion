from __future__ import annotations

from dataclasses import dataclass

SUSPICIOUS_REPORT_ID_MARKERS = ("../", "..\\", "<script", "javascript:", "file:", "data:")
INVALID_REPORT_ID_MESSAGE = "Invalid Trace report identifier."


@dataclass(frozen=True)
class ReportIdValidationResult:
    ok: bool
    value: str = ""
    error: str | None = None


def validate_report_id(report_id: str) -> ReportIdValidationResult:
    value = report_id.strip()
    lowered = value.lower()
    if not value:
        return ReportIdValidationResult(False, error=INVALID_REPORT_ID_MESSAGE)
    if any(marker in lowered for marker in SUSPICIOUS_REPORT_ID_MARKERS):
        return ReportIdValidationResult(False, error=INVALID_REPORT_ID_MESSAGE)
    if len(value) > 128:
        return ReportIdValidationResult(False, error=INVALID_REPORT_ID_MESSAGE)
    return ReportIdValidationResult(True, value=value)
