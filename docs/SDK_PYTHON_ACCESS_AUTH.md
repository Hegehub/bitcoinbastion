# Python SDK Proof-of-Access Authentication

Bitcoin Bastion Python SDK uses Bastion Proof-of-Access for protected APIs. Legacy `Authorization: Bearer` and `api_key` authentication are disabled by default and are not the primary authentication model.

## Flow

1. Import a Bastion Access Pass or `.bbp` certificate metadata file.
2. Create an origin-bound challenge with `client.access.create_challenge(...)`.
3. Sign the challenge with a Bastion device signer.
4. Create a short-lived Proof-of-Possession session with `client.access.create_session(...)`.
5. Use `BastionAccessAuth` to sign protected requests with `X-Bastion-*` headers.

This is not Bitcoin wallet signing. Bastion will never ask for a Bitcoin seed or private key.

## Headers

Protected requests include:

- `X-Bastion-Session`
- `X-Bastion-Timestamp`
- `X-Bastion-Nonce`
- `X-Bastion-Body-Hash`
- `X-Bastion-Signature`

The SDK signs `SHA256(method || path || body_hash || timestamp || nonce)` with the configured Bastion device signer.

## Example

```python
from datetime import UTC, datetime, timedelta

from bitcoin_bastion_sdk import BastionClient
from bitcoin_bastion_sdk.access_auth import AccessSession, BastionAccessAuth, import_access_pass
from bitcoin_bastion_sdk.signing import InMemoryDeviceSigner

material = import_access_pass(path="~/.bastion/bastion-pass.bbp")
signer = InMemoryDeviceSigner(b"replace-with-vault-backed-bastion-device-secret")

client = BastionClient(base_url="https://api.example.com")
challenge = client.access.create_challenge({
    "access_pass": material.raw_access_pass,
    "certificate_fingerprint": material.certificate_fingerprint,
    "origin": "https://app.example.com",
    "requested_scopes": ["market:intelligence:read"],
    "device_key_fingerprint": signer.public_key_fingerprint(),
})

# In production, sign the backend challenge payload and create the session.
session = AccessSession(
    session_token="session-token-from-/access/sessions",
    expires_at=datetime.now(UTC) + timedelta(minutes=15),
    scopes=["market:intelligence:read"],
    plan_code="pro_pass",
)

auth = BastionAccessAuth.from_session(session, signer=signer, origin="https://app.example.com")
protected_client = BastionClient(base_url="https://api.example.com", access_auth=auth)
me = protected_client.access.me()
```

## Secret handling

The SDK redacts Access Passes, session tokens, request signatures, private-key-looking values, recovery phrases, `Authorization`, and `X-Bastion-*` sensitive headers from repr/debug helpers. Raw Access Pass material should be used only to start challenge/session flow and should be kept in an external vault or user-controlled file.
