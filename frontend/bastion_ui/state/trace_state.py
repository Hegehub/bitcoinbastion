from __future__ import annotations

import secrets

import reflex as rx

from bastion_ui.domain.prompt12 import adapt_trace_submission
from bastion_ui.security.address_validation import validate_public_bitcoin_address
from bastion_ui.services.errors import BastionFrontendError
from bastion_ui.services.trace_client import TraceApiClient
from bastion_ui.topology import path_for

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
    submit_attempt_id: str = ""

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
            if not self.submit_attempt_id:
                self.submit_attempt_id = "trace-" + secrets.token_urlsafe(24)
            payload = await TraceApiClient().submit_trace(
                self.normalized_address, self.submit_attempt_id
            )
            result = adapt_trace_submission(payload)
            self.trace_lite_report_id = result.report_id
            self.summary = "Trace accepted by the authoritative backend."
            self.submit_attempt_id = ""
            return rx.redirect(path_for("trace.report", report_id=result.report_id))
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
        self.submit_attempt_id = ""

    def clear_error(self) -> None:
        self.error = ""

    def normalize_api_error(self, error: Exception) -> str:
        return normalize_trace_error(error)
