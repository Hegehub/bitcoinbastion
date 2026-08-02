from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def write_bastion_pass(payload: dict[str, Any], path: str | Path) -> Path:
    target = Path(path).expanduser()
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, sort_keys=True, separators=(",", ":"))
    return target


class AccessCertificateClient:
    def __init__(self, transport: Any) -> None:
        self._transport = transport

    def issue(self, **payload: Any) -> Any:
        return self._transport.request("POST", "/access/certificates", json=payload, require_auth=True)

    def write_export(self, payload: dict[str, Any], path: str | Path) -> Path:
        return write_bastion_pass(payload, path)
