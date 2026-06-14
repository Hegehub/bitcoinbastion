from __future__ import annotations

import typer

from cli.bastion_cli.commands._common import output, run

app = typer.Typer(help="News context without trading instructions.")


@app.command("latest")
def latest(ctx: typer.Context, limit: int = 20, offset: int = 0) -> None:
    data = run(ctx, lambda client: client.news.latest(limit=limit, offset=offset))
    output(ctx, data)
