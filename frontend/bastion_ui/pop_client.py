from __future__ import annotations

import hashlib
import json
import secrets
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from urllib.parse import quote

import httpx

from bastion_ui.auth_models import PopSessionMetadata


class BrowserDeviceSigner(Protocol):
    """Adapter for a non-exportable browser/platform Bastion Device Key."""

    def sign(self, digest: bytes) -> str: ...


def canonical_body(value: Any | None) -> bytes:
    if value is None:
        return b""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def canonical_query(params: Mapping[str, Any] | None) -> str:
    pairs = sorted(
        (str(key), str(value)) for key, value in (params or {}).items() if value is not None
    )
    return "&".join(f"{quote(key, safe='')}={quote(value, safe='')}" for key, value in pairs)


def signing_digest(
    method: str,
    path: str,
    params: Mapping[str, Any] | None,
    body: bytes,
    timestamp: str,
    nonce: str,
) -> bytes:
    query = canonical_query(params)
    target = f"{path}?{query}" if query else path
    material = "\n".join(
        (method.upper(), target, hashlib.sha256(body).hexdigest(), timestamp, nonce)
    )
    return hashlib.sha256(material.encode()).digest()


@dataclass(slots=True)
class PopApiClient:
    """Central PoP transport. It never persists the session or device signer."""

    base_url: str
    session: PopSessionMetadata
    signer: BrowserDeviceSigner
    timeout_seconds: float = 5.0
    clock: Callable[[], datetime] = lambda: datetime.now(UTC)
    nonce_factory: Callable[[], str] = lambda: secrets.token_hex(24)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Any | None = None,
    ) -> dict[str, Any]:
        if datetime.fromisoformat(self.session.expires_at.replace("Z", "+00:00")) <= self.clock():
            raise RuntimeError("session_expired")
        body = canonical_body(json_body)
        timestamp = self.clock().astimezone(UTC).isoformat().replace("+00:00", "Z")
        nonce = self.nonce_factory()
        digest = signing_digest(method, path, params, body, timestamp, nonce)
        headers = {
            "Authorization": f"PoP {self.session.session_token}",
            "Bastion-Request-Timestamp": timestamp,
            "Bastion-Request-Nonce": nonce,
            "Bastion-Request-Body-Hash": hashlib.sha256(body).hexdigest(),
            "Bastion-Request-Signature": self.signer.sign(digest),
            "Bastion-Principal": self.session.principal,
            "content-type": "application/json",
        }
        with httpx.Client(base_url=self.base_url, timeout=self.timeout_seconds) as client:
            response = client.request(
                method, path, params=params, content=body or None, headers=headers
            )
            response.raise_for_status()
            payload = response.json()
            data = payload.get("data") if isinstance(payload, dict) else None
            return data if isinstance(data, dict) else payload
