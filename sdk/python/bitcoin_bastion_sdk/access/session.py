from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from bitcoin_bastion_sdk.access.device import DeviceSigner
from bitcoin_bastion_sdk.access.request_signing import SignedRequest, sign_request
from bitcoin_bastion_sdk.redaction import redact_secret


@dataclass(slots=True)
class BastionPoPSession:
    token: str = field(repr=False)
    principal: str
    device_fingerprint: str
    expires_at: datetime
    signer: DeviceSigner = field(repr=False)
    scopes: tuple[str, ...] = ()
    plan: str | None = None
    verification_strength: str = "standard"
    policy_mode: str = "proof_of_possession"

    @property
    def expired(self) -> bool:
        expiry = self.expires_at
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=UTC)
        return expiry <= datetime.now(UTC)

    def sign(
        self,
        method: str,
        path: str,
        *,
        params: list[tuple[str, str]] | None = None,
        body: bytes = b"",
    ) -> SignedRequest:
        if self.expired:
            from bitcoin_bastion_sdk.errors import SessionExpiredError

            raise SessionExpiredError("PoP Session is expired")
        return sign_request(
            method=method,
            path=path,
            params=params,
            body=body,
            session_token=self.token,
            principal=self.principal,
            signer=self.signer,
        )

    def __repr__(self) -> str:
        return (
            f"BastionPoPSession(token={redact_secret(self.token)!r}, "
            f"principal={self.principal!r}, expires_at={self.expires_at!r})"
        )
