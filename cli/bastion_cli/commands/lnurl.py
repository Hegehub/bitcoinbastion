from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any
from urllib.parse import urlsplit

import httpx
import typer

from cli.bastion_cli.commands._common import output, run

app = typer.Typer(
    help="LNURL-auth, payment, and policy-gated withdraw orchestration. Payment is not authentication; Lightning Address is routing, not identity.",
    no_args_is_help=True,
)


def _map(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    return {
        name: getattr(value, name)
        for name in dir(value)
        if not name.startswith("_") and not callable(getattr(value, name))
    }


def _presentation(
    ctx: typer.Context,
    action: str,
    origin: str,
    device_key_fingerprint: str,
    intended_action: str | None = None,
) -> dict[str, Any]:
    data = run(
        ctx,
        lambda client: client.auth.lnurl.create_auth_challenge(
            action=action,
            origin=origin,
            device_key_fingerprint=device_key_fingerprint,
            intended_policy_action=intended_action,
        ),
    )
    raw = _map(data)
    # k1 is deliberately removed: it is embedded in the single-use public LNURL and is backend-owned.
    raw.pop("k1", None)
    return {
        **raw,
        "auth_domain": raw.get("auth_domain") or raw.get("domain"),
        "action": action,
        "state": "pending",
        "security": "LNURL-auth proves Lightning wallet control; a Device-bound PoP Session is still required.",
    }


@app.command("auth")
def auth(
    ctx: typer.Context,
    action: str = typer.Option("login", help="register, login, link, or auth"),
    origin: str = typer.Option(...),
    device_key_fingerprint: str = typer.Option(...),
    intended_action: str | None = typer.Option(None),
    uri_only: bool = typer.Option(False, "--uri-only"),
    qr: bool = typer.Option(False, "--qr/--no-qr"),
) -> None:
    if action not in {"register", "login", "link", "auth"}:
        raise typer.BadParameter("Unsupported LNURL-auth action.")
    data = _presentation(ctx, action, origin, device_key_fingerprint, intended_action)
    if qr:
        data["qr"] = "QR dependency unavailable; scan the LNURL URI shown above."
    if uri_only:
        output(
            ctx,
            {
                "lnurl": data.get("lnurl") or data.get("lnurl_bech32"),
                "auth_domain": data.get("auth_domain"),
                "action": action,
            },
        )
    else:
        output(ctx, data)


@app.command("auth-login")
def auth_login(
    ctx: typer.Context,
    origin: str = typer.Option(...),
    device_key_fingerprint: str = typer.Option(...),
) -> None:
    output(ctx, _presentation(ctx, "login", origin, device_key_fingerprint))


@app.command("auth-register")
def auth_register(
    ctx: typer.Context,
    origin: str = typer.Option(...),
    device_key_fingerprint: str = typer.Option(...),
) -> None:
    output(ctx, _presentation(ctx, "register", origin, device_key_fingerprint))


@app.command("auth-step-up")
def auth_step_up(
    ctx: typer.Context,
    action: str = typer.Option(...),
    device_key_fingerprint: str = typer.Option(...),
    target_reference: str | None = typer.Option(None),
) -> None:
    output(
        ctx,
        run(
            ctx,
            lambda client: client.auth.lnurl.step_up(
                action=action,
                device_key_fingerprint=device_key_fingerprint,
                target_reference=target_reference,
            ),
        ),
    )


@app.command("pay")
def pay(
    ctx: typer.Context,
    plan: str = typer.Option(...),
    comment: str | None = typer.Option(None),
    duration_days: int = typer.Option(30),
    payer_auth: bool = typer.Option(True, "--payer-auth/--no-payer-auth"),
) -> None:
    data = run(
        ctx,
        lambda client: client.auth.lnurl.create_subscription_payment(
            plan=plan, duration_days=duration_days, payerdata_auth_requested=payer_auth
        ),
    )
    raw = _map(data)
    allowed = raw.get("comment_allowed")
    if comment is not None and isinstance(allowed, int) and len(comment) > allowed:
        raise typer.BadParameter(f"Comment exceeds server commentAllowed limit ({allowed}).")
    output(
        ctx,
        {
            **raw,
            "comment": comment,
            "invoice_state": "not_issued",
            "settlement": "pending",
            "entitlement_active": False,
            "privacy": "payerData personal fields are never auto-filled; comments are untrusted metadata.",
        },
    )


@app.command("pay-status")
def pay_status(ctx: typer.Context, payment_id: str) -> None:
    raw = _map(run(ctx, lambda client: client.auth.lnurl.verify_payment(payment_id)))
    output(
        ctx,
        {
            **raw,
            "entitlement_active": bool(raw.get("entitlement_active"))
            and str(raw.get("state")) in {"settled", "verified"},
        },
    )


@app.command("verify")
def verify(ctx: typer.Context, payment_id: str) -> None:
    raw = _map(run(ctx, lambda client: client.auth.lnurl.verify_payment(payment_id)))
    state = str(raw.get("state", "pending"))
    output(
        ctx,
        {
            "payment_id": payment_id,
            "settlement": "verified" if state in {"settled", "verified"} else state,
            "entitlement_active": bool(raw.get("entitlement_active"))
            and state in {"settled", "verified"},
        },
    )


@app.command("address")
def address(ctx: typer.Context, lightning_address: str) -> None:
    parts = lightning_address.strip().lower().split("@")
    if len(parts) != 2 or not all(parts) or "/" in parts[1]:
        raise typer.BadParameter("Lightning Address must be name@domain.")
    url = f"https://{parts[1]}/.well-known/lnurlp/{parts[0]}"
    try:
        response = httpx.get(url, timeout=ctx.obj["config"].timeout, follow_redirects=False)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as exc:
        raise typer.BadParameter(
            "Lightning Address discovery failed; no payment was attempted."
        ) from exc
    callback = str(data.get("callback", ""))
    callback_domain = urlsplit(callback).hostname
    output(
        ctx,
        {
            "address": lightning_address,
            "discovery_url": url,
            "callback_domain": callback_domain,
            "min_sendable": data.get("minSendable"),
            "max_sendable": data.get("maxSendable"),
            "metadata": data.get("metadata"),
            "payer_data": data.get("payerData"),
            "comment_allowed": data.get("commentAllowed"),
            "warning": "Lightning Address is payment routing UX, not identity. No payment was sent.",
        },
    )


@app.command("withdraw")
def withdraw(
    ctx: typer.Context,
    amount_msat: int = typer.Option(..., min=1),
    purpose: str = typer.Option(...),
    reason: str = typer.Option(...),
    step_up_id: str | None = typer.Option(None),
) -> None:
    raw = _map(
        run(
            ctx,
            lambda client: client.auth.lnurl.request_withdraw(
                amount_msat=amount_msat, payout_type=purpose, reason=reason, step_up_id=step_up_id
            ),
        )
    )
    if raw.get("policy_approved") is not True:
        output(
            ctx,
            {
                "status": "DENIED",
                "policy_approved": False,
                "reason": raw.get(
                    "reason", "Backend policy did not approve withdraw; no QR issued."
                ),
            },
        )
        raise typer.Exit(4)
    output(
        ctx,
        {
            **raw,
            "purpose": purpose,
            "amount_msat": amount_msat,
            "warning": "Wallet callback and payout completion remain backend-authoritative.",
        },
    )


@app.command("withdraw-status")
def withdraw_status(ctx: typer.Context, withdraw_id: str) -> None:
    output(
        ctx,
        {
            "withdraw_id": withdraw_id,
            "status": "unknown",
            "message": "This backend exposes no Bastion-side withdraw status route; re-check the authoritative audit/payout API.",
        },
    )


@app.command("capabilities")
def capabilities(ctx: typer.Context) -> None:
    output(
        ctx,
        {
            "source": "implemented backend routes",
            "bip322": True,
            "lnurl_auth": True,
            "lnurl_pay": True,
            "lnurl_withdraw": True,
            "payer_data_auth": True,
            "success_action": ["message", "url"],
            "lightning_address": True,
            "note": "Wallet-specific interoperability is not claimed; query deployment compatibility registry when available.",
        },
    )
