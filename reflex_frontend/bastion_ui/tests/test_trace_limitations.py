from __future__ import annotations

from bastion_ui.components.evidence.evidence_limitations_card import EVIDENCE_LIMITATIONS
from bastion_ui.components.trace.trace_limitations_card import TRACE_REPORT_LIMITATIONS


def test_limitations_copy_covers_required_evidence_boundaries() -> None:
    combined = "\n".join(EVIDENCE_LIMITATIONS + TRACE_REPORT_LIMITATIONS)
    required = (
        "Trace is advisory-only.",
        "Provider data may be stale or incomplete.",
        "Risk bands are not legal labels.",
        "A report is not a Bitcoin consensus proof.",
        "A report is not financial advice.",
        "Operators must review high-impact decisions manually.",
    )
    for phrase in required:
        assert phrase in combined
