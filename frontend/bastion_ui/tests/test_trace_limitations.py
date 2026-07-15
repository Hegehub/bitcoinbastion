from __future__ import annotations

from bastion_ui.components.evidence.evidence_limitations_card import EVIDENCE_LIMITATIONS
from bastion_ui.components.trace.trace_limitations_card import TRACE_REPORT_LIMITATIONS
from bastion_ui.security.safety_copy import TRACE_PUBLIC_SAFETY_COPY


def test_limitations_copy_covers_trace_and_evidence_boundaries() -> None:
    text = (
        " ".join(TRACE_REPORT_LIMITATIONS + EVIDENCE_LIMITATIONS) + " " + TRACE_PUBLIC_SAFETY_COPY
    )
    for phrase in (
        "advisory-only",
        "not legal verification",
        "not Bitcoin consensus proof",
        "No custody",
        "Public Bitcoin addresses only",
        "Risk bands are not legal labels",
        "not financial advice",
    ):
        assert phrase in text
