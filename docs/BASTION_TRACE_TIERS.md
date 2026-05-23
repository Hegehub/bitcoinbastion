# Bastion Trace Tiers

Tiers are **capability profiles**, not billing enforcement.

## Lite
- User: public/basic operator checks.
- Capabilities: simplified plain-language address check.
- Limits: advisory-only, limited detail, requires production rate limiting before internet exposure.
- Status: BASELINE.

## Pro
- User: analysts/power operators.
- Capabilities: sandbox/watchtower/risk-drift/export/local-mode metadata baselines.
- Limits: scheduling and some advanced flows are placeholders.
- Status: BASELINE.

## Business
- User: merchants/treasury desks/OTC operations.
- Capabilities: batch screening, policy profiles, review desk, notes, proof packet/export baselines.
- Limits: operational recommendations, not legal verdicts or payment execution.
- Status: BASELINE.

## Enterprise
- User: governance-heavy organizations.
- Capabilities: RBAC/SSO placeholders, legal hold metadata, append-only audit baseline, SIEM hooks placeholder, retention/evidence governance.
- Limits: placeholder unless integrated with production auth/IdP/SIEM enforcement.
- Status: BASELINE/PLACEHOLDER.
