from __future__ import annotations

import typer

from cli.bastion_cli.commands._common import output, run

app = typer.Typer(help="Platform status and degraded-state visibility.")


@app.callback(invoke_without_command=True)
def status(ctx: typer.Context) -> None:
    """Show public platform status."""
    data = run(ctx, lambda client: client.health.public_status())
    output(ctx, data)
