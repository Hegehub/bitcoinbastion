from __future__ import annotations

from typer.testing import CliRunner

from cli.bastion_cli.main import app

runner = CliRunner()


class _Health:
    def __init__(self) -> None:
        self.called = False

    def ready(self) -> dict[str, str]:
        self.called = True
        return {"status": "ok"}


class _Client:
    def __init__(self) -> None:
        self.health = _Health()

    def __enter__(self) -> "_Client":
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_health_command_calls_expected_sdk_method(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    client = _Client()
    monkeypatch.setattr("cli.bastion_cli.commands._common.make_client", lambda config: client)

    result = runner.invoke(app, ["--output", "json", "health"])

    assert result.exit_code == 0, result.output
    assert client.health.called is True
    assert '"status": "ok"' in result.output
