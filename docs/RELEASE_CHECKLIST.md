# Release Checklist

- [ ] tag build
- [ ] container build
- [ ] migration validation
- [ ] frontend build
- [ ] OpenAPI/contract validation
- [ ] deployment validation
- [ ] security review
- [ ] docs review
- [ ] manual signoff
- [ ] rollback readiness
- [ ] production calibration status reviewed
- [ ] known limitations reviewed
- [ ] no fake readiness claims

- [ ] technical debt registry reviewed
- [ ] pre-release gaps acknowledged

## Wallet-first / LNURL mandatory gate

- [ ] `make wallet-lnurl-auth-release-gate` passes.
- [ ] `make wallet-lnurl-auth-production-gate` passes (currently expected to fail).
- [ ] `docs/WALLET_LNURL_AUTH_FINAL_VALIDATION.md` contains no unresolved `BLOCKED` critical item.
- [ ] Stable production LNURL auth domain and migration policy are operator-approved.
- [ ] Real-wallet BIP-322/LNURL compatibility evidence is archived.
- [ ] LNURL auth-attempt and withdraw status contracts are implemented or the dependent clients are disabled.
- [ ] Non-exportable browser/Vault Device signer and deployment secret-manager evidence exist.
- [ ] Production settlement, ingress, migration/rollback, alerting and burn-in evidence is attached.
