from __future__ import annotations

import typer

from cli.bastion_cli.commands._common import output, run

app = typer.Typer(help="Webhook management read commands plus explicit test delivery.")


@app.command("list")
def list_webhooks(ctx: typer.Context, limit: int = 50, offset: int = 0) -> None:
    data = run(ctx, lambda client: client.webhooks.list(limit=limit, offset=offset))
    output(ctx, data)


@app.command("get")
def get(ctx: typer.Context, webhook_id: str) -> None:
    data = run(ctx, lambda client: client.webhooks.get(webhook_id))
    output(ctx, data)


@app.command("deliveries")
def deliveries(ctx: typer.Context, webhook_id: str, limit: int = 50, offset: int = 0) -> None:
    data = run(ctx, lambda client: client.webhooks.deliveries(webhook_id, limit=limit, offset=offset))
    output(ctx, data)


@app.command("test")
def test(ctx: typer.Context, webhook_id: str, yes: bool = typer.Option(False, "--yes", help="Confirm creation of a signed test delivery.")) -> None:
    if not yes:
        typer.confirm(
            "Create a signed webhook test delivery for the configured endpoint? This may send a test request when dispatch is enabled.",
            abort=True,
        )
    data = run(ctx, lambda client: client.webhooks.test(webhook_id))
    output(ctx, data)
