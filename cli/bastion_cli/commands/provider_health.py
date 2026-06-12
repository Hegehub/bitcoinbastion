from __future__ import annotations

import typer

from cli.bastion_cli.commands._common import output, run


def provider_health(ctx: typer.Context) -> None:
    """Show provider health, degraded, fallback, and stale indicators where available."""
    data = run(ctx, lambda client: client.provider_health.list())
    output(ctx, data)
