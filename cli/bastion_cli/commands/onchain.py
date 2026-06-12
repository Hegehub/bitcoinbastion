from __future__ import annotations

import typer

from cli.bastion_cli.commands._common import output, run

app = typer.Typer(help="On-chain public-data context; no AML/legal certainty claims.")


@app.command("events")
def events(ctx: typer.Context, limit: int = 20, offset: int = 0) -> None:
    data = run(ctx, lambda client: client.onchain.events(limit=limit, offset=offset))
    output(ctx, data)


@app.command("state")
def state(ctx: typer.Context) -> None:
    data = run(ctx, lambda client: client.onchain.state())
    output(ctx, data)
