from __future__ import annotations

from typer.testing import CliRunner

from cli.bastion_cli.main import app

runner = CliRunner()


def test_treasury_commands_are_read_only() -> None:
    result = runner.invoke(app, ["treasury", "--help"])
    assert result.exit_code == 0
    assert "No approval" in result.output
    assert "signing" in result.output
    assert "approve" not in {"requests", "pending-approvals"}
