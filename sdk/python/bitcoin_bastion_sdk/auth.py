from __future__ import annotations

LEGACY_AUTH_DISABLED_MESSAGE = "Legacy auth is disabled. Use Proof-of-Access challenge/session flow."


class LegacyAuthDisabledError(RuntimeError):
    pass


def legacy_auth_disabled() -> None:
    raise LegacyAuthDisabledError(LEGACY_AUTH_DISABLED_MESSAGE)


def build_headers(api_key: str | None = None, headers: dict[str, str] | None = None) -> dict[str, str]:
    """Build request headers without bearer-token fallback.

    ``api_key`` is retained for source compatibility only. Passing it now fails closed
    because protected Bitcoin Bastion APIs require Proof-of-Access headers.
    """
    if api_key:
        legacy_auth_disabled()
    return dict(headers or {})


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
