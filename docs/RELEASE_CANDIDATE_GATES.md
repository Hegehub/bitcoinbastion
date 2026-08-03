# Release Candidate Gates

Gate statuses:
- PASS
- FAIL
- PENDING
- NOT_EXECUTED

Gate categories:
- Code Quality
- Backend Tests
- Frontend Tests
- Security Baseline
- API Contract Stability
- Docs Truthfulness
- Deployment Validation
- Observability Validation
- Operational Validation
- Manual Review

## Wallet/LNURL Proof-of-Access gate

| Gate | Status | Command / evidence |
|---|---|---|
| Wallet/LNURL release-candidate security gate | PASS | `make wallet-lnurl-auth-release-gate`; see `docs/WALLET_LNURL_AUTH_FINAL_VALIDATION.md`. |
| Wallet/LNURL production promotion gate | FAIL | `make wallet-lnurl-auth-production-gate` intentionally fails while documented production blockers remain. |

A candidate test pass is not production approval. Promotion requires the final validation decision to change based on deployment, interoperability, auth-domain, status-contract, signer-bridge, settlement-provider and operational evidence.
