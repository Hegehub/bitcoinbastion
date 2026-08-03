# Release Notes

## Release Candidate Baseline
This release is a **baseline RC transition pack** and is **not production-complete**.

Included:
- frontend foundation and Trace UX baselines
- operations dashboard baseline
- security middleware baseline
- k8s/gitops/deployment baseline scaffolding
- release governance and calibration docs

Pending:
- production calibration evidence
- load/perf testing
- penetration testing
- production deployment evidence


## Proof-of-Access Auth Migration Gate

This release line includes the final Bastion Proof-of-Access Auth migration gate. It does **not** claim production deployment completion; it adds local/CI checks that prevent regressions toward legacy email, username, password, JWT, bearer-token, or bearer Access Pass authentication.

Gate coverage includes:

- legacy password login/register disabled and returning deterministic legacy-disabled responses;
- raw Access Pass and `Authorization: Bearer` rejected for protected APIs;
- protected APIs requiring Access dependency and Policy Engine paths;
- payment-proof, certificate, challenge, session, replay-protection, revocation, recovery-safety, and redaction regression tests;
- Python and TypeScript SDK checks for `X-Bastion-*` Proof-of-Access headers and fail-closed legacy bearer compatibility fields;
- frontend/reflex checks that the Access flow is present and active password forms are absent;
- OpenAPI checks that active password login and bearer-token issuance are not advertised as production auth.

Run locally with `make access-release-gate`. Remaining non-Access contract tests that still depend on legacy `get_admin_user` overrides must be migrated before claiming full repository-wide green status.

## Wallet/LNURL Auth PQ v2 validation status

Wallet-first, LNURL adapter, Device-bound PoP, entitlement, policy, recovery, revocation, audit, certificate/offline and crypto-agile interfaces are implemented as a release candidate. The repository is **NOT PRODUCTION-READY**: see `docs/WALLET_LNURL_AUTH_FINAL_VALIDATION.md`. “PQ-ready” means versioned crypto-agility interfaces; it does not mean ML-DSA, SLH-DSA or ML-KEM are fully enabled.
