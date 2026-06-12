from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Literal

from bitcoin_bastion_sdk import BastionClient

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
            api_base_url=(api_base_url or os.getenv("BB_API_BASE_URL") or "http://localhost:8000").rstrip("/"),
            token=token if token is not None else os.getenv("BB_API_TOKEN"),
            timeout=float(timeout if timeout is not None else raw_timeout),
            output=selected_output,  # type: ignore[arg-type]
            debug=debug,
        )


def make_client(config: CLIConfig) -> BastionClient:
    return BastionClient(base_url=config.api_base_url, api_key=config.token, timeout=config.timeout)
