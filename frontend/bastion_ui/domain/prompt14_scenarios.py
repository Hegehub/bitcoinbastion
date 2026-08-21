from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from bastion_ui.domain.provenance import ProvenanceState


class ProofPacketScenarioStatus(StrEnum):
    LOADING = "loading"
    UNAVAILABLE = "unavailable"
    EMPTY_EVIDENCE = "empty_evidence"
    PARTIAL_EVIDENCE = "partial_evidence"
    SOURCE_UNAVAILABLE = "source_unavailable"
    INTEGRITY_MISMATCH = "integrity_mismatch"
    NOT_VERIFIED = "not_verified"
    HISTORICAL_UNAVAILABLE = "historical_unavailable"
    PRIVACY_REDACTED = "privacy_redacted"


class ProofPacketScenario(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    status: ProofPacketScenarioStatus
    provenance: ProvenanceState = ProvenanceState.DEMO_FIXTURE


PROMPT14_SCENARIOS = tuple(
    ProofPacketScenario(id=f"proof_packet_{status.value}", status=status)
    for status in ProofPacketScenarioStatus
)
