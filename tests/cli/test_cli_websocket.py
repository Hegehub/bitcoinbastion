from __future__ import annotations

from typer.testing import CliRunner

from cli.bastion_cli.main import app

runner = CliRunner()


def test_ws_events_supports_duration_and_max_events_options() -> None:
    result = runner.invoke(app, ["ws", "events", "--help"])
    assert result.exit_code == 0
    assert "--duration" in result.output
    assert "--max-events" in result.output
    assert "--follow" in result.output
