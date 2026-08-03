from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import typer

from cli.bastion_cli.commands._common import output, run
from cli.bastion_cli.security.local_vault import LocalVault, SAFETY_MESSAGE, reject_wallet_secrets

app = typer.Typer(
    help="Bitcoin wallet proof, Device Binding, and PoP Session orchestration. Wallet proof alone is not API authorization.",
    no_args_is_help=True,
)
_WARNING = "This signature does not authorize a Bitcoin transaction. This signature only proves wallet control for Bastion access."
_DEVICE_WARNING = "Bastion Device Key is an access key for Bastion. It is not a Bitcoin wallet key."
_ACTIONS = {
    "register",
    "login",
    "new_device",
    "step_up",
    "recovery_start",
    "create_api_key",
    "lockdown",
}


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    return {
        name: getattr(value, name)
        for name in dir(value)
        if not name.startswith("_") and not callable(getattr(value, name))
    }


def _proof(
    path: Path | None,
    signature: str | None,
    method: str,
    network: str,
    wallet_identifier: str | None,
) -> dict[str, Any]:
    if path:
        payload = json.loads(path.read_text(encoding="utf-8"))
        reject_wallet_secrets(payload)
        if not isinstance(payload, dict):
            raise typer.BadParameter("Proof file must contain a JSON object.")
        return payload
    if signature:
        typer.echo(
            "Warning: --signature may be retained in shell history; prefer --proof-file.", err=True
        )
        return {
            "proof_method": method,
            "signature": signature,
            "network": network,
            "wallet_identifier": wallet_identifier,
        }
    raise typer.BadParameter(
        "Provide an external-wallet proof with --proof-file (preferred) or --signature."
    )


@app.command("challenge")
def challenge(
    ctx: typer.Context,
    action: str = typer.Option(..., "--action"),
    network: str = typer.Option("bitcoin-mainnet", "--network"),
    device_key_fingerprint: str = typer.Option(..., "--device-key-fingerprint"),
    origin: str = typer.Option(..., "--origin"),
    proof_type: str = typer.Option("bip322", "--proof-type"),
) -> None:
    if action not in _ACTIONS:
        raise typer.BadParameter(f"Unsupported action: {action}")
    data = run(
        ctx,
        lambda client: client.auth.wallet.create_challenge(
            action=action,
            network=network,
            proof_type=proof_type,
            device_key_fingerprint=device_key_fingerprint,
            origin=origin,
        ),
    )
    output(
        ctx,
        {
            **_mapping(data),
            "action": action,
            "origin": origin,
            "device_key_fingerprint": device_key_fingerprint,
            "safety_warning": _WARNING,
            "seed_warning": SAFETY_MESSAGE,
        },
    )


def _submit(
    ctx: typer.Context,
    operation: str,
    challenge_id: str,
    proof_file: Path | None,
    signature: str | None,
    wallet_identifier: str | None,
    network: str,
    device_key_fingerprint: str,
    proof_method: str,
    origin: str,
    device_class: str,
) -> None:
    proof = _proof(proof_file, signature, proof_method, network, wallet_identifier)
    payload = {
        "challenge_id": challenge_id,
        "proof_type": proof.get("proof_method", proof_method),
        "signature": proof.get("signature"),
        "wallet_identifier": proof.get("wallet_identifier", wallet_identifier),
        "public_key": proof.get("public_key"),
        "device_key_fingerprint": device_key_fingerprint,
        "origin": origin,
        "network": proof.get("network", network),
    }
    if operation == "register":
        payload["device_class"] = device_class
    data = run(ctx, lambda client: getattr(client.auth.wallet, operation)(**payload))
    output(
        ctx,
        {
            "wallet_principal": "active",
            "proof_method": proof_method,
            "device": "bound",
            "result": data,
            "safety_warning": _WARNING,
        },
    )


@app.command("register")
def register(
    ctx: typer.Context,
    challenge_id: str = typer.Option(...),
    proof_file: Path | None = typer.Option(None, exists=True),
    signature: str | None = typer.Option(None),
    wallet_identifier: str | None = typer.Option(None),
    network: str = typer.Option("bitcoin-mainnet"),
    device_key_fingerprint: str = typer.Option(...),
    proof_method: str = typer.Option("bip322"),
    origin: str = typer.Option(...),
    device_class: str = typer.Option("cli_vault"),
) -> None:
    _submit(
        ctx,
        "register",
        challenge_id,
        proof_file,
        signature,
        wallet_identifier,
        network,
        device_key_fingerprint,
        proof_method,
        origin,
        device_class,
    )


@app.command("login")
def login(
    ctx: typer.Context,
    challenge_id: str = typer.Option(...),
    proof_file: Path | None = typer.Option(None, exists=True),
    signature: str | None = typer.Option(None),
    wallet_identifier: str | None = typer.Option(None),
    network: str = typer.Option("bitcoin-mainnet"),
    device_key_fingerprint: str = typer.Option(...),
    proof_method: str = typer.Option("bip322"),
    origin: str = typer.Option(...),
) -> None:
    _submit(
        ctx,
        "login",
        challenge_id,
        proof_file,
        signature,
        wallet_identifier,
        network,
        device_key_fingerprint,
        proof_method,
        origin,
        "cli_vault",
    )


