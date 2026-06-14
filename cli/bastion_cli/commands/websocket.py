from __future__ import annotations

import asyncio
from time import monotonic
import typer

from cli.bastion_cli.commands._common import config_from_context, output
from cli.bastion_cli.config import make_client
from cli.bastion_cli.errors import exit_with_error

app = typer.Typer(help="WebSocket smoke checks.")


@app.command("events")
def events(
    ctx: typer.Context,
    topics: str | None = typer.Option(None, "--topics", help="Comma-separated topics such as signals,trace,market."),
    duration: int = typer.Option(30, "--duration", min=1, help="Maximum seconds to listen."),
    max_events: int = typer.Option(20, "--max-events", min=1, help="Maximum messages to print."),
    follow: bool = typer.Option(False, "--follow", help="Remain open until interrupted."),
) -> None:
    """Connect to /ws/events and print bounded messages."""
    if follow:
        typer.echo("Following WebSocket stream until interrupted.")
    try:
        asyncio.run(_run_events(ctx, topics=topics, duration=duration, max_events=max_events, follow=follow))
    except Exception as exc:  # noqa: BLE001
        exit_with_error(exc, debug=config_from_context(ctx).debug)


async def _run_events(
    ctx: typer.Context,
    *,
    topics: str | None,
    duration: int,
    max_events: int,
    follow: bool,
) -> None:
    config = config_from_context(ctx)
    topic_list = [item.strip() for item in topics.split(",") if item.strip()] if topics else None
    count = 0
    started = monotonic()
    with make_client(config) as client:
        async with client.websocket.subscribe_events(topics=topic_list) as stream:
            async for event in stream:
                output(ctx, event)
                count += 1
                if not follow and count >= max_events:
                    return
                if not follow and monotonic() - started >= duration:
                    return
