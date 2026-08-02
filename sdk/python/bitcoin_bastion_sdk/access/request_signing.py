from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import quote

from bitcoin_bastion_sdk.access.device import DeviceSigner

HEADER_AUTHORIZATION = "Authorization"
HEADER_TIMESTAMP = "Bastion-Request-Timestamp"
HEADER_NONCE = "Bastion-Request-Nonce"
HEADER_BODY_HASH = "Bastion-Request-Body-Hash"
HEADER_SIGNATURE = "Bastion-Request-Signature"
HEADER_PRINCIPAL = "Bastion-Principal"


def canonical_json_bytes(value: object | None) -> bytes:
    if value is None:
        return b""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def hash_body(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def canonical_query(params: list[tuple[str, str]] | None = None) -> str:
    pairs = sorted(params or [], key=lambda item: (item[0], item[1]))
    return "&".join(f"{quote(k, safe='')}={quote(v, safe='')}" for k, v in pairs)


def canonical_target(path: str, params: list[tuple[str, str]] | None = None) -> str:
    if not path.startswith("/") or "?" in path or "#" in path:
        raise ValueError("path must be an absolute path without query or fragment")
    query = canonical_query(params)
    return f"{path}?{query}" if query else path


def request_digest(
    method: str, target: str, body_hash: str, timestamp: str, nonce: str
) -> bytes:
    material = "\n".join((method.upper(), target, body_hash.removeprefix("sha256:"), timestamp, nonce))
    return hashlib.sha256(material.encode()).digest()


def new_nonce() -> str:
    return secrets.token_hex(24)


@dataclass(frozen=True, slots=True)
class SignedRequest:
    headers: dict[str, str]
    target: str
    body: bytes


def sign_request(
    *,
    method: str,
    path: str,
    session_token: str,
    principal: str,
    signer: DeviceSigner,
    params: list[tuple[str, str]] | None = None,
    body: bytes = b"",
    timestamp: datetime | None = None,
    nonce: str | None = None,
) -> SignedRequest:
    instant = timestamp or datetime.now(UTC)
    if instant.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    formatted = instant.astimezone(UTC).isoformat().replace("+00:00", "Z")
    request_nonce = nonce or new_nonce()
    target = canonical_target(path, params)
    digest = hash_body(body)
    signature = signer.sign(request_digest(method, target, digest, formatted, request_nonce)).hex()
    return SignedRequest(
        headers={
            HEADER_AUTHORIZATION: f"PoP {session_token}",
            HEADER_TIMESTAMP: formatted,
            HEADER_NONCE: request_nonce,
            HEADER_BODY_HASH: digest,
            HEADER_SIGNATURE: signature,
            HEADER_PRINCIPAL: principal,
        },
        target=target,
        body=body,
    )