@app.command("session")
def session(
    ctx: typer.Context,
    authentication_grant: str = typer.Option(..., help="Single-use backend authentication grant."),
    requested_scope: list[str] | None = typer.Option(None, "--scope"),
) -> None:
    from bitcoin_bastion_sdk.access import Ed25519DeviceSigner

    signer = Ed25519DeviceSigner.generate()
    data = run(
        ctx,
        lambda client: client.auth.wallet.create_session(
            authentication_grant=authentication_grant,
            device_public_key=signer.public_key.hex(),
            session_public_key=signer.public_key.hex(),
            requested_scopes=requested_scope or [],
        ),
    )
    raw = _mapping(data)
    vault = LocalVault.from_environment()
    if vault and raw.get("session_token"):
        vault.save(
            {
                "device_key": signer.private_bytes_for_vault().hex(),
                "session": {
                    "token": raw["session_token"],
                    "principal": raw.get("principal_hash", ""),
                    "expires_at": raw["expires_at"],
                    "scopes": raw.get("scopes", []),
                    "plan": raw.get("plan"),
                },
            }
        )
    output(
        ctx,
        {
            "session": "active",
            "expires_at": raw.get("expires_at"),
            "scopes": raw.get("scopes", []),
            "stored": bool(vault),
            "device_warning": _DEVICE_WARNING,
        },
    )


@app.command("me")
def me(ctx: typer.Context) -> None:
    output(ctx, run(ctx, lambda client: client.auth.wallet.get_principal()))


@app.command("entitlements")
def entitlements(ctx: typer.Context) -> None:
    output(ctx, run(ctx, lambda client: client.auth.wallet.get_entitlements()))


@app.command("devices")
def devices(ctx: typer.Context) -> None:
    output(ctx, run(ctx, lambda client: client.auth.wallet.list_devices()))


@app.command("device-revoke")
def device_revoke(ctx: typer.Context, device_id: str) -> None:
    output(ctx, run(ctx, lambda client: client.auth.wallet.revoke_device(device_id)))


@app.command("step-up")
def step_up(
    ctx: typer.Context,
    action: str = typer.Option(...),
    challenge_id: str = typer.Option(...),
    proof_file: Path = typer.Option(..., exists=True),
) -> None:
    proof = _proof(proof_file, None, "bip322", "bitcoin-mainnet", None)
    output(
        ctx,
        run(
            ctx,
            lambda client: client.auth.wallet.step_up(
                action=action,
                challenge_id=challenge_id,
                proof_type=proof.get("proof_method", "bip322"),
                signature=proof.get("signature"),
                wallet_identifier=proof.get("wallet_identifier"),
                intent_hash=proof.get("intent_hash"),
            ),
        ),
    )


@app.command("recovery-start")
def recovery_start(
    ctx: typer.Context,
    principal_reference: str = typer.Option(...),
    recovery_profile: str = typer.Option(...),
    new_device_public_key: str = typer.Option(...),
) -> None:
    output(
        ctx,
        {
            "warning": "Bastion recovery never requires your Bitcoin wallet seed or private key.",
            "result": run(
                ctx,
                lambda client: client.auth.wallet.start_recovery(
                    principal_reference=principal_reference,
                    recovery_profile=recovery_profile,
                    requested_action="recovery_start",
                    new_device_public_key=new_device_public_key,
                ),
            ),
        },
    )


@app.command("recovery-status")
def recovery_status(ctx: typer.Context, recovery_id: str) -> None:
    output(ctx, run(ctx, lambda client: client.auth.wallet.recovery_status(recovery_id)))


@app.command("recovery-complete")
def recovery_complete(
    ctx: typer.Context, recovery_id: str, completion_file: Path = typer.Option(..., exists=True)
) -> None:
    payload = json.loads(completion_file.read_text())
    reject_wallet_secrets(payload)
    output(
        ctx, run(ctx, lambda client: client.auth.wallet.complete_recovery(recovery_id, **payload))
    )


@app.command("lockdown")
def lockdown(
    ctx: typer.Context, reason: str = typer.Option(...), yes: bool = typer.Option(False, "--yes")
) -> None:
    if not yes:
        typer.confirm(
            "Freeze sessions, applicable devices, delegated credentials, offline packs, and PayRegister access according to backend policy?",
            abort=True,
        )
    output(ctx, run(ctx, lambda client: client.auth.wallet.start_lockdown(reason_code=reason)))


@app.command("lockdown-release")
def lockdown_release(
    ctx: typer.Context,
    recovery_id: str = typer.Option(...),
    completion_file: Path = typer.Option(..., exists=True),
) -> None:
    typer.echo(
        "Lockdown release requires backend-approved high-assurance recovery; no policy bypass exists.",
        err=True,
    )
    recovery_complete(ctx, recovery_id, completion_file)


@app.command("status")
def status(ctx: typer.Context) -> None:
    vault = LocalVault.from_environment()
    state = vault.load() if vault else {}
    output(
        ctx,
        {
            "session_configured": bool(state.get("session")),
            "vault_configured": bool(vault),
            "architecture": "Wallet/LNURL Proof -> Principal -> Device Binding -> PoP Session -> Policy",
        },
    )
