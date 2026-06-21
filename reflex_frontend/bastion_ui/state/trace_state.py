from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.security.address_validation import validate_public_bitcoin_address
from bastion_ui.services.errors import BastionFrontendError
from bastion_ui.services.trace_client import TraceApiClient

TRACE_API_ERROR_MESSAGE = "Trace is temporarily unavailable. Manual review recommended."


def normalize_trace_error(error: Exception) -> str:
    public_message = getattr(error, "public_message", None)
    if isinstance(public_message, str) and public_message:
        return public_message
    return TRACE_API_ERROR_MESSAGE


class TraceState(rx.State):
    address: str = ""
    normalized_address: str = ""
    loading: bool = False
    error: str = ""
    validation_error: str = ""
    result: dict[str, Any] = {}
    trace_lite_report_id: str = ""
    risk_band: str = "confidence unavailable"
    confidence_label: str = "Unavailable"
    provider_count_label: str = "Unavailable"
    source_count_label: str = "Unavailable"
    summary: str = "No backend summary was provided."
    limitations_label: str = "Limitations: advisory-only; manual review recommended."
    warnings_label: str = "Warnings: none reported by backend."
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
        self.normalized_address = validation.normalized_address
        self.validation_error = ""
        return True

    async def submit_address_check(self) -> None:
        self.clear_error()
        if not self.validate_address():
            return
        self.loading = True
        try:
            trace_result = await TraceApiClient().get_trace_lite(self.normalized_address)
            payload = trace_result.model_dump(mode="json")
            self.result = payload
            self.trace_lite_report_id = str(payload.get("report_id") or "")
            self.risk_band = str(payload.get("risk_band") or "confidence unavailable")
            confidence = payload.get("confidence")
            self.confidence_label = "Unavailable" if confidence is None else str(confidence)
            provider_count = payload.get("provider_count")
            self.provider_count_label = (
                "Unavailable" if provider_count is None else str(provider_count)
            )
            source_count = payload.get("source_count")
            self.source_count_label = "Unavailable" if source_count is None else str(source_count)
            self.summary = str(payload.get("summary") or "No backend summary was provided.")
            limitations = payload.get("limitations")
            self.limitations_label = (
                "Limitations: " + ", ".join(str(item) for item in limitations)
                if isinstance(limitations, list) and limitations
                else "Limitations: advisory-only; manual review recommended."
            )
            warnings = payload.get("warnings")
            self.warnings_label = (
                "Warnings: " + ", ".join(str(item) for item in warnings)
                if isinstance(warnings, list) and warnings
                else "Warnings: none reported by backend."
            )
            self.degraded = bool(payload.get("degraded"))
            self.last_checked_at = str(payload.get("generated_at") or "")
        except BastionFrontendError as exc:
            self.error = normalize_trace_error(exc)
        except Exception as exc:  # pragma: no cover - defensive UI safety net
            self.error = normalize_trace_error(exc)
        finally:
            self.loading = False

    def reset_result(self) -> None:
        self.address = ""
        self.normalized_address = ""
        self.loading = False
        self.error = ""
        self.validation_error = ""
        self.result = {}
        self.trace_lite_report_id = ""
        self.risk_band = "confidence unavailable"
        self.confidence_label = "Unavailable"
        self.provider_count_label = "Unavailable"
        self.source_count_label = "Unavailable"
        self.summary = "No backend summary was provided."
        self.limitations_label = "Limitations: advisory-only; manual review recommended."
        self.warnings_label = "Warnings: none reported by backend."
        self.degraded = False
        self.last_checked_at = ""

    def clear_error(self) -> None:
        self.error = ""

    def normalize_api_error(self, error: Exception) -> str:
        return normalize_trace_error(error)
