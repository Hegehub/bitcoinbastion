"""Typed Feature-59/60 Prompt-13 development scenarios; never a production fallback."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from bastion_ui.domain.provenance import ProvenanceState


class TraceScenarioKind(StrEnum):
    TOPOLOGY_LOADING = "topology_loading"
    TOPOLOGY_EMPTY = "topology_empty"
    TOPOLOGY_PARTIAL = "topology_partial"
    TOPOLOGY_TRUNCATED = "topology_truncated"
    TOPOLOGY_MALFORMED = "topology_malformed"
    TOPOLOGY_UNAVAILABLE = "topology_unavailable"
    HISTORY_EMPTY = "history_empty"
    HISTORY_MISSING = "history_missing"
    HISTORY_LEGACY_UNAVAILABLE = "history_legacy_unavailable"
    HISTORY_BACKEND_UNAVAILABLE = "history_backend_unavailable"
    HISTORY_EXACT_A = "history_exact_a"
    HISTORY_EXACT_B = "history_exact_b"
    AGREEMENT = "agreement"
    DISAGREEMENT = "disagreement"
    INSUFFICIENT = "insufficient"
    NOT_COMPARABLE = "not_comparable"
    SOURCE_UNAVAILABLE = "source_unavailable"
    PRODUCER_FAILURE = "producer_failure"
    UNRESOLVED = "unresolved"
    RESOLVED = "resolved"
    PRIVACY_REDACTED = "privacy_redacted"


class TraceScenario(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    kind: TraceScenarioKind
    provenance: ProvenanceState = ProvenanceState.DEMO_FIXTURE


PROMPT13_SCENARIOS = tuple(TraceScenario(kind=kind) for kind in TraceScenarioKind)
