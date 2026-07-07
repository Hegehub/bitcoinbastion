# TypeScript SDK Proof-of-Access Auth Migration

## Current auth model audit

The previous TypeScript SDK accepted a static `apiKey` value in `sdk/typescript/src/config.ts` and injected it through `sdk/typescript/src/auth.ts` / `sdk/typescript/src/http.ts`. Earlier migration stubs already failed closed by default, but auth was still modeled as static client-wide headers and examples could imply session headers were manually supplied.

## Files changed

- `sdk/typescript/src/auth.ts`: adds Proof-of-Access types, `BastionAccessAuth`, access pass import/session helpers, signing, safe state export, and fail-closed legacy bearer guard.
- `sdk/typescript/src/http.ts`: signs protected requests with `X-Bastion-*` headers and throws locally when protected calls lack Access auth.
- `sdk/typescript/src/config.ts`: adds `accessAuth`, `allowLegacyBearerAuth`, and `redactSensitiveLogs` config.
- `sdk/typescript/src/resources/access.ts`: adds challenge/session and `/access/me` resource helpers.
- `sdk/typescript/src/resources/treasury.ts`, `policy.ts`, and `wallet.ts`: mark protected calls as requiring signed Access auth.
- `sdk/typescript/src/utils/crypto.ts` and `sdk/typescript/src/utils/redaction.ts`: add canonical hashing/signing helpers and recursive redaction.
- `sdk/typescript/examples/*`: use Proof-of-Access examples and warn not to provide Bitcoin seed/private keys.

## Deprecated behavior

`Authorization: Bearer` and `apiKey` are not used by default. `allowLegacyBearerAuth` is retained only as a rejected compatibility argument; it still fails closed and is not valid for Access Layer endpoints.

## New Proof-of-Access flow

1. Import a Bastion Access Pass only to create a challenge/session.
2. Create an origin-bound challenge via `client.access.createChallenge(...)`.
3. Sign the challenge with a Bastion `AccessSigner`.
4. Create a short-lived Proof-of-Possession session.
5. Configure `BitcoinBastionClient({ accessAuth })` so protected requests are signed.

## Request headers

Protected requests include:

- `X-Bastion-Session`
- `X-Bastion-Timestamp`
- `X-Bastion-Nonce`
- `X-Bastion-Body-Hash`
- `X-Bastion-Signature`
- `X-Bastion-Auth-Version: proof-of-access-v1`

The request digest is `SHA256(method || path || body_hash || timestamp || nonce)` encoded with newline delimiters to avoid ambiguity.

## Protected vs public resources

Public resources such as health/status and trace-lite can be called without Access auth. Protected resources such as treasury, policy evaluation, wallet health, and `/access/me` require an active Access session and device signer.

## Security rules

Never send raw Access Passes on every request. Never log raw Access Passes, session tokens, signatures, private key material, recovery phrases, Bitcoin seed phrases, or wallet private keys. Bastion will never ask for your Bitcoin seed or private key.

## Test coverage added

- Request signing headers, nonce uniqueness, timestamp presence, method/path digest binding, body hash stability.
- Redaction of access pass, session token, signatures, nested objects, and authorization headers.
- Legacy bearer disabled even when compatibility flags are supplied.
- Protected resource failure without Access auth and signed headers with Access auth.
- Safety rejection for Bitcoin seed/private-key-looking input.

## Validation notes

Run from `sdk/typescript`:

```bash
npm test
npm run typecheck
npm run lint
```

Repository-level checks:

```bash
pytest tests/contract/test_access_openapi_contract.py
pytest tests/security/test_no_bearer_access_pass.py
```
