from __future__ import annotations

from datetime import UTC, datetime

import reflex as rx

from bastion_ui.security.address_validation import validate_public_bitcoin_address
from bastion_ui.services.errors import BastionApiError
from bastion_ui.services.trace_client import get_trace_lite

SAFE_TRACE_ERROR = "Unable to load Trace advisory result safely. Try again shortly."


class TraceState(rx.State):
    address: str = ""
    normalized_address: str = ""
    loading: bool = False
    error: str = ""
    validation_error: str = ""
    result: dict[str, str] = {}
    latest_report_id: str = ""
    degraded: bool = False
    last_checked_at: str = ""

    def set_address(self, value: str) -> None:
        self.address = value
        self.validation_error = ""

    def validate_address(self) -> bool:
        validation = validate_public_bitcoin_address(self.address)
        if not validation.ok:
            self.validation_error = validation.error
            self.normalized_address = ""
            return False
        self.normalized_address = validation.normalized
        self.validation_error = ""
        return True

    async def submit_address_check(self) -> None:
        self.clear_error()
        self.reset_result()
        if not self.validate_address():
            return
        self.loading = True
        try:
            trace_result = await get_trace_lite(self.normalized_address)
            self.latest_report_id = trace_result.report_id or ""
            self.degraded = trace_result.degraded
            self.result = {
                "address": trace_result.address,
                "risk_band": trace_result.risk_band or "unknown",
                "confidence": str(trace_result.confidence)
                if trace_result.confidence is not None
                else "unavailable",
                "provider_count": str(trace_result.provider_count)
                if trace_result.provider_count is not None
                else "unavailable",
                "source_count": str(trace_result.source_count)
                if trace_result.source_count is not None
                else "unavailable",
                "summary": trace_result.summary or "Advisory result available.",
                "limitations_text": "; ".join(trace_result.limitations)
                if trace_result.limitations
                else "Manual review recommended.",
            }
            self.last_checked_at = datetime.now(UTC).isoformat()
        except BastionApiError as exc:
            self.normalize_api_error(exc)
        except Exception:
            self.error = SAFE_TRACE_ERROR
        finally:
            self.loading = False

    def reset_result(self) -> None:
        self.result = {}
        self.latest_report_id = ""
        self.degraded = False
        self.last_checked_at = ""

    def clear_error(self) -> None:
        self.error = ""

    def normalize_api_error(self, error: Exception) -> None:
        if isinstance(error, BastionApiError):
            self.error = error.public_message
        else:
            self.error = SAFE_TRACE_ERROR
