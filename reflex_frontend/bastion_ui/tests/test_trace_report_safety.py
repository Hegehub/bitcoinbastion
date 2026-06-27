from __future__ import annotations

import pytest

pytest.importorskip("reflex")

from pathlib import Path

from bastion_ui.components.trace.trace_limitations_card import TRACE_REPORT_LIMITATIONS
from bastion_ui.security.safety_copy import TRACE_PUBLIC_SAFETY_COPY

ROOT = Path(__file__).resolve().parents[1]


def test_trace_report_required_safety_copy_exists() -> None:
    text = TRACE_PUBLIC_SAFETY_COPY + " " + " ".join(TRACE_REPORT_LIMITATIONS)
    for phrase in (
        "Advisory-only.",
        "No custody.",
        "Not legal verification.",
        "Not Bitcoin consensus proof.",
        "Manual review may be required.",
    ):
        assert phrase in text


def test_trace_report_user_facing_code_avoids_forbidden_wording() -> None:
    forbidden = tuple(
        " ".join(parts)
        for parts in (
            ("clean", "address"),
            ("dirty", "address"),
            ("criminal", "address"),
            ("guaranteed", "safe"),
            ("approved", "payment"),
            ("verified", "illicit"),
        )
    )
    files = list((ROOT / "routes").glob("trace*.py")) + list(
        (ROOT / "components/trace").glob("*.py")
    )
    for path in files:
        lowered = path.read_text().lower()
        for phrase in forbidden:
            assert phrase not in lowered, f"{phrase!r} found in {path}"
