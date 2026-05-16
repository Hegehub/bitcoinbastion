# Operations Runbook

This runbook defines operational response steps for Bitcoin Bastion runtime incidents.

## 1) Post-deploy verification

After each deploy:
1. Check service health: `GET /api/v1/health/live` and `GET /api/v1/health/ready`.
2. Check admin module status: `GET /api/v1/admin/status`.
3. Check recovery posture: `GET /api/v1/admin/jobs/recovery-check`.
4. Check observability snapshot: `GET /api/v1/observability/snapshot`.
5. Verify metrics endpoint: `GET /metrics`.

If any check fails, stop rollout and proceed to rollback section.

## 2) Runtime governance interpretation

When reading `/api/v1/observability/snapshot`:
- `runtime_severity.level`: aggregate runtime posture (`ok|warning|critical`).
- `runtime_severity.escalation_required`: escalation gate for operator paging.
- `degraded_mode.active`: explicit degraded runtime mode flag.
- `degraded_mode.reasons`: degraded dependencies (e.g. stale chain/mempool, provider outage, delivery degradation).
- `operational_evidence`: compact audit packet for triage (runtime state, provider quality, unresolved findings, delivery/drill/recovery posture).

Governance rule: if `degraded_mode.active=true`, treat confidence-bearing outputs as reduced-confidence until recovery actions complete.

## 3) Failed background jobs

If `/api/v1/admin/jobs/recovery-check` reports `job_failure` issues:
1. Inspect `/api/v1/admin/jobs/runs` for task names and recent error payloads.
2. Retry safe task classes using `POST /api/v1/admin/jobs/retry`.
3. For repeated failures, disable recurring trigger and investigate provider/database dependencies.
4. Re-run recovery check and confirm failures are clearing.

## 4) Failed deliveries

If recovery check reports `delivery_failure` issues:
1. Verify destination/channel settings.
2. Re-run publish task (`delivery.publish`) once destination and rate-limit conditions are stable.
3. Confirm sent counters improve in `/api/v1/observability/snapshot`.
4. Track delivery failures over the next 24h for regression.

## 5) Degraded/fallback response workflow

Escalate promptly when one or more apply:
- `runtime_severity.level == "critical"`
- `runtime_severity.escalation_required == true`
- `degraded_mode.reasons` includes provider or observability outage markers
- `operational_evidence.unresolved_critical_findings > 0`

Actions:
1. Freeze high-impact policy automation and treasury-sensitive actions.
2. Recover provider freshness (probe/failover) and confirm fallback clears.
3. Run/queue highest-priority drill from `operational_evidence.drill_status`.
4. Reassess recovery SLO status and unresolved findings.
5. Document incident timeline and residual risk before resuming automation.

## 6) Rollback procedure

Rollback should be initiated when:
- Health checks fail after deploy and cannot be remediated quickly.
- Recovery check shows rapidly increasing failures.
- Policy/treasury critical endpoints return persistent 5xx.

Rollback steps:
1. Re-deploy previous known-good image.
2. Re-run migration compatibility check (`bash scripts/check_alembic_reproducibility.sh`).
3. Re-run post-deploy verification checklist.
4. Record incident summary and residual risks.

## 7) Governance-sensitive policy changes

For policy catalog changes with strict tightening:
1. Always include `change_justification` in policy catalog upsert payload.
2. Run policy simulation before activation (`POST /api/v1/policy/simulate`).
3. If simulation risk is high, require 2-person review and staged activation.

## 8) Evidence/recommendation traceability checks

For high-impact signals:
1. Inspect `/api/v1/signals/{signal_id}/recommendations` for `evidence_refs`, `evidence_paths`, and `policy_refs`.
2. Ensure actions and rationale are consistent with explainability graph artifacts.
3. Escalate to operator review for inconsistent or low-confidence traces.
