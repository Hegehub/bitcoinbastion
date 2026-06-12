from __future__ import annotations

import typer

from cli.bastion_cli.commands._common import output, run

app = typer.Typer(help="Evidence packet inspection. Evidence is application-level, not legal proof.")


@app.command("packet")
def packet(ctx: typer.Context, packet_id: str) -> None:
    data = run(ctx, lambda client: client.evidence.get_packet(packet_id))
    output(ctx, data)
