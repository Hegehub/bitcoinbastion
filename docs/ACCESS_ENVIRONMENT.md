# Access Environment Variables

The Access Layer relies on environment variables.  This document explains their purpose and safe example values.  Never commit real secrets to the repository.

## Required

| Variable | Example Value | Description |
|---|---|---|
| `ACCESS_SERVER_PEPPER` | `change-me-generate-strong-random-secret` | Secret HMAC pepper used to hash pass lookup values and session tokens.  Must be a long random string and stored in a secret manager. |
| `ACCESS_ISSUER_KEY_ID` | `access-issuer-dev` | Stable, non‑secret identifier for the issuer key used to sign certificates and entitlements. |
| `ACCESS_ISSUER_PRIVATE_KEY` | `dev-only-do-not-use-in-production` | Ed25519 private key PEM used to sign access certificates.  Must never be committed or logged. |
| `ACCESS_SESSION_TTL_SECONDS` | `900` | Lifetime of Proof‑of‑Possession sessions in seconds.  Short‑lived to limit risk. |
| `ACCESS_CHALLENGE_TTL_SECONDS` | `300` | Lifetime of origin‑bound challenges. |
| `ACCESS_REQUEST_MAX_CLOCK_SKEW_SECONDS` | `120` | Maximum acceptable clock skew (± seconds) when verifying `X-Bastion-Timestamp`. |
| `ACCESS_ALLOW_MANUAL_GRANTS` | `false` | Must remain `false` in production.  When `true`, test environments may bypass payments. |
| `ACCESS_BTCPAY_ENABLED` | `false` | Enable the BTCPay provider.  Set other BTCPay variables when `true`. |

## Payment provider (BTCPay)

| Variable | Example | Description |
|---|---|---|
| `ACCESS_BTCPAY_BASE_URL` | `https://btcpay.example.com` | BTCPay Server base URL. |
| `ACCESS_BTCPAY_API_KEY` | `(redacted)` | BTCPay API key. |
| `ACCESS_BTCPAY_STORE_ID` | `(redacted)` | Store identifier for invoices. |
| `ACCESS_BTCPAY_WEBHOOK_SECRET` | `(redacted)` | Secret used to verify BTCPay webhooks. |
| `ACCESS_BTCPAY_DEFAULT_CURRENCY` | `BTC` | Default currency. |
| `ACCESS_BTCPAY_CHECKOUT_EXPIRY_MINUTES` | `30` | Invoice expiry window. |
| `ACCESS_BTCPAY_HTTP_TIMEOUT_SECONDS` | `10` | Provider API timeout. |
| `ACCESS_BTCPAY_WEBHOOK_TOLERANCE_SECONDS` | `300` | Timestamp tolerance for BTCPay webhooks. |

## Recovery

| Variable | Example | Description |
|---|---|---|
| `ACCESS_RECOVERY_COOLDOWN_SECONDS` | `86400` | Minimum seconds between recovery attempts. |
| `ACCESS_LOCKDOWN_REQUIRE_STEP_UP` | `true` | When `true`, high‑impact lockdown scopes require a step‑up human‑intent signature. |
| `ACCESS_RECOVERY_MAX_ATTEMPTS_PER_HOUR` | `5` | Limit recovery attempts to prevent brute force. |
| `ACCESS_RECOVERY_REQUIRE_QUORUM_FOR_PRO` | `true` | Require 2‑of‑3 factors for Pro passes. |
| `ACCESS_RECOVERY_REQUIRE_QUORUM_FOR_BUSINESS` | `true` | Require 2‑of‑3 factors for Business passes. |
| `ACCESS_RECOVERY_REQUIRE_QUORUM_FOR_ENTERPRISE` | `true` | Require 3‑of‑5 factors for Enterprise passes. |
| `ACCESS_RECOVERY_REJECT_BITCOIN_SEED_INPUTS` | `true` | Reject any recovery submission that appears to be a Bitcoin wallet seed. |

## Crypto agility / reserved variables

| Variable | Default | Description |
|---|---|---|
| `ACCESS_CRYPTO_EPOCH` | `1` | Identifies the active crypto epoch.  Increment when rotating issuer keys or adding PQ algorithms. |
| `ACCESS_PQ_ENABLED` | `false` | Post‑quantum signature support.  Reserved; must remain `false` unless audited PQ suites are implemented. |
| `ACCESS_ML_DSA_ENABLED` | `false` | Enable the ML‑DSA signature algorithm when implemented. |
| `ACCESS_ML_KEM_ENABLED` | `false` | Enable the ML‑KEM key‑encapsulation mechanism when implemented. |
| `ACCESS_SLH_DSA_ENABLED` | `false` | Enable the SLH‑DSA signature algorithm when implemented. |

When any PQ variables are enabled, all clients and servers must support the corresponding algorithms.  At present these variables are reserved for future cryptographic agility and **must remain disabled** in production.

## Miscellaneous

| Variable | Example | Description |
|---|---|---|
| `ACCESS_SIGNATURE_ALG` | `ed25519` | Signature algorithm used by the issuer.  Future suites may be added. |
| `ACCESS_DEFAULT_PAYMENT_PROVIDER` | `manual` | Default provider for new payment intents. |
| `ACCESS_PAYMENT_INTENT_TTL_SECONDS` | `900` | Payment intent invoice expiry. |
| `ACCESS_REQUEST_SIGNATURE_REQUIRED` | `true` | Require per‑request signatures on protected endpoints. |

This document does not list unrelated environment variables (e.g. database, storage, analytics).  See `docs/ENVIRONMENT_VARIABLES.md` for a complete list.
