# Burn-in checklist

## First 1 hour / 24h / 7d / 30d
Track: API availability, readiness, degraded mode frequency, provider fallback frequency, provider confidence, delivery failures, recovery findings, Citadel synthetic influence, protocol advisory warnings, DB latency, Redis latency, worker backlog, failed jobs, restart count, memory growth, error rate.

## Pass criteria
- No sustained critical severity.
- Readiness stable and availability within internal SLO baseline.
- Backup/evidence jobs succeed.

## Fail criteria
- Repeated readiness failures, rising unresolved critical findings, persistent degraded mode without mitigation.

## Rollback triggers
- Sev-0 conditions across consecutive review windows.
- Persistent critical path failures after immediate remediation.

## Escalation triggers
- Provider fallback persists beyond policy window.
- Delivery failures exceed configured operational threshold.
