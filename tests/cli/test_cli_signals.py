from __future__ import annotations

from typer.testing import CliRunner

from cli.bastion_cli.main import app

runner = CliRunner()


class _Signals:
    def __init__(self) -> None:
        self.latest_called = False

    def latest(self) -> list[dict[str, object]]:
        self.latest_called = True
        return [{"id": 1, "confidence": 0.7}]


class _Client:
    def __init__(self) -> None:
        self.signals = _Signals()

    def __enter__(self) -> "_Client":
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_signals_latest_command_calls_expected_sdk_method(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    client = _Client()
    monkeypatch.setattr("cli.bastion_cli.commands._common.make_client", lambda config: client)
    result = runner.invoke(app, ["--output", "json", "signals", "latest"])
    assert result.exit_code == 0, result.output
    assert client.signals.latest_called is True
    assert "not financial advice" in result.output
