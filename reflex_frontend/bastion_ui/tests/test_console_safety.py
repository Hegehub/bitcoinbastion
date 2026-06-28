from __future__ import annotations

from pathlib import Path

from bastion_ui.components.console.degraded_mode_banner import DEGRADED_MODE_COPY
from bastion_ui.components.console.operator_safety_panel import OPERATOR_SAFETY_COPY

ROOT = Path(__file__).resolve().parents[3]
CONSOLE_PATHS = (
    ROOT / "reflex_frontend/bastion_ui/components/console",
    ROOT / "reflex_frontend/bastion_ui/routes/console.py",
    ROOT / "reflex_frontend/bastion_ui/routes/console_trace.py",
    ROOT / "reflex_frontend/bastion_ui/routes/console_evidence.py",
    ROOT / "reflex_frontend/bastion_ui/routes/console_provider_health.py",
    ROOT / "reflex_frontend/bastion_ui/routes/console_policy.py",
    ROOT / "reflex_frontend/bastion_ui/routes/console_audit.py",
)
FORBIDDEN_PARTS = (
    ("clean", "address"),
    ("dirty", "address"),
    ("criminal", "address"),
    ("guaranteed", "safe"),
    ("approved", "payment"),
    ("verified", "illicit"),
)


def _console_text() -> str:
    files: list[Path] = []
    for path in CONSOLE_PATHS:
        if path.is_dir():
            files.extend(path.rglob("*.py"))
        else:
            files.append(path)
    return "\n".join(path.read_text(encoding="utf-8") for path in files).lower()


def test_console_operator_safety_copy_present() -> None:
    assert "Bitcoin Bastion is advisory-only." in OPERATOR_SAFETY_COPY
    assert "Do not enter seed phrases" in OPERATOR_SAFETY_COPY
    assert "private keys" in OPERATOR_SAFETY_COPY
    assert "wallet files" in OPERATOR_SAFETY_COPY
    assert "signing material" in OPERATOR_SAFETY_COPY
    assert "not legal verification" in OPERATOR_SAFETY_COPY
    assert "not Bitcoin consensus proof" in OPERATOR_SAFETY_COPY
    assert "not financial advice" in OPERATOR_SAFETY_COPY
    assert "explicit human approval" in OPERATOR_SAFETY_COPY


def test_console_degraded_copy_present() -> None:
    assert "delayed, stale, degraded, or partially unavailable" in DEGRADED_MODE_COPY
    assert "Review provider health and evidence limitations" in DEGRADED_MODE_COPY


def test_console_forbidden_wording_absent() -> None:
    text = _console_text()
    for left, right in FORBIDDEN_PARTS:
        assert f"{left} {right}" not in text


def test_console_does_not_add_sensitive_inputs() -> None:
    text = _console_text()
    assert "rx.input" not in text
    assert "type=\"file\"" not in text
    assert "upload" not in text
    assert "transaction signing" not in text
    assert "automatic treasury execution" not in text
