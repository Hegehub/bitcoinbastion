from __future__ import annotations

from time import perf_counter

import typer

from cli.bastion_cli.commands._common import config_from_context, output, run

app = typer.Typer(help="Health and readiness checks.")


@app.callback(invoke_without_command=True)
def health(ctx: typer.Context) -> None:
    """Show API readiness."""
    config = config_from_context(ctx)
    start = perf_counter()
    data = run(ctx, lambda client: client.health.ready())
    latency_ms = round((perf_counter() - start) * 1000, 2)
    output(ctx, {"api_base_url": config.api_base_url, "latency_ms": latency_ms, "health": data})
