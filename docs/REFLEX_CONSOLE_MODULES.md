# Reflex Console Modules

## Core modules

- Dashboard: `/console`
- Trace: `/console/trace`
- Evidence: `/console/evidence`
- Provider Health: `/console/provider-health`
- Policy: `/console/policy`
- Audit: `/console/audit`

## Advanced modules

- Market Intelligence: `/console/market-intelligence`
- Market Time Machine: `/console/time-machine`
- Sovereign Grid: `/console/sovereign-grid`
- API Explorer: `/console/api-explorer`

## Module status

All advanced modules are frontend console surfaces. They provide operator context, safe placeholders, degraded visibility, endpoint mappings, and safety copy. They are not production cutover modules and do not replace FastAPI/Jinja Market surfaces.

## Safety posture

- No custody.
- No transaction signing.
- No treasury approval.
- No exchange execution.
- No seed phrase, mnemonic, private key, wallet file, keystore, or signing-material collection.
- No financial advice.
- No legal-verdict UI.
- No Bitcoin-consensus-proof UI.

## API Explorer safety classifications

- Safe read
- Advisory analysis
- Draft-only
- Requires approval
- Admin-only
- Unavailable
- Experimental

Only safe read examples are marked as tryable from the Reflex API Explorer.
