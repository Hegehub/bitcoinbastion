from __future__ import annotations

import typer

from cli.bastion_cli.commands import (
    evidence,
    health,
    market,
    news,
    onchain,
    signals,
    status,
    trace,
    treasury,
    webhooks,
    websocket,
    wallet_auth,
    lnurl,
)
from cli.bastion_cli.commands.provider_health import provider_health
from cli.bastion_cli.config import CLIConfig

app = typer.Typer(
    help="Operator-safe Bitcoin Bastion CLI. No custody, no seed/private-key handling, read-first commands.",
    no_args_is_help=True,
)


@app.callback()
def main(
    ctx: typer.Context,
    api_base_url: str | None = typer.Option(
        None, "--api-base-url", help="Bitcoin Bastion API base URL."
    ),
    token: str | None = typer.Option(
        None, "--token", hidden=True, help="Deprecated; legacy authentication is disabled."
    ),
    timeout: float | None = typer.Option(None, "--timeout", help="Request timeout seconds."),
    output: str | None = typer.Option(None, "--output", help="Output mode: table, json, or yaml."),
    debug: bool = typer.Option(
        False, "--debug", help="Show debug diagnostics without printing secrets."
    ),
) -> None:
    ctx.obj = {
        "config": CLIConfig.from_env(
            api_base_url=api_base_url,
            token=token,
            timeout=timeout,
            output=output,
            debug=debug,
        )
    }


app.add_typer(health.app, name="health")
app.add_typer(status.app, name="status")
app.add_typer(signals.app, name="signals")
app.add_typer(news.app, name="news")
app.add_typer(trace.app, name="trace")
app.add_typer(evidence.app, name="evidence")
app.add_typer(market.app, name="market")
app.add_typer(onchain.app, name="onchain")
app.add_typer(treasury.app, name="treasury")
app.command("provider-health")(provider_health)
app.add_typer(webhooks.app, name="webhooks")
app.add_typer(websocket.app, name="ws")
app.add_typer(wallet_auth.app, name="wallet-auth")
app.add_typer(lnurl.app, name="lnurl")

if __name__ == "__main__":
    app()
