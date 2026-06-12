from __future__ import annotations

import json

from rich.console import Console

from cli.bastion_cli.output import emit, redact


def test_output_json_is_valid_json() -> None:
    console = Console(record=True, force_terminal=False)
    emit({"status": "ok"}, output="json", console=console)
    parsed = json.loads(console.export_text())
    assert parsed == {"status": "ok"}


def test_output_table_is_human_readable() -> None:
    console = Console(record=True, force_terminal=False)
    emit({"status": "ok"}, output="table", console=console)
    text = console.export_text()
    assert "status" in text
    assert "ok" in text


def test_webhook_secrets_are_redacted() -> None:
    assert redact({"secret_ref": "abc", "token": "secret-token"}) == {
        "secret_ref": "[REDACTED]",
        "token": "[REDACTED]",
    }
