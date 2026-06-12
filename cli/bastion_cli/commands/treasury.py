from __future__ import annotations

import typer

from cli.bastion_cli.commands._common import output, run

app = typer.Typer(help="Treasury observer commands only. No approval, rejection, signing, or broadcast commands are available.")

_READ_ONLY = "Read-only treasury view. This CLI does not approve, reject, sign, broadcast, or execute treasury actions."


@app.command("requests")
def requests(ctx: typer.Context, limit: int = 20, offset: int = 0) -> None:
    data = run(ctx, lambda client: client.treasury.list_requests(limit=limit, offset=offset))
    output(ctx, {"safety": _READ_ONLY, "requests": data})


@app.command("pending-approvals")
def pending_approvals(ctx: typer.Context, limit: int = 20, offset: int = 0) -> None:
    data = run(ctx, lambda client: client.treasury.pending_approvals(limit=limit, offset=offset))
    output(ctx, {"safety": _READ_ONLY, "pending_approvals": data})
