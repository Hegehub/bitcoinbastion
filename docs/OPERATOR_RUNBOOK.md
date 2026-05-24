# Operator Runbook

## Startup
- verify env vars and secrets injection
- run API/worker/frontend and health checks

## Operations
- review logs and runtime events
- verify docs/readiness gates
- run release-readiness checks

## Troubleshooting
- inspect failing checks
- rollback to previous known-good release if needed

## Safety invariants
- No custody
- No transaction signing
- No seed/private key handling
