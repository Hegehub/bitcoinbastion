from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar, cast

import typer

from cli.bastion_cli.config import CLIConfig, make_client
from cli.bastion_cli.errors import exit_with_error
from cli.bastion_cli.output import emit

T = TypeVar("T")


def config_from_context(ctx: typer.Context) -> CLIConfig:
    return cast(CLIConfig, ctx.obj["config"])


def run(ctx: typer.Context, operation: Callable[[Any], T]) -> T:
    config = config_from_context(ctx)
    try:
        with make_client(config) as client:
            return operation(client)
    except Exception as exc:  # noqa: BLE001 - normalized CLI errors
        exit_with_error(exc, debug=config.debug)


def output(ctx: typer.Context, data: Any) -> None:
    emit(data, output=config_from_context(ctx).output)


def safety_note(kind: str) -> dict[str, str]:
    notes = {
        "signals": "Signals are informational only, not financial advice, and do not guarantee future BTC price behavior.",
        "trace": "Advisory-only. Not legal verification. Not Bitcoin consensus proof. No custody. Public Bitcoin addresses only. Never enter seed phrases, private keys, wallet files or signing material.",
        "market": "Market intelligence is informational only. Correlation is not causation. Historical similarity does not guarantee future behavior. Not financial advice.",
    }
    return {"safety": notes[kind]}
