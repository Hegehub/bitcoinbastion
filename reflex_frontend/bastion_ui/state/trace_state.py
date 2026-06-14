from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.security.address_validation import validate_public_bitcoin_address
from bastion_ui.services.api_client import normalize_api_error
from bastion_ui.services.trace_client import (
    get_counterparty_lens,
    get_origin_passport,
    get_policy_facts,
    get_privacy_shield,
    get_provider_disagreement,
    get_public_trace_summary,
    get_trace_evidence,
    get_trace_lite,
    get_trace_report,
)

PANEL_UNAVAILABLE = "This panel is temporarily unavailable. The Trace report remains advisory-only and may be incomplete."


class TraceState(rx.State):
    address: str = ""
    loading: bool = False
    error: str = ""
    trace_report_id: str = ""
    summary: dict[str, Any] = {}
    report: dict[str, Any] = {}
    evidence: list[dict[str, Any]] = []
    privacy: dict[str, Any] = {}
    origin: dict[str, Any] = {}
    provider_disagreement: dict[str, Any] = {}
    counterparty: dict[str, Any] = {}
    policy_facts: dict[str, Any] = {}

    def set_address(self, value: str) -> None:
        self.address = value

    async def submit_address_check(self) -> None:
        valid, message = validate_public_bitcoin_address(self.address)
        if not valid:
            self.error = message or "Input must be a public Bitcoin address."
            return
        self.loading = True
        self.error = ""
        try:
            self.summary = await get_trace_lite(self.address.strip())
            self.trace_report_id = str(self.summary.get("report_id", ""))
        except Exception as exc:
            self.error = normalize_api_error(exc)
        finally:
            self.loading = False

    async def load_report(self, trace_report_id: str) -> None:
        self.loading = True
        self.error = ""
        self.trace_report_id = trace_report_id
        try:
            self.summary = await get_public_trace_summary(trace_report_id)
            self.report = await get_trace_report(trace_report_id)
            self.evidence = await get_trace_evidence(trace_report_id)
            self.privacy = await self._optional_panel(get_privacy_shield, trace_report_id)
            self.origin = await self._optional_panel(get_origin_passport, trace_report_id)
            self.provider_disagreement = await self._optional_panel(get_provider_disagreement, trace_report_id)
            self.counterparty = await self._optional_panel(get_counterparty_lens, trace_report_id)
            self.policy_facts = await self._optional_panel(get_policy_facts, trace_report_id)
        except Exception as exc:
            self.error = normalize_api_error(exc)
        finally:
            self.loading = False

    async def load_proof_packet(self, trace_report_id: str) -> None:
        self.loading = True
        self.error = ""
        self.trace_report_id = trace_report_id
        try:
            self.summary = await get_public_trace_summary(trace_report_id)
            self.evidence = await get_trace_evidence(trace_report_id)
        except Exception as exc:
            self.error = normalize_api_error(exc)
        finally:
            self.loading = False

    async def _optional_panel(self, loader: Any, trace_report_id: str) -> dict[str, Any]:
        try:
            result = await loader(trace_report_id)
            return result if isinstance(result, dict) else {"message": PANEL_UNAVAILABLE}
        except Exception:
            return {"message": PANEL_UNAVAILABLE}

    def clear_error(self) -> None:
        self.error = ""

    def reset_trace(self) -> None:
        self.address = ""
        self.loading = False
        self.error = ""
        self.trace_report_id = ""
        self.summary = {}
        self.report = {}
        self.evidence = []
        self.privacy = {}
        self.origin = {}
        self.provider_disagreement = {}
        self.counterparty = {}
        self.policy_facts = {}
