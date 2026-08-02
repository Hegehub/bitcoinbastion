from __future__ import annotations

from bitcoin_bastion_sdk.errors import BastionLegacyAuthDisabled
from bitcoin_bastion_sdk.access.certificates import AccessCertificateClient
from bitcoin_bastion_sdk.access.lockdown import LockdownClient
from bitcoin_bastion_sdk.access.recovery import RecoveryClient
from bitcoin_bastion_sdk.lnurl.client import AsyncLNURLClient, LNURLClient
from bitcoin_bastion_sdk.wallet_auth.client import AsyncWalletAuthClient, WalletAuthClient

LEGACY_AUTH_DISABLED_MESSAGE = (
    "Legacy auth is disabled. Use Proof-of-Access challenge/session flow."
)


class LegacyAuthDisabledError(BastionLegacyAuthDisabled):
    pass


def legacy_auth_disabled() -> None:
    raise LegacyAuthDisabledError(LEGACY_AUTH_DISABLED_MESSAGE)


def build_headers(
    api_key: str | None = None,
    headers: dict[str, str] | None = None,
    *,
    allow_legacy_bearer_auth: bool = False,
) -> dict[str, str]:
    """Build request headers without bearer-token fallback.

    ``api_key`` is retained for source compatibility only. Passing it now fails closed
    because protected Bitcoin Bastion APIs require Proof-of-Access headers.
    """
    merged = dict(headers or {})
    _ = allow_legacy_bearer_auth
    if api_key:
        legacy_auth_disabled()
    return merged


def build_proof_of_access_headers(
    *,
    session: str,
    timestamp: str,
    nonce: str,
    body_hash: str,
    signature: str,
    headers: dict[str, str] | None = None,
) -> dict[str, str]:
    merged = dict(headers or {})
    merged.update(
        {
            "X-Bastion-Session": session,
            "X-Bastion-Timestamp": timestamp,
            "X-Bastion-Nonce": nonce,
            "X-Bastion-Body-Hash": body_hash,
            "X-Bastion-Signature": signature,
        }
    )
    return merged


def redact_access_secret(value: str) -> str:
    """Redact Proof-of-Access secrets including child keys and delegated passes."""
    if value.startswith("bbk_live_"):
        return "bbk_live_…redacted"
    if value.startswith("bbd_live_"):
        return "bbd_live_…redacted"
    if value.startswith("bap_"):
        return "bap_…redacted"
    return "<redacted>"


class BastionAuth:
    """High-level Wallet/LNURL authentication facade."""

    def __init__(self, transport: object) -> None:
        self.wallet = WalletAuthClient(transport)
        self.lnurl = LNURLClient(transport)
        self.recovery = RecoveryClient(self.wallet)
        self.lockdown = LockdownClient(self.wallet)
        self.access = AccessCertificateClient(transport)
        self.session = self.wallet


class AsyncBastionAuth:
    def __init__(self, transport: object) -> None:
        self.wallet = AsyncWalletAuthClient(transport)
        self.lnurl = AsyncLNURLClient(transport)
        self.session = self.wallet
