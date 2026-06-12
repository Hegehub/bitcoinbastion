from __future__ import annotations

import typer

from cli.bastion_cli.commands._common import output, run, safety_note

app = typer.Typer(help="Signals are informational only and not financial advice.")


@app.command("latest")
def latest(ctx: typer.Context) -> None:
    data = run(ctx, lambda client: client.signals.latest())
    output(ctx, {**safety_note("signals"), "signals": data})


@app.command("top")
def top(ctx: typer.Context, limit: int = 20, offset: int = 0) -> None:
    data = run(ctx, lambda client: client.signals.list_top(limit=limit, offset=offset))
    output(ctx, {**safety_note("signals"), "signals": data})


@app.command("get")
def get(ctx: typer.Context, signal_id: str) -> None:
    data = run(ctx, lambda client: client.signals.get(signal_id))
    output(ctx, {**safety_note("signals"), "signal": data})
