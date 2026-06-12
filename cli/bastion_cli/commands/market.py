from __future__ import annotations

import typer

from cli.bastion_cli.commands._common import output, run, safety_note

app = typer.Typer(help="Market intelligence is informational only and not financial advice.")


@app.command("dashboard")
def dashboard(ctx: typer.Context) -> None:
    data = run(ctx, lambda client: client.market.dashboard())
    output(ctx, {**safety_note("market"), "market": data})


@app.command("timeline")
def timeline(ctx: typer.Context) -> None:
    data = run(ctx, lambda client: client.market.timeline())
    output(ctx, {**safety_note("market"), "timeline": data})
