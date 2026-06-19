from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import reflex as rx

from bastion_ui.security.report_validation import validate_report_id
from bastion_ui.services.models import ApiResult
from bastion_ui.services.trace_client import (
    get_counterparty_lens_result,
    get_dust_radar_result,
    get_origin_passport_result,
    get_policy_facts_result,
    get_privacy_shield_result,
    get_proof_packet,
    get_provider_disagreement_result,
    get_public_trace_summary,
    get_source_summary_result,
    get_trace_evidence_result,
    get_trace_report_result,
    get_utxo_hygiene_result,
)

PanelLoader = Callable[[str], Awaitable[ApiResult]]


class TraceReportState(rx.State):
    current_trace_report_id: str = ""
    loading: bool = False
    error: str | None = None

    summary: dict[str, Any] | None = None
    report: dict[str, Any] | None = None
    evidence: dict[str, Any] | None = None
    privacy_shield: dict[str, Any] | None = None
    origin_passport: dict[str, Any] | None = None
    source_summary: dict[str, Any] | None = None
    provider_disagreement: dict[str, Any] | None = None
    utxo_hygiene: dict[str, Any] | None = None
    dust_radar: dict[str, Any] | None = None
    counterparty_lens: dict[str, Any] | None = None
    policy_facts: dict[str, Any] | None = None
    proof_packet: dict[str, Any] | None = None

    has_degraded_data: bool = False
    has_provider_disagreement: bool = False
    has_limited_evidence: bool = False
    proof_packet_available: bool = False

    def set_report_id(self, report_id: str) -> None:
        validation = validate_report_id(report_id)
        self.current_trace_report_id = validation.value if validation.ok else ""
        self.error = validation.error

    async def _load_panel(self, attr: str, loader: PanelLoader) -> None:
        result = await loader(self.current_trace_report_id)
        if result.ok and isinstance(result.data, dict):
            setattr(self, attr, result.data)
            self.has_degraded_data = self.has_degraded_data or result.degraded
            return
        setattr(self, attr, None)
        self.has_degraded_data = True
        if result.error:
            self.error = "Some Trace report panels could not be loaded."

    async def load_trace_summary(self) -> None:
        await self._load_panel("summary", get_public_trace_summary)

    async def load_trace_evidence(self) -> None:
        await self._load_panel("evidence", get_trace_evidence_result)
        self.has_limited_evidence = self.evidence is None

    async def load_trace_panels(self) -> None:
        panel_loaders: tuple[tuple[str, PanelLoader], ...] = (
            ("privacy_shield", get_privacy_shield_result),
            ("origin_passport", get_origin_passport_result),
            ("source_summary", get_source_summary_result),
            ("provider_disagreement", get_provider_disagreement_result),
            ("utxo_hygiene", get_utxo_hygiene_result),
            ("dust_radar", get_dust_radar_result),
            ("counterparty_lens", get_counterparty_lens_result),
            ("policy_facts", get_policy_facts_result),
        )
        for attr, loader in panel_loaders:
            await self._load_panel(attr, loader)
        self.has_provider_disagreement = self.provider_disagreement is not None

    async def load_trace_report(self) -> None:
        if not validate_report_id(self.current_trace_report_id).ok:
            self.error = "Invalid Trace report identifier."
            return
        self.loading = True
        self.error = None
        self.has_degraded_data = False
        await self._load_panel("report", get_trace_report_result)
        await self.load_trace_summary()
        await self.load_trace_evidence()
        await self.load_trace_panels()
        self.loading = False

    async def load_proof_packet(self) -> None:
        if not validate_report_id(self.current_trace_report_id).ok:
            self.error = "Invalid Trace report identifier."
            self.proof_packet_available = False
            return
        self.loading = True
        result = await get_proof_packet(self.current_trace_report_id)
        if result.ok and isinstance(result.data, dict):
            self.proof_packet_available = True
            self.proof_packet = result.data
        else:
            self.proof_packet_available = False
            self.proof_packet = None
        if not self.proof_packet_available:
            self.has_degraded_data = True
            self.error = result.error or "Proof packet is not available for this report."
        self.loading = False

    def clear_error(self) -> None:
        self.error = None

    def reset(self) -> None:
        self.current_trace_report_id = ""
        self.loading = False
        self.error = None
        self.summary = None
        self.report = None
        self.evidence = None
        self.privacy_shield = None
        self.origin_passport = None
        self.source_summary = None
        self.provider_disagreement = None
        self.utxo_hygiene = None
        self.dust_radar = None
        self.counterparty_lens = None
        self.policy_facts = None
        self.proof_packet = None
        self.has_degraded_data = False
        self.has_provider_disagreement = False
        self.has_limited_evidence = False
        self.proof_packet_available = False
