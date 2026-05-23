from app.schemas.bastion_trace import TraceReasonCode

BASELINE_REASONS = [
    TraceReasonCode.ADVISORY_ONLY.value,
    TraceReasonCode.NOT_LEGAL_VERDICT.value,
    TraceReasonCode.NOT_CONSENSUS_PROOF.value,
    TraceReasonCode.NO_CUSTODY.value,
    TraceReasonCode.BASELINE_SCORING_ONLY.value,
]
