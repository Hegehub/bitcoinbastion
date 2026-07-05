from __future__ import annotations

from typer.testing import CliRunner

from cli.bastion_cli.main import app

runner = CliRunner()


class _Webhooks:
    def __init__(self) -> None:
        self.tested: list[str] = []

    def list(self, *, limit: int = 50, offset: int = 0) -> list[dict[str, object]]:
        return [{"id": 1, "secret_ref": "secret-value", "limit": limit, "offset": offset}]

    def get(self, webhook_id: str) -> dict[str, object]:
        return {"id": webhook_id, "token": "secret-token"}

    def deliveries(
        self, webhook_id: str, *, limit: int = 50, offset: int = 0
    ) -> list[dict[str, object]]:
        return [{"webhook_id": webhook_id, "signature_secret": "hidden"}]

    def test(self, webhook_id: str) -> dict[str, object]:
        self.tested.append(webhook_id)
        return {"delivery_id": "d1", "status": "test_created"}


class _Client:
    def __init__(self) -> None:
        self.webhooks = _Webhooks()

    def __enter__(self) -> "_Client":
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_webhooks_list_redacts_secrets(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr("cli.bastion_cli.commands._common.make_client", lambda config: _Client())
    result = runner.invoke(app, ["--output", "json", "webhooks", "list"])
    assert result.exit_code == 0, result.output
    assert "secret-value" not in result.output
    assert "[REDACTED]" in result.output


def test_webhook_test_requires_confirmation_unless_yes(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    client = _Client()
    monkeypatch.setattr("cli.bastion_cli.commands._common.make_client", lambda config: client)

    rejected = runner.invoke(app, ["webhooks", "test", "123"], input="n\n")
    assert rejected.exit_code != 0
    assert client.webhooks.tested == []

    accepted = runner.invoke(app, ["--output", "json", "webhooks", "test", "123", "--yes"])
    assert accepted.exit_code == 0, accepted.output
    assert client.webhooks.tested == ["123"]
