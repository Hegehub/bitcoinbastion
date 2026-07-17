from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONSOLE_COMPONENTS = ROOT / "frontend/bastion_ui/components/console"
CONSOLE_ROUTES = ROOT / "frontend/bastion_ui/routes"

FORBIDDEN_PHRASES = (
    "clean address",
    "dirty address",
    "criminal address",
    "guaranteed safe",
    "approved payment",
    "verified illicit",
)
SENSITIVE_PROMPTS = (
    "seed phrase input",
    "private key input",
    "wallet.dat upload",
    "keystore upload",
    "signing-material field",
    "raw transaction signing",
)


def _console_text() -> str:
    files = list(CONSOLE_COMPONENTS.glob("*.py")) + [
        CONSOLE_ROUTES / "console_trace.py",
        CONSOLE_ROUTES / "console_evidence.py",
        CONSOLE_ROUTES / "console_provider_health.py",
        CONSOLE_ROUTES / "console_policy.py",
        CONSOLE_ROUTES / "console_audit.py",
    ]
    return "\n".join(path.read_text(encoding="utf-8") for path in files).lower()


def test_console_safety_copy_present() -> None:
    text = _console_text()
    assert "advisory-only" in text
    assert "not legal verification" in text
    assert "not bitcoin consensus proof" in text
    assert "no custody" in text
    assert "never enter seed phrases" in text
    assert "private keys" in text
    assert "wallet files" in text
    assert "signing material" in text


def test_forbidden_wording_absent_from_console_modules() -> None:
    text = _console_text()
    for phrase in FORBIDDEN_PHRASES:
        assert phrase not in text


def test_sensitive_prompts_and_execution_actions_absent() -> None:
    text = _console_text()
    for phrase in SENSITIVE_PROMPTS:
        assert phrase not in text
    assert "rx.input" not in text
    assert "type=\"file\"" not in text
    assert "auto-approve" not in text
    assert "auto-send" not in text
    assert "auto-trade" not in text
    assert "direct treasury execution" not in text
