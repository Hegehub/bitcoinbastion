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

## 2) Failed background jobs

If `/api/v1/admin/jobs/recovery-check` reports `job_failure` issues:
1. Inspect `/api/v1/admin/jobs/runs` for task names and recent error payloads.
2. Retry safe task classes using `POST /api/v1/admin/jobs/retry`.
3. For repeated failures, disable recurring trigger and investigate provider/database dependencies.
4. Re-run recovery check and confirm failures are clearing.

## 3) Failed deliveries

If recovery check reports `delivery_failure` issues:
1. Verify destination/channel settings.
2. Re-run publish task (`delivery.publish`) once destination and rate-limit conditions are stable.
3. Confirm sent counters improve in `/api/v1/observability/snapshot`.
4. Track delivery failures over the next 24h for regression.

## 4) Rollback procedure

Rollback should be initiated when:
- Health checks fail after deploy and cannot be remediated quickly.
- Recovery check shows rapidly increasing failures.
- Policy/treasury critical endpoints return persistent 5xx.

Rollback steps:
1. Re-deploy previous known-good image.
2. Re-run migration compatibility check (`bash scripts/check_alembic_reproducibility.sh`).
3. Re-run post-deploy verification checklist.
4. Record incident summary and residual risks.

## 5) Governance-sensitive policy changes

For policy catalog changes with strict tightening:
1. Always include `change_justification` in policy catalog upsert payload.
2. Run policy simulation before activation (`POST /api/v1/policy/simulate`).
3. If simulation risk is high, require 2-person review and staged activation.

## 6) Evidence/recommendation traceability checks

For high-impact signals:
1. Inspect `/api/v1/signals/{signal_id}/recommendations` for `evidence_refs`, `evidence_paths`, and `policy_refs`.
2. Ensure actions and rationale are consistent with explainability graph artifacts.
3. Escalate to operator review for inconsistent or low-confidence traces.
