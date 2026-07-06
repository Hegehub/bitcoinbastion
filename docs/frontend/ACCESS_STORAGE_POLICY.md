# Frontend Access Storage Policy

Proof-of-Access frontend state is intentionally short-lived and secret-minimizing.

## Never store

- Raw Bastion Access Pass in `localStorage`.
- Bastion Recovery Seed or recovery phrase in `localStorage`, session storage, logs, analytics, or URLs.
- Device private key material unencrypted in the browser.
- Raw challenge signatures, BTCPay API keys, webhook secrets, issuer private keys, or server pepper.

## Allowed frontend state

- Short-lived Proof-of-Possession session metadata may be kept in memory or secure session storage depending on deployment policy.
- Safe display metadata may include plan code, scope names, quota usage, locked metric groups, session expiry, and a short device fingerprint.
- Raw passes are displayed only once after settled payment and certificate issuance.

## Development signer policy

`BB_ACCESS_DEV_SIGNER_ENABLED` / `ACCESS_DEV_SIGNER_ENABLED` must remain `false` in production. If a local development signer is enabled in a non-production environment, the UI must show “Development signer — not for production” and it must never claim Vault production custody.

## User warnings

Frontend Access screens repeat:

- “This is not a password.”
- “This is not your Bitcoin wallet seed.”
- “Bastion will never ask for your Bitcoin wallet seed or private key.”
