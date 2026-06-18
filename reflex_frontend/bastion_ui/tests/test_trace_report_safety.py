from __future__ import annotations

from pathlib import Path

from bastion_ui.components.trace.trace_safety_banner import TRACE_SAFETY_COPY

TRACE_DIR = Path(__file__).resolve().parents[1] / "components" / "trace"


def _trace_text() -> str:
    return "\n".join(path.read_text() for path in TRACE_DIR.glob("*.py"))


def test_trace_report_safety_copy_present() -> None:
    text = _trace_text() + TRACE_SAFETY_COPY
    required = (
        "Advisory-only.",
        "Not legal verification.",
        "Not Bitcoin consensus proof.",
        "No custody.",
        "Public Bitcoin addresses only.",
        "Never enter seed phrases, private keys, wallet files or signing material.",
    )
    for phrase in required:
        assert phrase in text


def test_trace_report_forbidden_wording_absent() -> None:
    text = _trace_text().lower()
    for phrase in (
        "clean address",
        "dirty address",
        "criminal address",
        "guaranteed safe",
        "approved payment",
        "verified illicit",
    ):
        assert phrase not in text
