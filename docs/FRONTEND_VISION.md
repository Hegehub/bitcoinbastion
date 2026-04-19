# FRONTEND VISION

## Product framing
Bitcoin Bastion frontend is not a generic crypto dashboard.

It is the control surface for a Bitcoin-native intelligence and sovereignty platform with two product modes:

1. **Bastion Intelligence**
2. **Bastion Citadel**

The frontend must reflect the real backend state that already exists:
- signals
- on-chain events
- entities
- wallet health
- fees
- treasury
- policy
- privacy
- observability
- Citadel assessment, recovery, simulations, inheritance, repair plan

## Primary surfaces

### 1. Intelligence Terminal
Core views:
- signal feed
- on-chain events
- entity intelligence
- news and source reputation
- fee state
- policy-aware recommendations

### 2. Citadel Console
Core views:
- Citadel overview
- assessment breakdown
- dependency graph
- recovery readiness
- disaster simulations
- inheritance readiness
- repair plan
- policy maturity and gaps

### 3. Admin / Operator Surface
Core views:
- health/live/ready checks
- observability snapshot
- job runs
- audit logs
- recovery check
- delivery/runtime visibility

## UX principles
- calm, decision-first interface
- explainability visible at the point of decision
- no casino-style crypto design
- severity, confidence, freshness, and evidence shown consistently
- high-impact actions require operator clarity

## Data contract requirements
The frontend should rely on existing and near-term API contracts:
- `/api/v1/signals/top`
- `/api/v1/signals/{signal_id}/explanation`
- `/api/v1/signals/{signal_id}/recommendations`
- `/api/v1/onchain/events`
- `/api/v1/entities`
- `/api/v1/wallet/health`
- `/api/v1/fees/recommendation`
- `/api/v1/privacy/assess`
- `/api/v1/treasury/requests`
- `/api/v1/policy/*`
- `/api/v1/observability/snapshot`
- `/api/v1/citadel/*`

## Technology direction
Recommended frontend stack:
- Next.js
- TypeScript
- React
- TanStack Query
- componentized, typed API clients
- graph and chart primitives only where they improve decisions

## Current implementation truth
Frontend is not yet the most mature part of the platform.
Backend and API surface lead the product.
Frontend work should follow real backend contracts and avoid inventing data that the backend does not actually produce.

## Immediate frontend priorities
1. Bastion overview dashboard
2. Citadel overview and assessment screens
3. signal explanation panel
4. observability/admin screens
5. treasury review surface