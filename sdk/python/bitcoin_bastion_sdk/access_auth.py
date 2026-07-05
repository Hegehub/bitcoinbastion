from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bitcoin_bastion_sdk.errors import (
    BastionAccessChallengeExpired,
    BastionAccessError,
    BastionAccessSessionExpired,
    BastionAccessSignatureError,
)
from bitcoin_bastion_sdk.redaction import redact_secret
from bitcoin_bastion_sdk.signing import DeviceSigner

EMPTY_BODY_HASH = "sha256:" + hashlib.sha256(b"").hexdigest()


def canonical_json_bytes(payload: Any | None) -> bytes:
    if payload is None:
        return b""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def body_hash(payload: Any | None) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def request_digest(method: str, path: str, body_digest: str, timestamp: str, nonce: str) -> str:
    material = f"{method.upper()}{path}{body_digest}{timestamp}{nonce}".encode()
    return "sha256:" + hashlib.sha256(material).hexdigest()


@dataclass(frozen=True)
class AccessPassMaterial:
    certificate_fingerprint: str | None = None
    raw_access_pass: str | None = field(default=None, repr=False)
    metadata: dict[str, Any] = field(default_factory=dict, repr=False)

    def __repr__(self) -> str:
        return f"AccessPassMaterial(certificate_fingerprint={self.certificate_fingerprint!r}, raw_access_pass='<redacted>')"


def import_access_pass(
    raw_pass: str | None = None,
    *,
    path: str | Path | None = None,
    payload: dict[str, Any] | None = None,
) -> AccessPassMaterial:
    if path is not None:
        payload = json.loads(Path(path).expanduser().read_text())
    if payload is not None:
        raw_pass = raw_pass or payload.get("access_pass") or payload.get("raw_access_pass")
        return AccessPassMaterial(
            certificate_fingerprint=payload.get("certificate_fingerprint"),
            raw_access_pass=raw_pass,
            metadata={
                k: v for k, v in payload.items() if k not in {"access_pass", "raw_access_pass"}
            },
        )
    if not raw_pass:
        raise BastionAccessError("Access Pass material is required")
    return AccessPassMaterial(raw_access_pass=raw_pass)


@dataclass
class AccessChallenge:
    challenge_id: str
    challenge_payload: str
    expires_at: datetime
    requested_scopes: list[str]
    origin: str

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "AccessChallenge":
        expires = payload.get("expires_at")
        expires_at = (
            datetime.fromisoformat(str(expires).replace("Z", "+00:00"))
            if expires
            else datetime.now(UTC)
        )
        return cls(
            challenge_id=str(payload.get("challenge_id")),
            challenge_payload=str(payload.get("challenge_payload") or payload.get("payload") or ""),
            expires_at=expires_at,
            requested_scopes=list(payload.get("requested_scopes") or payload.get("scopes") or []),
            origin=str(payload.get("origin") or ""),
        )

    def ensure_valid_for_origin(self, origin: str, *, now: datetime | None = None) -> None:
        current = now or datetime.now(UTC)
        if self.expires_at <= current:
            raise BastionAccessChallengeExpired("Access challenge is expired")
        if self.origin != origin:
            raise BastionAccessSignatureError("Access challenge origin mismatch")


@dataclass
class AccessSession:
    session_token: str = field(repr=False)
    expires_at: datetime
    scopes: list[str]
    plan_code: str
    policy_mode: str | None = None

    def __repr__(self) -> str:
        return f"AccessSession(session_token={redact_secret(self.session_token)!r}, expires_at={self.expires_at!r}, scopes={self.scopes!r}, plan_code={self.plan_code!r})"


@dataclass
class BastionAccessAuth:
    session_token: str = field(repr=False)
    session_expires_at: datetime
    signer: DeviceSigner
    origin: str = "https://app.bitcoinbastion.local"
    scopes: list[str] = field(default_factory=list)
    plan_code: str | None = None

    def __repr__(self) -> str:
        return f"BastionAccessAuth(session_token={redact_secret(self.session_token)!r}, session_expires_at={self.session_expires_at!r}, signer_fingerprint={self.signer.public_key_fingerprint()!r})"

    def ensure_active(self, *, now: datetime | None = None) -> None:
        if self.signer is None:
            raise BastionAccessSignatureError("Device signer is required for Proof-of-Access")
        current = now or datetime.now(UTC)
        if self.session_expires_at <= current:
            raise BastionAccessSessionExpired("Proof-of-Access session is expired")

    def sign_headers(
        self,
        method: str,
        path: str,
        *,
        json_body: Any | None = None,
        now: datetime | None = None,
        nonce: str | None = None,
    ) -> dict[str, str]:
        self.ensure_active(now=now)
        timestamp = (now or datetime.now(UTC)).isoformat().replace("+00:00", "Z")
        request_nonce = nonce or secrets.token_hex(16)
        digest = body_hash(json_body)
        request_hash = request_digest(method, path, digest, timestamp, request_nonce)
        signature = self.signer.sign(request_hash.encode())
        return {
            "X-Bastion-Session": self.session_token,
            "X-Bastion-Timestamp": timestamp,
            "X-Bastion-Nonce": request_nonce,
            "X-Bastion-Body-Hash": digest,
            "X-Bastion-Signature": signature,
        }

    def sign_challenge(
        self, challenge: AccessChallenge, *, origin: str | None = None, now: datetime | None = None
    ) -> str:
        challenge.ensure_valid_for_origin(origin or self.origin, now=now)
        return self.signer.sign(challenge.challenge_payload.encode())

    @classmethod
    def from_session(
        cls,
        session: AccessSession,
        *,
        signer: DeviceSigner,
        origin: str = "https://app.bitcoinbastion.local",
    ) -> "BastionAccessAuth":
        return cls(
            session_token=session.session_token,
            session_expires_at=session.expires_at,
            signer=signer,
            origin=origin,
            scopes=session.scopes,
            plan_code=session.plan_code,
        )
