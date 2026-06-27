from __future__ import annotations

from pathlib import Path

from bastion_ui.security import safety_copy

ROOT = Path(__file__).resolve().parents[1]
TRACE_FILES = (
    ROOT / "routes" / "trace.py",
    ROOT / "routes" / "trace_report.py",
    ROOT / "routes" / "proof_packet.py",
    ROOT / "components" / "trace" / "trace_limitations_card.py",
    ROOT / "components" / "trace" / "trace_safety_banner.py",
)


def _trace_text() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in TRACE_FILES).lower()


def test_trace_safety_copy_constants_are_complete() -> None:
    copy = safety_copy.TRACE_PUBLIC_SAFETY_COPY
    assert safety_copy.ADVISORY_ONLY in copy
    assert safety_copy.NOT_LEGAL_VERIFICATION in copy
    assert safety_copy.NOT_CONSENSUS_PROOF in copy
    assert safety_copy.NO_CUSTODY in copy
    assert safety_copy.PUBLIC_ADDRESSES_ONLY in copy
    assert safety_copy.NEVER_ENTER_SENSITIVE_MATERIAL in copy


def test_trace_pages_include_required_visible_safety_copy() -> None:
    text = _trace_text()
    assert "advisory-only" in text
    assert "not legal verification" in text
    assert "trace_public_safety_copy" in text
    assert safety_copy.NOT_CONSENSUS_PROOF == "Not Bitcoin consensus proof."
    assert safety_copy.NO_CUSTODY == "No custody."
    assert safety_copy.PUBLIC_ADDRESSES_ONLY == "Public Bitcoin addresses only."
    assert "seed phrases" in safety_copy.NEVER_ENTER_SENSITIVE_MATERIAL
    assert "private keys" in safety_copy.NEVER_ENTER_SENSITIVE_MATERIAL
    assert "wallet files" in safety_copy.NEVER_ENTER_SENSITIVE_MATERIAL
    assert "signing material" in safety_copy.NEVER_ENTER_SENSITIVE_MATERIAL


def test_trace_report_and_proof_packet_include_limitations() -> None:
    text = _trace_text()
    assert "limitations" in text
    assert "low confidence" in safety_copy.LOW_CONFIDENCE.lower()
    assert "degraded" in safety_copy.DEGRADED_DATA.lower()


def test_trace_copy_does_not_claim_legal_or_consensus_verdicts() -> None:
    text = _trace_text()
    assert "legal verdict" not in text
    assert "verified by bitcoin consensus" not in text
    assert "final legal" not in text
