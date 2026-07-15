from __future__ import annotations

from dataclasses import dataclass

INVALID_REPORT_ID_MESSAGE = "Invalid Trace report id. Open a report from a trusted Trace link."
SUSPICIOUS_REPORT_ID_MARKERS = ("../", "..\\", "<script", "javascript:", "file:", "data:")


@dataclass(frozen=True)
class ReportIdValidationResult:
    ok: bool
    report_id: str = ""
    error: str = ""


def validate_report_id(value: str) -> ReportIdValidationResult:
    normalized = value.strip()
    if not normalized:
        return ReportIdValidationResult(False, error=INVALID_REPORT_ID_MESSAGE)
    lowered = normalized.lower()
    if any(marker in lowered for marker in SUSPICIOUS_REPORT_ID_MARKERS):
        return ReportIdValidationResult(False, error=INVALID_REPORT_ID_MESSAGE)
    if len(normalized) > 128:
        return ReportIdValidationResult(False, error=INVALID_REPORT_ID_MESSAGE)
    return ReportIdValidationResult(True, report_id=normalized)
