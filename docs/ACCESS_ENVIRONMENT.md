# Access Environment Variables

Use safe placeholders in examples. Real secrets must be injected from a secret manager, Kubernetes secret, Vault, SOPS, SealedSecret, or equivalent.

## Required Access variables

| Variable | Example | Notes |
| --- | --- | --- |
| `ACCESS_SERVER_PEPPER` | `change-me-generate-strong-random-secret` | Secret HMAC pepper; strong and secret in production. |
| `ACCESS_ISSUER_KEY_ID` | `access-issuer-dev` | Non-secret issuer key id. |
| `ACCESS_ISSUER_PRIVATE_KEY` | `dev-only-do-not-use-in-production` | Secret issuer private key; never commit or bake into images. |
| `ACCESS_SESSION_TTL_SECONDS` | `900` | Short-lived PoP session lifetime. |
| `ACCESS_CHALLENGE_TTL_SECONDS` | `300` | Origin-bound challenge lifetime. |
| `ACCESS_REQUEST_MAX_CLOCK_SKEW_SECONDS` | `120` | Preferred clock skew setting for request signing. |
| `ACCESS_REQUEST_MAX_SKEW_SECONDS` | `120` | Compatibility alias used by current settings. |
| `ACCESS_ALLOW_MANUAL_GRANTS` | `false` | Must be false in production unless explicitly approved. |
| `ACCESS_BTCPAY_ENABLED` | `false` | Enable only when BTCPay is configured. |
| `ACCESS_BTCPAY_BASE_URL` | empty | Required when BTCPay is enabled. |
| `ACCESS_BTCPAY_API_KEY` | empty | Secret provider API key. |
| `ACCESS_BTCPAY_STORE_ID` | empty | BTCPay store id. |
| `ACCESS_BTCPAY_WEBHOOK_SECRET` | empty | Required when BTCPay is enabled; never log. |

## Recovery, lockdown, and crypto agility

| Variable | Example | Status |
| --- | --- | --- |
| `ACCESS_RECOVERY_COOLDOWN_SECONDS` | `86400` | Implemented recovery policy setting. |
| `ACCESS_LOCKDOWN_REQUIRE_STEP_UP` | `true` | Lockdown policy requirement. |
| `ACCESS_CRYPTO_EPOCH` | `1` | Implemented crypto epoch label. |
| `ACCESS_PQ_ENABLED` | `false` | Reserved/future; do not enable until real audited PQ support exists. |
| `ACCESS_ML_DSA_ENABLED` | `false` | Reserved/future. |
| `ACCESS_ML_KEM_ENABLED` | `false` | Reserved/future. |
| `ACCESS_SLH_DSA_ENABLED` | `false` | Reserved/future. |

## Production requirements

- `ACCESS_SERVER_PEPPER` must be generated with strong randomness and kept secret.
- `ACCESS_ISSUER_PRIVATE_KEY` must not be committed.
- `ACCESS_ALLOW_MANUAL_GRANTS=false` in production.
- BTCPay webhook secret must be set when BTCPay is enabled.
- PQ flags are reserved for crypto agility only unless implementation and tests exist.
