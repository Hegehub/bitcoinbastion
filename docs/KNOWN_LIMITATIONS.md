# Known Limitations

- Advisory-only analysis
- Heuristic limitations
- Provider disagreement/coverage limitations
- Placeholder enterprise capabilities
- Deployment validation pending
- No production calibration evidence
- No transaction signing
- No custody
- Not legal verification
- Not consensus proof

## Access Layer limitations

- Post-quantum settings are crypto-agility placeholders unless real ML-KEM, ML-DSA, or SLH-DSA implementations and tests are integrated.
- BTCPay is optional and disabled by default until configured with a base URL, store id, API key, and webhook secret.
- Manual grants must be disabled in production unless explicitly approved and audited.
- Recovery seed UX must be handled carefully; Bastion Recovery Seed is not a Bitcoin wallet seed.
- Browser-only critical approval is insufficient for disabling lockdown, recovery changes, treasury policy changes, or enterprise policy changes.
- Offline validity packs and some enterprise private-policy hooks should be considered planned unless exposed by OpenAPI and covered by tests.
