from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.table import Table

SECRET_KEYS = {
    "secret",
    "token",
    "authorization",
    "api_key",
    "signature",
    "signature_secret",
    "k1",
    "private_key",
    "device_key",
    "preimage",
    "recovery_material",
    "access_pass",
    "linking_key",
}


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        safe: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if any(secret in key_text.casefold() for secret in SECRET_KEYS):
                safe[key_text] = "[REDACTED]"
            else:
                safe[key_text] = redact(item)
        return safe
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def emit(data: Any, *, output: str = "table", console: Console | None = None) -> None:
    console = console or Console()
    safe = redact(data)
    if output == "json":
        console.print(json.dumps(safe, indent=2, sort_keys=True, default=str))
        return
    if output == "yaml":
        # YAML is intentionally dependency-free in this prompt; JSON-compatible YAML is valid YAML.
        console.print(json.dumps(safe, indent=2, sort_keys=True, default=str))
        return
    _emit_table(safe, console=console)


def _emit_table(data: Any, *, console: Console) -> None:
    if isinstance(data, list):
        if not data:
            console.print("No results.")
            return
        rows = [item for item in data if isinstance(item, dict)]
        if not rows:
            console.print(str(data))
            return
        columns = list(dict.fromkeys(key for row in rows for key in row.keys()))[:8]
        table = Table(show_header=True, header_style="bold")
        for column in columns:
            table.add_column(str(column))
        for row in rows:
            table.add_row(*[_stringify(row.get(column)) for column in columns])
        console.print(table)
        return
    if isinstance(data, dict):
        table = Table(show_header=True, header_style="bold")
        table.add_column("field")
        table.add_column("value")
        for key, value in data.items():
            table.add_row(str(key), _stringify(value))
        console.print(table)
        return
    console.print(str(data))


def _stringify(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(redact(value), default=str)
    return "" if value is None else str(value)
