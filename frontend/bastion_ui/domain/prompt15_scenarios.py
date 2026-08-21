from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from bastion_ui.domain.provenance import ProvenanceState


class EvidenceWorkflowScenarioKind(StrEnum):
    LINEAGE_COMPLETE = "lineage_complete"
    LINEAGE_PARTIAL = "lineage_partial"
    LINEAGE_TRUNCATED = "lineage_truncated"
    LINEAGE_UNAVAILABLE = "lineage_unavailable"
    BROKEN_REFERENCE = "broken_reference"
    LEGACY_UNAVAILABLE = "legacy_unavailable"
    REPLAYABLE = "replayable"
    NOT_REPLAYABLE = "not_replayable"
    REPLAY_MATCH = "replay_match"
    REPLAY_MISMATCH = "replay_mismatch"
    INPUTS_UNAVAILABLE = "inputs_unavailable"
    VERSION_UNAVAILABLE = "version_unavailable"
    EXECUTION_FAILED = "execution_failed"
    VERIFIED = "verified"
    VERIFICATION_FAILED = "verification_failed"
    VERIFICATION_NOT_RUN = "verification_not_run"
    VERIFICATION_UNAVAILABLE = "verification_unavailable"
    VERIFICATION_UNSUPPORTED = "verification_unsupported"
    MULTIPLE_SCOPES = "multiple_scopes"
    EXPORT_READY = "export_ready"
    EXPORT_UNAVAILABLE = "export_unavailable"
    EXPORT_FAILED = "export_failed"
    EXPORT_PRIVACY_REDACTED = "export_privacy_redacted"


class EvidenceWorkflowScenario(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    kind: EvidenceWorkflowScenarioKind
    provenance: ProvenanceState = ProvenanceState.DEMO_FIXTURE


PROMPT15_SCENARIOS = tuple(
    EvidenceWorkflowScenario(id=f"evidence_{kind.value}", kind=kind)
    for kind in EvidenceWorkflowScenarioKind
)
