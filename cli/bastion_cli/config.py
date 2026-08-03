from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Literal

from bitcoin_bastion_sdk import BastionClient
from bitcoin_bastion_sdk.access import BastionPoPSession, Ed25519DeviceSigner
from datetime import datetime

from cli.bastion_cli.security.local_vault import LocalVault

OutputMode = Literal["table", "json", "yaml"]


@dataclass(frozen=True)
class CLIConfig:
    api_base_url: str = "http://localhost:8000"
    token: str | None = None
    timeout: float = 5.0
    output: OutputMode = "table"
    debug: bool = False

    @classmethod
    def from_env(
        cls,
        *,
        api_base_url: str | None = None,
        token: str | None = None,
        timeout: float | None = None,
        output: str | None = None,
        debug: bool = False,
    ) -> "CLIConfig":
        raw_timeout = os.getenv("BB_REQUEST_TIMEOUT_SECONDS", "5")
        selected_output = (output or os.getenv("BB_CLI_OUTPUT") or "table").strip().lower()
        if selected_output not in {"table", "json", "yaml"}:
            selected_output = "table"
        return cls(
            api_base_url=(
                api_base_url or os.getenv("BB_API_BASE_URL") or "http://localhost:8000"
            ).rstrip("/"),
            token=token if token is not None else os.getenv("BB_API_TOKEN"),
            timeout=float(timeout if timeout is not None else raw_timeout),
            output=selected_output,  # type: ignore[arg-type]
            debug=debug,
        )


def make_client(config: CLIConfig) -> BastionClient:
    if config.token:
        raise ValueError(
            "Legacy authentication is disabled. Use `bastion wallet-auth` or `bastion lnurl auth`."
        )
    vault = LocalVault.from_environment()
    state = vault.load() if vault else {}
    pop_session = None
    session = state.get("session")
    device_key = state.get("device_key")
    if isinstance(session, dict) and isinstance(device_key, str):
        signer = Ed25519DeviceSigner.from_private_bytes(bytes.fromhex(device_key))
        pop_session = BastionPoPSession(
            token=str(session["token"]),
            principal=str(session["principal"]),
            device_fingerprint=signer.fingerprint,
            expires_at=datetime.fromisoformat(str(session["expires_at"]).replace("Z", "+00:00")),
            signer=signer,
            scopes=tuple(session.get("scopes", ())),
            plan=session.get("plan"),
        )
    return BastionClient(
        base_url=config.api_base_url, timeout=config.timeout, pop_session=pop_session
    )
