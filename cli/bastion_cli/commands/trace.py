from __future__ import annotations

import re

import typer

from bitcoin_bastion_sdk.errors import BastionSafetyError
from bitcoin_bastion_sdk.safety import SAFETY_MESSAGE, assert_safe
from cli.bastion_cli.commands._common import output, run, safety_note
from cli.bastion_cli.errors import exit_with_error

app = typer.Typer(
    help="Trace commands. Advisory-only; not legal verification; not Bitcoin consensus proof; no custody. Public Bitcoin addresses only. Never enter seed phrases, private keys, wallet files or signing material."
)
_ADDRESS_RE = re.compile(r"^(bc1|tb1|bcrt1|[13])[a-zA-HJ-NP-Z0-9]{20,90}$", re.IGNORECASE)


def _validate_address(address: str) -> None:
    assert_safe(address)
    if not _ADDRESS_RE.match(address):
        raise BastionSafetyError(f"Public Bitcoin address required. {SAFETY_MESSAGE}")


@app.command("address")
def address(ctx: typer.Context, bitcoin_address: str) -> None:
    try:
        _validate_address(bitcoin_address)
    except Exception as exc:  # noqa: BLE001
        exit_with_error(exc, debug=ctx.obj["config"].debug)
    data = run(ctx, lambda client: client.trace.analyze_address(bitcoin_address))
    output(ctx, {**safety_note("trace"), "trace": data})


@app.command("report")
def report(ctx: typer.Context, report_id: str) -> None:
    data = run(ctx, lambda client: client.trace.get_report(report_id))
    output(ctx, {**safety_note("trace"), "report": data})


@app.command("summary")
def summary(ctx: typer.Context, report_id: str) -> None:
    data = run(ctx, lambda client: client.trace.get_public_summary(report_id))
    output(ctx, {**safety_note("trace"), "summary": data})


@app.command("evidence")
def evidence(ctx: typer.Context, report_id: str) -> None:
    data = run(ctx, lambda client: client.trace.get_evidence(report_id))
    output(ctx, {**safety_note("trace"), "evidence": data})
